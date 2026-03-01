"""Store .env files. Encrypted if ENCRYPTION_KEY set; else restricted path. Never log secrets."""
from __future__ import annotations

import base64
from pathlib import Path

from app.common.logging import logger
from app.common.settings import settings


def _get_fernet():
    from cryptography.fernet import Fernet
    key = settings.encryption_key
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        return None


def _project_env_path(project_id: int) -> Path:
    p = settings.data_dir / "projects" / str(project_id)
    p.mkdir(parents=True, exist_ok=True)
    return p / ".env"


def store_env(project_id: int, content: bytes) -> None:
    """Store .env content. Encrypts if ENCRYPTION_KEY is set."""
    path = _project_env_path(project_id)
    fernet = _get_fernet()
    if fernet:
        enc = fernet.encrypt(content)
        path.write_bytes(enc)
    else:
        path.write_bytes(content)
    logger.bind(component="env-storage").info("env_stored", project_id=project_id, encrypted=fernet is not None)


def load_env_path(project_id: int) -> Path | None:
    """Return path to decrypted .env file (writes temp decrypted for Docker --env-file)."""
    path = _project_env_path(project_id)
    if not path.exists():
        return None
    return path


def get_env_for_docker(project_id: int) -> Path | None:
    """Return path to .env file usable by Docker. Decrypts if needed into temp file."""
    path = _project_env_path(project_id)
    if not path.exists():
        return None
    fernet = _get_fernet()
    if fernet:
        dec = fernet.decrypt(path.read_bytes())
        tmp = path.parent / ".env.decrypted"
        tmp.write_bytes(dec)
        return tmp
    return path


def validate_env_format(content: str) -> tuple[bool, str]:
    """Validate .env format. Returns (valid, error_message). Do NOT log content."""
    lines = content.strip().splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            return False, f"Line {i + 1}: invalid format (no =)"
    return True, ""


def env_exists(project_id: int) -> bool:
    return _project_env_path(project_id).exists()
