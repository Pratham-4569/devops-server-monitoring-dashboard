"""Application-specific errors raised by services and handled in routes."""


class AppError(Exception):
    """Base error with an HTTP status code the route layer can return as JSON."""

    def __init__(self, message, status_code=500, code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class MetricsError(AppError):
    """Raised when psutil cannot read host metrics (permissions, unsupported OS, etc.)."""

    def __init__(self, message, code="METRICS_ERROR"):
        super().__init__(message, status_code=500, code=code)


class DockerError(AppError):
    """Raised when the Docker daemon is unreachable from the API container."""

    def __init__(self, message, code="DOCKER_UNAVAILABLE"):
        super().__init__(message, status_code=503, code=code)
