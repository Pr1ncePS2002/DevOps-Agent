from __future__ import annotations

from pathlib import Path

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file(start: Path) -> Path | None:
    current = start
    for _ in range(8):
        candidate = current / ".env"
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


_DEFAULT_ENV_FILE = _find_env_file(Path(__file__).resolve())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_DEFAULT_ENV_FILE) if _DEFAULT_ENV_FILE else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    host: str = "127.0.0.1"  # maps to HOST in .env
    api_port: int = 3001  # maps to API_PORT
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Storage
    data_dir: Path = Path("./data")
    database_url: str = "sqlite:///./data/dev.db"  # maps to DATABASE_URL

    # Queue
    redis_url: str = "redis://localhost:6379"
    rq_queue_name: str = "ai-devops"

    # LLM
    llm_provider: str = "OPENAI"  # OLLAMA | OPENAI | GEMINI
    openai_api_key: str | None = None
    openai_base_url: AnyUrl = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-pro"

    ollama_base_url: AnyUrl = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Deployment Providers
    deploy_provider: str = "local"  # local | vercel | render
    vercel_token: str | None = None
    vercel_org_id: str | None = None
    vercel_project_id: str | None = None
    render_api_key: str | None = None
    render_service_id: str | None = None

    # Safety
    dry_run: bool = True
    enable_local_execution: bool = False


settings = Settings()  # singleton


def get_database_url() -> str:
    """Normalize DATABASE_URL values.

    Supports:
    - sqlite:///./data/dev.db
    - file:./data/dev.db (common in JS ecosystems)
    """

    url = settings.database_url
    if url.startswith("file:"):
        # Convert to SQLAlchemy SQLite URL
        path = url.removeprefix("file:")
        if path.startswith("/"):
            return f"sqlite://{path}"
        return f"sqlite:///./{path.lstrip('./')}"
    return url
