# Ansible

Provisions a Linux host and deploys the Docker Compose stack.

## Layout

```
ansible/
├── inventory/hosts.ini   # Target hosts ([monitoring] group)
├── vars/main.yml         # Shared variables
├── playbook.yml          # Entry point
└── roles/
    ├── docker/           # Install Docker + Compose
    ├── security/         # UFW, SSH hardening
    └── deploy/           # Copy project, start containers
```

## Usage

```bash
ansible-playbook ansible/playbook.yml -i ansible/inventory/hosts.ini
```

Role task files (`roles/*/tasks/main.yml`) are added in Phase 5. The playbook entry point and inventory are ready now.
