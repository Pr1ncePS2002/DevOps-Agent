"""Docker adapter — uses Docker SDK, no raw shell. Structured error handling."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from app.common.logging import logger

try:
    import docker
    import docker.errors
except ImportError:
    docker = None  # type: ignore[assignment]


_client_lock = threading.Lock()
_client_instance = None


def _get_client():
    """Return a lazily-initialized, thread-safe singleton Docker client."""
    global _client_instance
    if _client_instance is not None:
        return _client_instance
    with _client_lock:
        if _client_instance is not None:
            return _client_instance
        if docker is None:
            raise RuntimeError("Docker SDK not installed. Run: pip install docker")
        _client_instance = docker.from_env()
        return _client_instance


def image_exists(image_tag: str) -> bool:
    """Check if image exists locally."""
    try:
        client = _get_client()
        client.images.get(image_tag)
        return True
    except docker.errors.ImageNotFound:
        return False
    except docker.errors.APIError as exc:
        logger.warning("docker_image_check_failed", image=image_tag, error=str(exc))
        return False


def container_exists(container_id: str) -> bool:
    """Check if container exists (running or stopped)."""
    try:
        client = _get_client()
        c = client.containers.get(container_id)
        return c is not None
    except docker.errors.NotFound:
        return False
    except docker.errors.APIError as exc:
        logger.warning("docker_container_check_failed", container=container_id, error=str(exc))
        return False


def remove_container_safe(container_id: str | None, timeout: int = 10) -> bool:
    """Stop and remove container. Never fails silently."""
    if not container_id:
        return True
    log = logger.bind(component="docker-adapter")
    try:
        client = _get_client()
        c = client.containers.get(container_id)
        c.stop(timeout=timeout)
        c.remove()
        log.info("container_removed", container_id=container_id)
        return True
    except docker.errors.NotFound:
        log.info("container_already_gone", container_id=container_id)
        return True
    except Exception as e:
        log.warning("container_remove_failed", container_id=container_id, error=str(e))
        return False


def build_image(
    context_path: Path,
    dockerfile_path: Path,
    tag: str,
    *,
    timeout: int = 600,
    log_callback: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Build Docker image. Stream build logs via callback. Returns (success, message)."""
    log = logger.bind(component="docker-adapter")
    context_str = str(context_path.resolve())
    dockerfile_name = dockerfile_path.name

    try:
        client = _get_client()
        stream = client.api.build(
            path=context_str,
            dockerfile=dockerfile_name,
            tag=tag,
            decode=True,
        )
        for chunk in stream:
            if isinstance(chunk, dict):
                if "stream" in chunk and chunk["stream"]:
                    raw_line = chunk["stream"].rstrip()
                    line = raw_line.encode("ascii", errors="replace").decode("ascii")
                    if line and log_callback:
                        log_callback(line)
                    log.debug("docker_build", line=line[:200])
                if "error" in chunk:
                    err = chunk["error"]
                    log.error("docker_build_error", error=err)
                    return False, err
        log.info("docker_build_success", tag=tag)
        return True, f"Built {tag}"
    except docker.errors.BuildError as e:
        msg = str(e)
        log.exception("docker_build_failed", error=msg)
        return False, msg
    except Exception as e:
        msg = str(e)
        log.exception("docker_build_failed", error=msg)
        return False, msg


def _load_env_vars(path: Path) -> list[str]:
    """Load KEY=VALUE lines from env file. Never log content."""
    if not path.exists():
        return []
    lines = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            lines.append(line)
    return lines


def run_container(
    image_tag: str,
    *,
    name: str | None = None,
    env_file: Path | None = None,
    ports: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[bool, str | None]:
    """Run container. Returns (success, container_id or error message)."""
    log = logger.bind(component="docker-adapter")

    try:
        client = _get_client()
        run_kw: dict = {
            "detach": True,
            "remove": False,
        }
        if name:
            run_kw["name"] = name
        if ports:
            run_kw["ports"] = ports
        if env_file and env_file.exists():
            env_list = _load_env_vars(env_file)
            if env_list:
                run_kw["environment"] = env_list

        container = client.containers.run(image_tag, **run_kw)
        cid = container.id if hasattr(container, "id") else str(container)
        log.info("container_started", container_id=cid, image=image_tag)
        return True, cid
    except docker.errors.ImageNotFound:
        return False, f"Image {image_tag} not found"
    except Exception as e:
        msg = str(e)
        log.exception("docker_run_failed", error=msg)
        return False, msg


def container_health_check(
    container_id: str,
    *,
    retries: int = 5,
    interval: float = 2.0,
) -> bool:
    """Check if container is running, with retries."""
    for attempt in range(retries):
        try:
            client = _get_client()
            c = client.containers.get(container_id)
            c.reload()
            if c.status == "running":
                return True
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(interval)
    return False
