import re
from typing import List, Dict, Any

_PARAM_RE = re.compile(r"{([^}]+)}")

def normalize_path(raw: str) -> str:
    # Express ':id' -> '{id}'; Flask '<int:id>' or '<id>' -> '{id}'
    p = raw.strip()
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r":([A-Za-z0-9_]+)", r"{\1}", p)
    p = re.sub(r"<[^:>]*:([^>]+)>", r"{\1}", p)
    p = re.sub(r"<([^>]+)>", r"{\1}", p)
    # collapse double slashes
    p = re.sub(r"//+", "/", p)
    return p

def extract_path_params(path: str) -> List[Dict[str, Any]]:
    names = _PARAM_RE.findall(path)
    return [
        {"name": n, "in": "path", "required": True, "schema": {"type": "string"}}
        for n in names
    ]
