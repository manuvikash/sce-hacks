from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GenerateOptions(BaseModel):
    max_search_rounds: int = 3
    max_files: int = 200
    max_routes: int = 300
    context_lines: int = 20
    enrich_top_n: Optional[int] = None
    max_bytes_per_file: int = 200_000
    exts: Optional[List[str]] = [
        ".js", ".jsx", ".ts", ".tsx",
        ".py", ".go", ".java", ".rb",
        ".php", ".cs", ".kt", ".scala",
        ".rs", ".c", ".cpp", ".mjs",
        ".md", ".yml", ".yaml", ".json"
    ]

class GenerateRequest(BaseModel):
    repo_url: str
    options: GenerateOptions = Field(default_factory=GenerateOptions)

class FileIndex(BaseModel):
    path: str
    ext: str
    size: int
    head: str
    tail: str

class GenerateResponse(BaseModel):
    status: str
    spec_path: str
    routes_found: int
    rounds_used: int
    skipped: Dict[str, int]
    notes: List[str]
    report: Dict[str, Any]

class SearchQuery(BaseModel):
    regex: str
    glob: str = "**/*"
    why: str

class SearchPlan(BaseModel):
    frameworks: List[str]
    searches: List[SearchQuery]

class Match(BaseModel):
    file: str
    line: int
    match: str
    before: List[str]
    after: List[str]

class DiscoveredRoute(BaseModel):
    method: str           # "get" | "post" | ...
    raw_path: str         # e.g. "/users/:id"
    file: str
    line: int
    evidence: List[str]   # exact lines that prove it

class Enrichment(BaseModel):
    summary: Optional[str] = None
    auth: Optional[str] = None                      # "required" | "none" | "maybe"
    requestBody: Optional[Dict[str, Any]] = None    # JSON Schema or None
    responses: Optional[Dict[str, Any]] = None      # map like {"200": {...}, "400": {...}}

class RouteDef(BaseModel):
    method: str
    path: str
    parameters: List[Dict[str, Any]] = []
    requestBody: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = {}
    evidence: Dict[str, Any] = {}                   # { file, line, quotes: [...] }
    summary: Optional[str] = None
    auth: Optional[str] = None

class Snippet(BaseModel):
    file: str
    start: int
    end: int
    text: str   # the actual chunk of code we read

