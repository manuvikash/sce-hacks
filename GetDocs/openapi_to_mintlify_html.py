#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Tuple

from playwright.sync_api import sync_playwright

INDEX_MDX = """---
title: Home
---

# API docs

This site was generated locally with Mintlify and your OpenAPI spec.
Open the **API reference** section in the sidebar to view endpoint pages.
"""

def wait_for_server(port: int, timeout_s: int = 60) -> bool:
    """Return True when HTTP responds (<500), False on timeout."""
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            conn.request("GET", "/")
            resp = conn.getresponse()
            if resp.status < 500:
                _ = resp.read(64)
                return True
        except Exception:
            pass
        time.sleep(2)
    return False

def launch_mint_dev(project_dir: Path, port: int) -> subprocess.Popen:
    cli = shutil.which("mintlify")
    if cli:
        cmd = [cli, "dev", "--port", str(port)]
    else:
        cmd = ["npx", "mintlify", "dev", "--port", str(port)]

    proc = subprocess.Popen(
        cmd,
        cwd=str(project_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Stream CLI logs so errors surface immediately
    def _drain(p):
        if not p.stdout:
            return
        for line in iter(p.stdout.readline, ''):
            print("[mintlify]", line, end='')

    threading.Thread(target=_drain, args=(proc,), daemon=True).start()
    return proc

def capture_mhtml_and_pdf(base_url: str, first_slug: str, out_mhtml: Path, out_pdf: Path | None, settle_ms: int = 1200):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Load home first
        page.goto(base_url, wait_until="domcontentloaded")

        # Go to first endpoint page to ensure API UI hydrated
        preferred_targets = [
            f"/api-reference/{first_slug}",  # our first page
            "/api-reference",                # group landing
            "/"                              # fallback
        ]
        for t in preferred_targets:
            try:
                page.goto(base_url.rstrip("/") + t, wait_until="domcontentloaded")
                break
            except Exception:
                continue

        # Give client JS/hydration a moment
        page.wait_for_timeout(settle_ms)

        # Snapshot to single-file MHTML
        cdp = context.new_cdp_session(page)
        mhtml = cdp.send("Page.captureSnapshot", {"format": "mhtml"})["data"]
        out_mhtml.write_text(mhtml, encoding="utf-8")

        # Optional PDF
        if out_pdf:
            page.pdf(path=str(out_pdf), format="Letter", print_background=True)

        browser.close()

def load_openapi(spec_path: Path) -> Dict[str, Any]:
    ext = spec_path.suffix.lower()
    text = spec_path.read_text(encoding="utf-8")
    if ext in [".json"]:
        return json.loads(text)
    elif ext in [".yaml", ".yml"]:
        try:
            import yaml  # type: ignore
        except Exception:
            print("YAML spec detected. Please `pip install pyyaml` and retry.", file=sys.stderr)
            sys.exit(1)
        return yaml.safe_load(text)
    else:
        # Try JSON first, then YAML
        try:
            return json.loads(text)
        except Exception:
            try:
                import yaml  # type: ignore
            except Exception:
                print("Unknown spec format. Install pyyaml or provide JSON.", file=sys.stderr)
                sys.exit(1)
            return yaml.safe_load(text)

METHODS = {"get","post","put","delete","patch","options","head","trace"}

def slugify(method: str, path: str) -> str:
    # e.g., GET /api/guides/{city} -> get-api-guides-city
    clean = path.strip("/")
    clean = re.sub(r"[{}]", "", clean)  # remove braces
    clean = clean.replace("/", "-") or "root"
    return f"{method.lower()}-{clean}"

def list_operations(spec: Dict[str, Any]) -> List[Tuple[str, str]]:
    ops: List[Tuple[str, str]] = []
    paths = spec.get("paths", {})
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() in METHODS and isinstance(op, dict):
                ops.append((method.upper(), path))
    return ops

def write_project_from_spec(project_dir: Path, spec_path: Path, spec_basename: str, ops: List[Tuple[str, str]]) -> str:
    # index
    (project_dir / "index.mdx").write_text(INDEX_MDX, encoding="utf-8")

    # Create API pages
    api_dir = project_dir / "api-reference"
    api_dir.mkdir(exist_ok=True)

    pages = []
    first_slug = None
    for method, path in ops:
        slug = slugify(method, path)
        if first_slug is None:
            first_slug = slug
        mdx = f"""---
title: {method} {path}
openapi: "./{spec_basename} {method} {path}"
---

"""
        (api_dir / f"{slug}.mdx").write_text(mdx, encoding="utf-8")
        pages.append(f"api-reference/{slug}")

    # docs.json
    docs = {
        "$schema": "https://mintlify.com/docs.json",
        "theme": "mint",
        "name": "API Docs",
        "colors": { "primary": "#0ea5e9" },
        "navigation": {
            "groups": [
                {
                    "group": "API reference",
                    "pages": pages if pages else ["api-reference"]  # shouldn't be empty
                }
            ]
        },
        "interaction": { "drilldown": True }
    }
    (project_dir / "docs.json").write_text(json.dumps(docs, indent=2), encoding="utf-8")

    return first_slug or "index"

def main():
    parser = argparse.ArgumentParser(
        description="Render an OpenAPI spec with Mintlify locally and export as single-file MHTML (and optional PDF)."
    )
    parser.add_argument("spec", help="Path to OpenAPI file (.yaml or .json)")
    parser.add_argument("--out", default="api-docs.mhtml", help="Output MHTML file path (default: api-docs.mhtml)")
    parser.add_argument("--pdf", default=None, help="Optional PDF file path")
    parser.add_argument("--port", type=int, default=3333, help="Port to run mintlify dev on (default: 3333)")
    parser.add_argument("--timeout", type=int, default=300, help="Seconds to wait for server to become reachable (default: 300)")
    parser.add_argument("--startup-grace", type=int, default=12, help="Extra seconds to wait after server is reachable before capture (default: 12)")
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temp Mintlify project folder for debugging")
    parser.add_argument("--keep-server", action="store_true", help="Keep the Mintlify dev server running after capture (blocks until Ctrl+C)")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    print(spec_path)
    if not spec_path.exists():
        print(f"OpenAPI file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    # Parse to enumerate operations (also acts as a quick sanity check)
    try:
        spec = load_openapi(spec_path)
    except Exception as e:
        print(f"Failed to parse OpenAPI file: {e}", file=sys.stderr)
        sys.exit(1)

    ops = list_operations(spec)
    if not ops:
        print("No operations found in the OpenAPI spec under `paths`.", file=sys.stderr)
        sys.exit(1)

    temp_dir = Path(tempfile.mkdtemp(prefix="mintlify_api_"))
    print(f"[info] Working dir: {temp_dir}")
    try:
        # Copy the user's spec into project root as openapi.<ext>
        ext = spec_path.suffix.lower()
        if ext not in [".yaml", ".yml", ".json"]:
            print("Warning: unrecognized spec extension; proceeding anyway.", file=sys.stderr)
        openapi_name = f"openapi{ext if ext else '.yaml'}"
        shutil.copyfile(spec_path, temp_dir / openapi_name)

        print("[info] Project tree (pre-gen):")
        for p in sorted(temp_dir.rglob("*")):
            rel = p.relative_to(temp_dir)
            print(" -", rel)

        first_slug = write_project_from_spec(temp_dir, spec_path, openapi_name, ops)

        print("[info] Project tree (post-gen):")
        for p in sorted(temp_dir.rglob("*")):
            rel = p.relative_to(temp_dir)
            print(" -", rel)

        # Launch mintlify dev
        proc = launch_mint_dev(temp_dir, args.port)

        # Wait for server to answer HTTP
        if not wait_for_server(args.port, timeout_s=args.timeout):
            try:
                out = proc.stdout.read() if proc.stdout else ""
            except Exception:
                out = ""
            try:
                proc.terminate()
            except Exception:
                pass
            print("Failed to start Mintlify dev server.\nOutput:\n" + str(out), file=sys.stderr)
            sys.exit(2)

        # Give it extra time to finish bundling/hydration
        if args.startup_grace > 0:
            time.sleep(args.startup_grace)

        # Capture
        base_url = f"http://127.0.0.1:{args.port}"
        out_mhtml = Path(args.out).resolve()
        out_pdf = Path(args.pdf).resolve() if args.pdf else None
        capture_mhtml_and_pdf(base_url, first_slug, out_mhtml, out_pdf, settle_ms=1500)

        print(f"Done.\nMHTML: {out_mhtml}")
        if out_pdf:
            print(f"PDF:   {out_pdf}")
        print(f"Preview locally: {base_url}")

        if args.keep_server:
            print("[info] --keep-server is on; leaving dev server running.")
            print(f"[info] Project dir: {temp_dir}")
            print("[info] Press Ctrl+C to stop.")
            try:
                proc.wait()
            except KeyboardInterrupt:
                pass

    finally:
        try:
            if 'proc' in locals() and proc and proc.poll() is None and not args.keep_server:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            pass

        if not args.keep_temp and not args.keep_server:
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            print(f"Kept temp project at: {temp_dir}")

if __name__ == "__main__":
    main()
