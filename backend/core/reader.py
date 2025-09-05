import os
from typing import List
from .types import Snippet

def _safe_read_lines(abs_path: str) -> List[str]:
    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()

def read_snippet(repo_dir: str, file: str, center_line: int, radius: int = 60) -> Snippet:
    # file may be absolute from /tmp; keep as-is if absolute, else join repo_dir
    abs_path = file if os.path.isabs(file) else os.path.join(repo_dir, file)
    lines = _safe_read_lines(abs_path)
    start = max(1, center_line - radius)
    end = min(len(lines), center_line + radius)
    text = "".join(lines[start-1:end])
    return Snippet(file=file, start=start, end=end, text=text)

def read_file_section(repo_dir: str, file: str, start: int, end: int) -> Snippet:
    abs_path = file if os.path.isabs(file) else os.path.join(repo_dir, file)
    lines = _safe_read_lines(abs_path)
    start = max(1, start)
    end = min(len(lines), end)
    text = "".join(lines[start-1:end])
    return Snippet(file=file, start=start, end=end, text=text)
