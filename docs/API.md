# API reference

Base path: `/api` (proxied by Nginx to the Flask service in Docker).

## Response envelope

**Success**

```json
{
  "status": "ok",
  "timestamp": "2026-05-26T12:00:00+00:00",
  "data": {}
}
```

**Error**

```json
{
  "status": "error",
  "timestamp": "2026-05-26T12:00:00+00:00",
  "message": "Human-readable description",
  "code": "METRICS_ERROR"
}
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Liveness check (plain `{status, timestamp}`) |
| `/api/metrics` | GET | **Aggregate:** CPU, memory, disk, and network in one response |
| `/api/cpu` | GET | CPU usage percentage |
| `/api/memory` | GET | RAM used / total (bytes + percent) |
| `/api/disk` | GET | Disk usage per mount point |
| `/api/network` | GET | Network bytes sent/received per second |
| `/api/containers` | GET | Running Docker containers |

### `GET /api/metrics`

Preferred endpoint for dashboard polling (one request instead of four).

```json
{
  "status": "ok",
  "timestamp": "...",
  "data": {
    "cpu": { "cpu_percent": 12.5 },
    "memory": {
      "total_bytes": 17179869184,
      "used_bytes": 8589934592,
      "available_bytes": 8589934592,
      "free_bytes": 4294967296,
      "percent": 50.0
    },
    "disk": {
      "disks": [
        {
          "device": "/dev/sda1",
          "mountpoint": "/",
          "fstype": "ext4",
          "total_bytes": 1000000000,
          "used_bytes": 400000000,
          "free_bytes": 600000000,
          "percent": 40.0
        }
      ]
    },
    "network": {
      "bytes_sent_per_sec": 1024.5,
      "bytes_recv_per_sec": 2048.0,
      "sample_interval_sec": 1.002
    }
  }
}
```

Note: This endpoint still blocks for ~2 seconds total (CPU ~1s + network ~1s sample).

### `GET /api/cpu`

```json
{
  "status": "ok",
  "timestamp": "...",
  "data": {
    "cpu_percent": 12.5
  }
}
```

### `GET /api/memory`

```json
{
  "status": "ok",
  "timestamp": "...",
  "data": {
    "total_bytes": 17179869184,
    "used_bytes": 8589934592,
    "available_bytes": 8589934592,
    "free_bytes": 4294967296,
    "percent": 50.0
  }
}
```

### `GET /api/disk`

Returns user-facing filesystems only. Docker bind-mounts (`/etc/resolv.conf`, etc.) and pseudo filesystems (`tmpfs`, `proc`, …) are filtered out. Root (`/`) is always included when readable.

```json
{
  "status": "ok",
  "timestamp": "...",
  "data": {
    "disks": [
      {
        "device": "/dev/sda1",
        "mountpoint": "/",
        "fstype": "ext4",
        "total_bytes": 1000000000,
        "used_bytes": 400000000,
        "free_bytes": 600000000,
        "percent": 40.0
      }
    ]
  }
}
```

### `GET /api/network`

Sample interval is ~1 second (two kernel counter reads).

```json
{
  "status": "ok",
  "timestamp": "...",
  "data": {
    "bytes_sent_per_sec": 1024.5,
    "bytes_recv_per_sec": 2048.0,
    "sample_interval_sec": 1.0
  }
}
```

### `GET /api/containers`

Requires Docker socket mount in the API container.

```json
{
  "status": "ok",
  "timestamp": "...",
  "data": {
    "containers": [
      {
        "id": "a1b2c3d4",
        "name": "monitor-api",
        "image": "devops-monitor-api:latest",
        "status": "running",
        "created_at": "2026-05-26T10:00:00+00:00"
      }
    ],
    "count": 1,
    "docker_available": true
  }
}
```

If Docker is unavailable, returns HTTP `503` with `code: DOCKER_UNAVAILABLE`.
