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

# Pseudo filesystem types — not useful on a storage dashboard.
_IGNORED_FSTYPES = frozenset(
    {
        "tmpfs",
        "devtmpfs",
        "proc",
        "sysfs",
        "devpts",
        "squashfs",
        "cgroup",
        "cgroup2",
        "mqueue",
        "autofs",
        "efivarfs",
        "securityfs",
        "pstore",
        "bpf",
        "tracefs",
        "fusectl",
        "hugetlbfs",
    }
)

# Docker often bind-mounts these files into containers (not real disks).
_IGNORED_MOUNTPOINTS = frozenset(
    {
        "/etc/resolv.conf",
        "/etc/hostname",
        "/etc/hosts",
    }
)

# Kernel/virtual paths — never show in the UI.
_IGNORED_MOUNT_PREFIXES = ("/proc", "/sys", "/dev", "/run")


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


def _is_user_facing_mount(part) -> bool:
    """
    Return True only for partitions end users care about (real disks / root FS).

    Filters Docker file bind-mounts (/etc/resolv.conf, etc.) and kernel pseudo mounts.
    """
    mountpoint = part.mountpoint
    fstype = part.fstype or ""

    if not fstype:
        return False
    if mountpoint in _IGNORED_MOUNTPOINTS:
        return False
    if any(mountpoint.startswith(prefix) for prefix in _IGNORED_MOUNT_PREFIXES):
        return False
    # Single-file bind mounts under /etc (e.g. /etc/resolv.conf)
    if mountpoint.startswith("/etc/") and "." in mountpoint.rsplit("/", 1)[-1]:
        return False

    # Container root is often overlay on / — keep that one, skip other overlay mounts.
    if fstype == "overlay":
        return mountpoint == "/"

    if fstype in _IGNORED_FSTYPES:
        return False

    # Typical block devices: /dev/sda1, /dev/nvme0n1p1, etc.
    if part.device.startswith("/dev/"):
        return True

    # Fallback: always include root even if device name is opaque.
    return mountpoint == "/"


def _disk_entry_from_path(mountpoint: str, device: str, fstype: str) -> dict | None:
    """Build one disk dict from a path, or None if usage cannot be read."""
    try:
        usage = psutil.disk_usage(mountpoint)
    except (PermissionError, OSError):
        return None

    return {
        "device": device,
        "mountpoint": mountpoint,
        "fstype": fstype,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "percent": round(usage.percent, 2),
    }


def get_disk() -> list:
    """
    Return usage for user-facing filesystems only.

    Docker containers expose many internal mounts; we filter those so the dashboard
    shows root (/) and real block devices (e.g. /dev/sda1) when present.
    """
    disks = []
    root_meta = {"device": "root", "fstype": "unknown"}

    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception as exc:
        raise MetricsError(f"Unable to list disk partitions: {exc}") from exc

    for part in partitions:
        if part.mountpoint == "/":
            root_meta = {"device": part.device, "fstype": part.fstype or "unknown"}
        if not _is_user_facing_mount(part):
            continue

        entry = _disk_entry_from_path(part.mountpoint, part.device, part.fstype)
        if entry:
            disks.append(entry)

    # If everything was filtered (unusual), still report root filesystem usage.
    if not disks:
        entry = _disk_entry_from_path(
            "/",
            root_meta["device"],
            root_meta["fstype"],
        )
        if entry:
            disks.append(entry)

    # Sort: root first, then by size (largest first) for stable dashboard display.
    disks.sort(key=lambda d: (d["mountpoint"] != "/", -d["total_bytes"]))

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
