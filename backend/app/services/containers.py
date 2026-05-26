"""
List running Docker containers via the official Docker SDK.

The API container must mount /var/run/docker.sock (see docker-compose.yml) so
docker.from_env() can talk to the host daemon.
"""

from datetime import datetime, timezone

import docker
from docker.errors import DockerException

from app.exceptions import DockerError

# Reuse one client for all requests (lazy singleton) instead of connecting every time.
_docker_client = None


def get_docker_client():
    """
    Return a shared Docker client, creating it on first use.

    docker.from_env() reads DOCKER_HOST / the default Unix socket once; reusing
    the client avoids extra connection setup on every /api/containers poll.
    """
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


def _format_created(created_value) -> str | None:
    """Normalize Docker's created field to an ISO timestamp string."""
    if created_value is None:
        return None
    if isinstance(created_value, str):
        return created_value
    if isinstance(created_value, datetime):
        if created_value.tzinfo is None:
            created_value = created_value.replace(tzinfo=timezone.utc)
        return created_value.isoformat()
    return str(created_value)


def get_containers() -> dict:
    """Return running containers plus metadata about Docker availability."""
    try:
        client = get_docker_client()
        running = client.containers.list()
    except DockerException as exc:
        raise DockerError(f"Docker daemon unavailable: {exc}") from exc
    except FileNotFoundError as exc:
        raise DockerError(
            "Docker socket not found. Mount /var/run/docker.sock into the API container."
        ) from exc

    containers = []
    for container in running:
        # Docker names are stored with a leading slash, e.g. "/monitor-api".
        name = (container.name or "").lstrip("/")
        image_tags = container.image.tags if container.image else []
        image = image_tags[0] if image_tags else (container.image.short_id if container.image else "unknown")

        containers.append(
            {
                "id": container.short_id,
                "name": name,
                "image": image,
                "status": container.status,
                "created_at": _format_created(container.attrs.get("Created")),
            }
        )

    return {
        "containers": containers,
        "count": len(containers),
        "docker_available": True,
    }


def get_containers_safe() -> dict:
    """
    Same as get_containers() but never raises — used when you prefer a soft failure.

    Routes use get_containers() and map DockerError to JSON; this helper is available
    if you later want optional container data on a combined endpoint.
    """
    try:
        return get_containers()
    except DockerError as exc:
        return {
            "containers": [],
            "count": 0,
            "docker_available": False,
            "warning": exc.message,
        }
