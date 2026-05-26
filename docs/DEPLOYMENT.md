# Deployment

## Local (Docker Compose)

```bash
cp .env.example .env
docker compose up --build
```

Dashboard: `http://localhost:3000` (default `WEB_PORT`).

Health check: `curl http://localhost:3000/api/health`

## Remote (Ansible)

1. Add hosts to `ansible/inventory/hosts.ini` under `[monitoring]`.
2. Implement role tasks (Phase 5).
3. Run:

```bash
ansible-playbook ansible/playbook.yml -i ansible/inventory/hosts.ini
```

## Ports

| Service | Internal | Host |
|---------|----------|------|
| web (Nginx) | 80 | 3000 (configurable) |
| api (Flask) | 5000 | not exposed |

The API container mounts `/var/run/docker.sock` (read-only) so the Docker SDK can list containers on the host.
