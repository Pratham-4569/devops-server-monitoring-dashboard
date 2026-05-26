# API reference (planned)

Base path: `/api` (proxied by Nginx to the Flask service).

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Liveness check (implemented) |
| `/api/cpu` | GET | CPU usage percentage |
| `/api/ram` | GET | Memory used / total |
| `/api/disk` | GET | Disk usage per mount point |
| `/api/network` | GET | Network bytes sent/received per second |
| `/api/docker` | GET | Running containers |

## Response envelope (target)

```json
{
  "status": "ok",
  "timestamp": "2026-05-26T12:00:00+00:00",
  "data": {}
}
```

Metric endpoints will be added in Phase 2 (Backend API).
