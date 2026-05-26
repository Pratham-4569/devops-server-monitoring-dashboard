"""
Collect live host metrics with psutil.

psutil talks directly to the Linux kernel (via /proc on most systems), so every
call reflects current machine state — no database or background worker needed.
"""

import time

import psutil

from app.exceptions import MetricsError

# How long to wait between network counter samples when computing per-second rates.
NETWORK_SAMPLE_SECONDS = 1.0


def get_cpu_percent() -> float:
    """
    Return overall CPU usage as a percentage (0.0–100.0).

    interval=1 blocks for one second so psutil can average usage across cores.
    """
    try:
        return float(psutil.cpu_percent(interval=1))
    except Exception as exc:
        raise MetricsError(f"Unable to read CPU metrics: {exc}") from exc


def get_memory() -> dict:
    """
    Return RAM totals from virtual_memory().

    Values are bytes (easy for charts) plus a rounded percent for display.
    """
    try:
        mem = psutil.virtual_memory()
        return {
            "total_bytes": mem.total,
            "used_bytes": mem.used,
            "available_bytes": mem.available,
            "free_bytes": mem.free,
            "percent": round(mem.percent, 2),
        }
    except Exception as exc:
        raise MetricsError(f"Unable to read memory metrics: {exc}") from exc


def get_disk() -> list:
    """
    Return usage for each mounted filesystem.

    Some mount points (e.g. Docker internals) may deny access; those are skipped
    instead of failing the whole request.
    """
    disks = []
    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception as exc:
        raise MetricsError(f"Unable to list disk partitions: {exc}") from exc

    for part in partitions:
        # Skip pseudo filesystems with no type.
        if not part.fstype:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue

        disks.append(
            {
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "percent": round(usage.percent, 2),
            }
        )

    return disks


def get_network_rates() -> dict:
    """
    Return bytes sent/received per second.

    psutil only exposes cumulative counters; we sample twice and divide by the
    elapsed time to get a rate (same idea as `speedtest` or `iftop`).
    """
    try:
        first = psutil.net_io_counters()
        # monotonic() measures real elapsed time (immune to system clock changes).
        start = time.monotonic()
        time.sleep(NETWORK_SAMPLE_SECONDS)
        elapsed = time.monotonic() - start
        second = psutil.net_io_counters()

        if elapsed <= 0:
            elapsed = NETWORK_SAMPLE_SECONDS

        bytes_sent_ps = max(0, (second.bytes_sent - first.bytes_sent) / elapsed)
        bytes_recv_ps = max(0, (second.bytes_recv - first.bytes_recv) / elapsed)

        return {
            "bytes_sent_per_sec": round(bytes_sent_ps, 2),
            "bytes_recv_per_sec": round(bytes_recv_ps, 2),
            "sample_interval_sec": round(elapsed, 3),
        }
    except Exception as exc:
        raise MetricsError(f"Unable to read network metrics: {exc}") from exc


def get_all_metrics() -> dict:
    """
    Return CPU, memory, disk, and network in one payload.

    Used by GET /api/metrics so the frontend can poll a single URL instead of
    five separate requests (each with its own blocking sample time).
    """
    return {
        "cpu": {"cpu_percent": get_cpu_percent()},
        "memory": get_memory(),
        "disk": {"disks": get_disk()},
        "network": get_network_rates(),
    }
