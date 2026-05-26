# Project structure

```
.
├── backend/                 # Flask REST API (app factory + blueprint)
│   ├── app/
│   │   ├── routes/          # /api/* HTTP handlers
│   │   └── services/        # psutil + Docker SDK (Phase 2)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py               # Local development entry point
│   └── wsgi.py              # Gunicorn entry point
│
├── frontend/                # Static HTML / CSS / JS (Nginx-served)
│   ├── css/
│   ├── js/                  # api.js · charts.js · app.js
│   └── index.html
│
├── nginx/                   # Reverse proxy + static file server
│   ├── Dockerfile
│   └── nginx.conf
│
├── ansible/                 # Host provisioning and deployment
│   ├── inventory/
│   ├── roles/
│   └── playbook.yml
│
├── docs/
├── docker-compose.yml
├── requirements.txt         # Root pointer to backend deps
├── .env.example
└── README.md
```

## Data flow

1. Browser loads static assets from **web** (Nginx).
2. Browser calls `/api/*`; Nginx proxies to **api** (Flask/Gunicorn).
3. Flask reads live metrics via **services** (Phase 2) using psutil and the Docker SDK.
4. **Ansible** installs Docker on a Linux host and starts the Compose stack.
