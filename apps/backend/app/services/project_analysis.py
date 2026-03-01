"""Detect tech stack and generate Dockerfile if missing."""
from __future__ import annotations

from pathlib import Path

from app.common.logging import logger

NODE_DOCKERFILE = '''# Auto-generated for Node.js project
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .
RUN npm run build 2>/dev/null || true

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app ./
EXPOSE 3000
CMD ["npm", "start"]
'''

PYTHON_DOCKERFILE = '''# Auto-generated for Python project
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || pip install -e . 2>/dev/null || true
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''


def detect_stack(workspace_path: Path) -> str:
    """Detect project type: node, python, or docker."""
    if (workspace_path / "Dockerfile").exists() or (workspace_path / "dockerfile").exists():
        return "docker"
    if (workspace_path / "package.json").exists():
        return "node"
    if (workspace_path / "requirements.txt").exists() or (workspace_path / "pyproject.toml").exists():
        return "python"
    return "unknown"


def get_existing_dockerfile(workspace_path: Path) -> Path | None:
    for name in ("Dockerfile", "dockerfile"):
        p = workspace_path / name
        if p.exists():
            return p
    return None


def generate_dockerfile(workspace_path: Path, stack: str) -> Path:
    """Generate and save Dockerfile. Returns path."""
    if stack == "node":
        content = NODE_DOCKERFILE
    elif stack == "python":
        content = PYTHON_DOCKERFILE
    else:
        content = NODE_DOCKERFILE  # fallback
    path = workspace_path / "Dockerfile"
    path.write_text(content)
    logger.bind(component="project-analysis").info("dockerfile_generated", path=str(path), stack=stack)
    return path


def analyze_project(workspace_path: Path) -> dict:
    """
    Analyze project. Returns:
    {
        detected_stack: str,
        dockerfile_path: str | None,
        dockerfile_generated: bool,
        default_port: int,
    }
    """
    workspace_path = Path(workspace_path)
    if not workspace_path.exists():
        raise FileNotFoundError(f"Workspace does not exist: {workspace_path}")

    stack = detect_stack(workspace_path)
    existing = get_existing_dockerfile(workspace_path)
    generated = False

    if existing:
        dockerfile_path = str(existing)
    else:
        if stack in ("node", "python"):
            p = generate_dockerfile(workspace_path, stack)
            dockerfile_path = str(p)
            generated = True
        else:
            dockerfile_path = None

    default_port = 3000 if stack == "node" else 8000
    return {
        "detected_stack": stack,
        "dockerfile_path": dockerfile_path,
        "dockerfile_generated": generated,
        "default_port": default_port,
    }
