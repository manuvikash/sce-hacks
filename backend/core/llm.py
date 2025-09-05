import os
import json
import re
from typing import Optional, Dict, Any, List

import google.generativeai as genai

from .types import (
    FileIndex,
    SearchPlan,
    SearchQuery,
    Match,
    DiscoveredRoute,
    Snippet,
    Enrichment,
)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _ensure_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)


def gemini_json(
    system: Optional[str],
    user: str,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    _ensure_client()
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        generation_config={
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
        system_instruction=system or "",
    )
    resp = model.generate_content(user)
    text = resp.text or "{}"

    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def plan_search(inventory: List[FileIndex]) -> SearchPlan:
    system = """You are an API discovery planner.
Given a repo inventory (file paths + first/last lines),
infer likely web frameworks and propose regex searches to find HTTP endpoints.
Output JSON only, shaped as:
{
  "frameworks": [...],
  "searches": [
    {"regex": "...", "glob": "**/*.{js,ts}", "why": "..."}
  ]
}"""

    compact = []
    for f in inventory[:50]:
        compact.append(
            {
                "path": f.path,
                "ext": f.ext,
                "head": f.head[:200],
                "tail": f.tail[-200:],
            }
        )

    user = json.dumps(compact, indent=2)
    raw = gemini_json(system=system, user=user)

    searches = [SearchQuery(**s) for s in raw.get("searches", [])]
    return SearchPlan(frameworks=raw.get("frameworks", []), searches=searches)


def extract_routes(matches_map: Dict[int, List[Match]]) -> List[DiscoveredRoute]:
    system = """You extract HTTP endpoints from grep-like matches.
Each match has a file, line, the matched line, and nearby lines.
Emit ONLY endpoints directly supported by the quoted lines (no guessing).
Return JSON array of:
{ "method": "get|post|put|patch|delete|options|head|all",
  "raw_path": "/users/:id",
  "file": "relative/path.js",
  "line": 123,
  "evidence": ["<exact lines>"] }"""

    compact = {
        str(k): [
            {
                "file": m.file,
                "line": m.line,
                "match": m.match,
                "before": m.before[-5:],
                "after": m.after[:5],
            }
            for m in v[:50]
        ]
        for k, v in matches_map.items()
    }

    user = json.dumps(compact, indent=2)
    raw = gemini_json(system=system, user=user)

    out: List[DiscoveredRoute] = []
    if isinstance(raw, list):
        for item in raw:
            try:
                out.append(DiscoveredRoute(**item))
            except Exception:
                pass
    return out


def enrich_route(snippet: Snippet, method: str, raw_path: str) -> Enrichment:
    system = (
        "You produce ONLY JSON with hints for OpenAPI. "
        "Infer strictly from the code snippet; if unknown use nulls. "
        "Keys: summary (string), auth ('required'|'none'|'maybe'), "
        "requestBody (JSON Schema or null), responses (map like "
        "{'200': {'description': 'OK', 'schema': {...}}})."
    )

    # 👇 this is a multi-line string we feed to Gemini
    user = f"""METHOD: {method.upper()}
RAW_PATH: {raw_path}
CODE_SNIPPET:
"""
    data = gemini_json(system=system, user=user, temperature=0.1)
    try:
        return Enrichment(**data)
    except Exception:
        return Enrichment(summary=None, auth=None, requestBody=None, responses=None)


