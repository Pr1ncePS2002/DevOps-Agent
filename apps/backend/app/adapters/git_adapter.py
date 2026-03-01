"""Git adapter — whitelisted clone only. No raw shell."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from app.common.logging import logger


GITHUB_URL_PATTERN = re.compile(
    r"^https?://(?:github\.com|git@github\.com)[/:][\w\-]+/[\w\-\.]+(?:\.git)?$",
    re.IGNORECASE,
)


def is_valid_github_url(url: str) -> bool:
    """Validate GitHub URL format."""
    return bool(GITHUB_URL_PATTERN.match(url.strip()))


def clone_repo(url: str, target_dir: Path, timeout_seconds: int = 120) -> None:
    """Clone a GitHub repo into target_dir. Uses whitelisted git clone only."""
    if not is_valid_github_url(url):
        raise ValueError(f"Invalid GitHub URL: {url}")

    target_dir.mkdir(parents=True, exist_ok=True)
    log = logger.bind(component="git-adapter")
    log.info("git_clone_start", url=url, target=str(target_dir))

    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(target_dir)],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )

    if result.returncode != 0:
        err = result.stderr or result.stdout or "Unknown error"
        log.error("git_clone_failed", returncode=result.returncode, stderr=err[:500])
        raise RuntimeError(f"git clone failed: {err[:300]}")

    log.info("git_clone_success", path=str(target_dir))
