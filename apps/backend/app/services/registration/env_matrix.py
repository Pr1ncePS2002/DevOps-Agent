PLATFORM_MATRIX = {
    "local": ["local", "docker"],
    "github": ["local", "docker", "vercel", "render"],
}

# Required env vars per source × platform.
# These are REAL runtime env vars, not paths (workspace path is already in the Project record).
ENV_MATRIX: dict[str, list[str]] = {
    "local:local":   [],                                          # Nothing special needed
    "local:docker":  ["APP_PORT"],                               # Port to expose
    "github:local":  [],
    "github:docker": ["APP_PORT"],
    "github:vercel": ["VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID"],
    "github:render": ["RENDER_API_KEY", "RENDER_SERVICE_ID"],
}


def get_required_env_keys(source: str, platform: str) -> list[str]:
    """Return required env var keys for a given source × platform combo."""
    return ENV_MATRIX.get(f"{source}:{platform}", [])


def validate_env(env: dict, source: str, platform: str) -> list[str]:
    """
    Returns a list of missing required env keys.
    Non-blocking — caller decides whether to warn or block.
    """
    required = get_required_env_keys(source, platform)
    return [k for k in required if not env.get(k, "").strip()]


def validate_platform_compat(source: str, platform: str) -> None:
    """
    Raises ValueError if this source × platform combination is not supported.
    """
    allowed = PLATFORM_MATRIX.get(source)
    if allowed is None:
        raise ValueError(f"Unknown source type: {source!r}")
    if platform not in allowed:
        raise ValueError(
            f"Platform {platform!r} is not available for source type {source!r}. "
            f"Allowed: {allowed}"
        )
