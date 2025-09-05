import os
from typing import List, Optional
from .types import FileIndex

IGNORE_DIRS = {
    ".git", ".hg", ".svn",
    "node_modules", "dist", "build", ".next", ".nuxt",
    ".venv", "venv", "__pycache__",
    "target", "out"
}

TEXT_LIKE = {
    ".js",".jsx",".ts",".tsx",".py",".go",".java",".rb",".php",".cs",".kt",
    ".scala",".rs",".c",".cpp",".mjs",".json",".yml",".yaml",".md",".txt"
}

def _should_skip_dir(name: str) -> bool:
    return name in IGNORE_DIRS or name.startswith(".")

def _is_text_ext(ext: str, allowed_exts: Optional[List[str]]) -> bool:
    if allowed_exts is not None:
        return ext in allowed_exts
    return ext in TEXT_LIKE

def _read_head_tail(path: str, max_bytes: int) -> tuple[str, str]:
    # Read first and last chunks without loading entire huge files.
    try:
        with open(path, "rb") as f:
            head_bytes = f.read(min(max_bytes, 8192))
            # tail: seek from end if file is large
            try:
                f.seek(-min(max_bytes, 8192), os.SEEK_END)
                tail_bytes = f.read(min(max_bytes, 8192))
            except OSError:
                # File smaller than chunk; re-open from start and read all
                f.seek(0)
                tail_bytes = f.read()
    except Exception:
        return "", ""
    head = head_bytes.decode("utf-8", errors="ignore")
    tail = tail_bytes.decode("utf-8", errors="ignore")
    return head, tail

def build_inventory(
    repo_dir: str,
    exts: Optional[List[str]] = None,
    max_files: int = 200,
    max_bytes: int = 200_000
) -> List[FileIndex]:
    results: List[FileIndex] = []
    count = 0
    for root, dirs, files in os.walk(repo_dir):
        # prune ignored dirs
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
        for name in files:
            if count >= max_files:
                return results
            full = os.path.join(root, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            ext = os.path.splitext(name)[1].lower()
            if not _is_text_ext(ext, exts):
                continue
            head, tail = _read_head_tail(full, max_bytes=max_bytes)
            rel = os.path.relpath(full, repo_dir)
            results.append(FileIndex(path=rel, ext=ext, size=size, head=head, tail=tail))
            count += 1
    return results
