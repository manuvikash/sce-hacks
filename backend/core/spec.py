import json, os
from typing import Dict, Any
from openapi_spec_validator import validate_spec

def build_openapi_skeleton(title: str, version: str = "0.1.0", servers=None) -> Dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {"title": title, "version": version},
        "servers": [{"url": s} for s in (servers or ["http://localhost"])],
        "paths": {}
    }

def _ensure_path(spec: Dict[str, Any], path: str):
    spec["paths"].setdefault(path, {})

def _default_response():
    return {"description": "OK", "content": {"application/json": {"schema": {"type": "object", "additionalProperties": True}}}}

def merge_route(spec: Dict[str, Any], route: Dict[str, Any]) -> None:
    path = route["path"]
    method = route["method"].lower()
    _ensure_path(spec, path)
    entry = {
        "summary": route.get("summary") or f"{method.upper()} {path}",
        "parameters": route.get("parameters") or [],
        "responses": route.get("responses") or {"200": _default_response()},
    }
    if route.get("requestBody") is not None:
        entry["requestBody"] = {
            "required": False,
            "content": {"application/json": {"schema": route["requestBody"]}}
        }
    spec["paths"][path][method] = entry

def _downgrade_schemas(spec: Dict[str, Any]) -> None:
    # Replace any problematic schemas with permissive objects
    for p, methods in spec.get("paths", {}).items():
        for m, op in methods.items():
            if "requestBody" in op:
                op["requestBody"]["content"]["application/json"]["schema"] = {"type": "object", "additionalProperties": True}
            for code, resp in (op.get("responses") or {}).items():
                if "content" in resp and "application/json" in resp["content"]:
                    resp["content"]["application/json"]["schema"] = {"type": "object", "additionalProperties": True}

def validate_openapi(spec: Dict[str, Any]) -> tuple[bool, list[str]]:
    try:
        validate_spec(spec)   # throws if invalid
        return True, []
    except Exception as e:
        return False, [str(e)]

def export_spec(spec: Dict[str, Any], out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)
    return out_path
