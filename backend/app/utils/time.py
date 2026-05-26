"""Small time helpers used across API responses."""

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string for JSON payloads."""
    return datetime.now(timezone.utc).isoformat()
