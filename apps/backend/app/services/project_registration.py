"""Project registration: validate path/url, clone if GitHub, persist."""
from __future__ import annotations

import re
from pathlib import Path

from app.common.logging import logger
from app.common.settings import settings

from app.adapters.git_adapter import clone_repo, is_valid_github_url


def _is_path_safe(path_str: str) -> bool:
    """Ensure path is under allowed roots to prevent traversal."""
    path_str = path_str.strip().strip('"\'')
    if not path_str:
        return False
    try:
        resolved = Path(path_str).resolve()
    except Exception:
        return False
    roots = [p.strip() for p in settings.allowed_repo_roots.split(",") if p.strip()]
    if roots:
        for r in roots:
            try:
                root = Path(r).resolve()
                if str(resolved).startswith(str(root)):
                    return True
            except Exception:
                continue
        return False
    return resolved.exists()


def register_local(path_or_url: str) -> tuple[Path, str]:
    """Validate local path. Returns (workspace_path, name)."""
    path_str = path_or_url.strip().strip('"\'')
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"Path does not exist: {path_str}")
    if not p.is_dir():
        raise ValueError("Path must be a directory")
    if not _is_path_safe(path_str):
        raise PermissionError("Path not under allowed roots. Set ALLOWED_REPO_ROOTS.")
    return p, p.name


def register_github(path_or_url: str) -> tuple[Path, str]:
    """Clone GitHub repo into workspace. Returns (workspace_path, name)."""
    url = path_or_url.strip()
    if not is_valid_github_url(url):
        raise ValueError(f"Invalid GitHub URL: {url}")

    settings.workspace_root.mkdir(parents=True, exist_ok=True)
    # Extract repo name for folder (e.g. user/repo -> repo)
    parts = url.rstrip("/").replace(".git", "").split("/")
    repo_name = parts[-1] if parts else "repo"
    target = settings.workspace_root / repo_name

    if target.exists():
        # Already cloned; reuse
        logger.bind(component="project-registration").info("workspace_exists", path=str(target))
        return target, repo_name

    clone_repo(url, target)
    return target, repo_name


def register_project(source_type: str, path_or_url: str) -> tuple[Path, str]:
    """Register project. Returns (workspace_path, name)."""
    if source_type == "local":
        return register_local(path_or_url)
    if source_type == "github":
        return register_github(path_or_url)
    raise ValueError(f"Unknown source_type: {source_type}. Use 'local' or 'github'.")
