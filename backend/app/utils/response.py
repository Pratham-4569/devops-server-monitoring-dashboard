"""Reusable JSON response builders so every endpoint shares the same shape."""

from flask import jsonify

from app.utils.time import utc_now_iso


def success_response(data, status_code=200):
    """
    Standard success envelope used by all metric endpoints.

    Example:
        {"status": "ok", "timestamp": "...", "data": {...}}
    """
    body = {
        "status": "ok",
        "timestamp": utc_now_iso(),
        "data": data,
    }
    return jsonify(body), status_code


def error_response(message, status_code=500, code=None):
    """
    Standard error envelope for handled failures.

    Example:
        {"status": "error", "timestamp": "...", "message": "...", "code": "..."}
    """
    body = {
        "status": "error",
        "timestamp": utc_now_iso(),
        "message": message,
    }
    if code:
        body["code"] = code
    return jsonify(body), status_code
