"""
HTTP routes for the monitoring API.

Keep handlers thin: call a service, return JSON. Logic lives in app/services/;
response shape lives in app/utils/response.py.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify

from app.exceptions import AppError
from app.services import containers as container_service
from app.services import metrics as metrics_service
from app.utils.response import error_response, success_response

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _handle_service_call(build_data):
    """
    Run a service callable and map errors to JSON responses.

    build_data: zero-argument callable returning the dict to place under "data".
    """
    try:
        return success_response(build_data())
    except AppError as exc:
        return error_response(exc.message, status_code=exc.status_code, code=exc.code)
    except Exception:
        # Fallback so API clients never receive Flask's default HTML error pages.
        return error_response(
            "An unexpected error occurred",
            status_code=500,
            code="INTERNAL_ERROR",
        )


@api_bp.get("/health")
def health():
    """Liveness probe for Docker healthcheck and load balancers."""
    return jsonify(
        {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@api_bp.get("/metrics")
def all_metrics():
    """CPU, memory, disk, and network in one response (preferred for dashboard polling)."""
    return _handle_service_call(metrics_service.get_all_metrics)


@api_bp.get("/cpu")
def cpu():
    """Current CPU utilization (%)."""
    return _handle_service_call(
        lambda: {"cpu_percent": metrics_service.get_cpu_percent()}
    )


@api_bp.get("/memory")
def memory():
    """RAM usage (bytes and percent)."""
    return _handle_service_call(metrics_service.get_memory)


@api_bp.get("/disk")
def disk():
    """Disk usage per mount point."""
    return _handle_service_call(lambda: {"disks": metrics_service.get_disk()})


@api_bp.get("/network")
def network():
    """Network throughput (bytes per second)."""
    return _handle_service_call(metrics_service.get_network_rates)


@api_bp.get("/containers")
def containers():
    """Running Docker containers on the host."""
    return _handle_service_call(container_service.get_containers)
