import os
import tempfile
from git import Repo
from urllib.parse import urlparse

def repo_name_from_url(repo_url: str) -> str:
    parsed = urlparse(repo_url)
    name = os.path.basename(parsed.path)
    return name[:-4] if name.endswith(".git") else name

def clone_repo(repo_url: str) -> str:
    workdir = tempfile.mkdtemp(prefix="ai-openapi-")
    Repo.clone_from(repo_url, workdir, depth=1, multi_options=["--no-tags"])
    return workdir

def cleanup_repo(repo_dir: str) -> None:
    # Keep placeholder in case you want to delete the temp dir later.
    pass
