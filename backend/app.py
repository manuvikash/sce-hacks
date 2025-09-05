from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from os import path
from fastapi.middleware.cors import CORSMiddleware

from core.types import (
    GenerateRequest,
    GenerateResponse,
    FileIndex,
    DiscoveredRoute,
    RouteDef,
)
from core.gitops import clone_repo, repo_name_from_url
from core.indexer import build_inventory
from core.llm import plan_search, extract_routes, enrich_route
from core.searcher import multi_search, FALLBACK_QUERIES
from core.reader import read_snippet
from core.normalize import normalize_path, extract_path_params
from core.spec import (
    build_openapi_skeleton,
    merge_route,
    validate_openapi,
    export_spec,
    _downgrade_schemas,
)

app = FastAPI(title="AI OpenAPI Generator", version="0.1.0")
# allow your frontend’s origin (adjust the URL/port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # your frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate", response_model=GenerateResponse)
def post_generate(req: GenerateRequest):
    try:
        # Step 1: clone + index
        repo_dir = clone_repo(req.repo_url)
        inv: list[FileIndex] = build_inventory(
            repo_dir,
            exts=req.options.exts,
            max_files=req.options.max_files,
            max_bytes=req.options.max_bytes_per_file,
        )

        # Step 2: LLM plan + search
        plan = plan_search(inv)
        matches = multi_search(
            repo_dir, plan.searches, context=req.options.context_lines
        )

        used_fallback = False
        if sum(len(v) for v in matches.values()) == 0:
            used_fallback = True
            matches = multi_search(
                repo_dir, FALLBACK_QUERIES, context=req.options.context_lines
            )

        # Step 3: Extract endpoints
        routes: list[DiscoveredRoute] = extract_routes(matches)

        # Step 4: Build OpenAPI
        title = repo_name_from_url(req.repo_url) + " (Generated)"
        spec = build_openapi_skeleton(title=title)

        merged = 0
        for r in routes[: req.options.max_routes]:
            norm = normalize_path(r.raw_path)
            params = extract_path_params(norm)
            snippet = read_snippet(repo_dir, r.file, r.line, radius=60)
            enr = enrich_route(snippet, r.method, r.raw_path)

            route_def = RouteDef(
                method=r.method,
                path=norm,
                parameters=params,
                requestBody=enr.requestBody,
                responses=enr.responses or {"200": {"description": "OK"}},
                summary=enr.summary,
                auth=enr.auth,
                evidence={"file": r.file, "line": r.line, "quotes": r.evidence},
            ).model_dump()

            merge_route(spec, route_def)
            merged += 1

        valid, errors = validate_openapi(spec)
        notes_extra = []
        if not valid:
            _downgrade_schemas(spec)
            valid2, _ = validate_openapi(spec)
            if not valid2:
                notes_extra.append(
                    "Spec still invalid after downgrade; check logs."
                )
            else:
                notes_extra.append(
                    "Some schemas downgraded to permissive object."
                )

        spec_path = export_spec(
            spec, path.join(repo_dir, "openapi.generated.json")
        )

        return GenerateResponse(
            status="ok",
            spec_path=spec_path,
            routes_found=len(routes),
            rounds_used=1 + int(used_fallback),
            skipped={"files": 0, "routes": max(0, len(routes) - merged)},
            notes=[
                "Step 1 complete: repo cloned and indexed.",
                "Step 2 complete: planned searches and ran regex.",
                "Step 3 complete: extracted endpoints with evidence.",
                "Step 4 complete: assembled and validated OpenAPI spec.",
            ]
            + notes_extra,
            report={
                "repo": repo_name_from_url(req.repo_url),
                "inventory_count": len(inv),
                "frameworks": plan.frameworks,
                "searches": [
                    q.dict()
                    for q in (
                        plan.searches if not used_fallback else FALLBACK_QUERIES
                    )
                ],
                "matches_counts": {
                    str(k): len(v) for k, v in matches.items()
                },
                "routes_sample": [r.dict() for r in routes[:10]],
                "spec_servers": [
                    s["url"] for s in spec.get("servers", [])
                ],
                "paths_count": len(spec.get("paths", {})),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return JSONResponse({"ok": True, "service": "AI OpenAPI Generator"})
