# DevOps Server Monitoring Dashboard

Real-time server monitoring dashboard — Flask API, static frontend, Docker Compose, and Ansible deployment.

**Stack:** Python 3.11 · Flask · Vanilla JS · Chart.js · Nginx · Docker · Ansible

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000` · Health: `curl http://localhost:3000/api/health`

## Project layout

See [docs/STRUCTURE.md](docs/STRUCTURE.md).

## Documentation

- [docs/README.md](docs/README.md) — index
- [docs/API.md](docs/API.md) — planned endpoints
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Docker and Ansible

## Development

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

API: `http://localhost:5000/api/health`

## Implementation phases

This repository is scaffolded for phased delivery (Foundation → Backend → Frontend → Docker → Ansible → Testing → Docs). See `docs/` and the project TASKS specification.
