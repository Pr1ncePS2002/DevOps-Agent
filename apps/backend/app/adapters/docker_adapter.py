"""Docker adapter — uses Docker SDK, no raw shell. Structured error handling."""
from __future__ import annotations

import time
from pathlib import Path

from app.common.logging import logger


def _get_client():
    import docker
    return docker.from_env()


def image_exists(image_tag: str) -> bool:
    """Check if image exists locally."""
    try:
        client = _get_client()
        client.images.get(image_tag)
        return True
    except Exception:
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass


def container_exists(container_id: str) -> bool:
    """Check if container exists (running or stopped)."""
    try:
        client = _get_client()
        c = client.containers.get(container_id)
        return c is not None
    except Exception:
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass


def remove_container_safe(container_id: str | None, timeout: int = 10) -> bool:
    """Stop and remove container. Never fails silently."""
    if not container_id:
        return True
    log = logger.bind(component="docker-adapter")
    try:
        client = _get_client()
        try:
            c = client.containers.get(container_id)
            c.stop(timeout=timeout)
            c.remove()
            log.info("container_removed", container_id=container_id)
            return True
        except Exception as e:
            log.warning("container_remove_failed", container_id=container_id, error=str(e))
            return False
    finally:
        try:
            client.close()
        except Exception:
            pass


def build_image(
    context_path: Path,
    dockerfile_path: Path,
    tag: str,
    *,
    timeout: int = 600,
    log_callback: callable = None,
) -> tuple[bool, str]:
    """Build Docker image. Stream build logs via callback. Returns (success, message)."""
    import docker

    log = logger.bind(component="docker-adapter")
    context_str = str(context_path.resolve())
    dockerfile_dir = str(dockerfile_path.parent)
    dockerfile_name = dockerfile_path.name

    try:
        client = _get_client()
        try:
            stream = client.api.build(
                path=context_str,
                dockerfile=dockerfile_name,
                tag=tag,
                decode=True,
            )
            for chunk in stream:
                if isinstance(chunk, dict):
                    if "stream" in chunk and chunk["stream"]:
                        line = chunk["stream"].rstrip()
                        if line and log_callback:
                            log_callback(line)
                        log.debug("docker_build", line=line[:200])
                    if "error" in chunk:
                        err = chunk["error"]
                        log.error("docker_build_error", error=err)
                        return False, err
            log.info("docker_build_success", tag=tag)
            return True, f"Built {tag}"
        finally:
            client.close()
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
    import docker

    log = logger.bind(component="docker-adapter")

    try:
        client = _get_client()
        try:
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
        finally:
            client.close()
    except docker.errors.ImageNotFound:
        return False, f"Image {image_tag} not found"
    except Exception as e:
        msg = str(e)
        log.exception("docker_run_failed", error=msg)
        return False, msg


def container_health_check(container_id: str) -> bool:
    """Check if container is running."""
    try:
        client = _get_client()
        try:
            c = client.containers.get(container_id)
            c.reload()
            return c.status == "running"
        finally:
            client.close()
    except Exception:
        return False
