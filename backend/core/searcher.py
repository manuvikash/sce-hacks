import os, re, glob
from typing import List
from .types import SearchQuery, Match

FALLBACK_QUERIES: list[SearchQuery] = [
    # JS/TS Express/Nest-ish
    SearchQuery(regex=r"\b(app|router)\.(get|post|put|patch|delete|options|head|all)\s*\(", glob="**/*.{js,ts,jsx,tsx}", why="Generic JS HTTP methods"),
    SearchQuery(regex=r"express\.Router\(", glob="**/*.{js,ts,jsx,tsx}", why="Express routers"),
    SearchQuery(regex=r"@Controller|@Get\(|@Post\(|@Put\(|@Delete\(", glob="**/*.{ts,tsx}", why="NestJS annotations"),
    # Python Flask/FastAPI/Django
    SearchQuery(regex=r"@\w+\.route\(", glob="**/*.py", why="Flask route decorator"),
    SearchQuery(regex=r"@app\.(get|post|put|patch|delete)\(", glob="**/*.py", why="FastAPI decorators"),
    # Go gin/chi
    SearchQuery(regex=r"\b(POST|GET|PUT|PATCH|DELETE)\s*\(", glob="**/*.go", why="Go std http handlers"),
    SearchQuery(regex=r"\b(Handle|HandleFunc)\s*\(", glob="**/*.go", why="Go mux/chi"),
    # Java Spring
    SearchQuery(regex=r"@RequestMapping|@GetMapping|@PostMapping|@PutMapping|@DeleteMapping", glob="**/*.java", why="Spring annotations"),
    # Ruby Rails
    SearchQuery(regex=r"resources\s+:|get\s+['\"]|post\s+['\"]", glob="**/*.rb", why="Rails routes"),
]

def _grep_file(path: str, regex: str, context: int, limit: int) -> List[Match]:
    matches = []
    try:
        pattern = re.compile(regex, re.IGNORECASE)
    except re.error as e:
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    for i, line in enumerate(lines, start=1):
        if pattern.search(line):
            start = max(0, i - context - 1)
            end = min(len(lines), i + context)
            before = [l.rstrip("\n") for l in lines[start:i-1]]
            after = [l.rstrip("\n") for l in lines[i:end]]
            matches.append(Match(file=path, line=i, match=line.strip(), before=before, after=after))
            if len(matches) >= limit:
                break
    return matches

def multi_search(repo_dir: str, queries: List[SearchQuery], context: int = 20, limit: int = 50) -> dict:
    results = {}
    for idx, q in enumerate(queries):
        files = glob.glob(os.path.join(repo_dir, q.glob), recursive=True)
        acc = []
        for f in files:
            acc.extend(_grep_file(f, q.regex, context, limit))
            if len(acc) >= limit:
                break
        results[idx] = acc
    return results
