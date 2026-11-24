# Deployment Guide

## Overview

Production topology:
```
Internet → Cloudflare DNS → Oracle Cloud Free VM
                                 ├── Caddy (HTTPS reverse proxy)
                                 ├── FastAPI backend (Docker)
                                 └── n8n (Docker)
Cloudflare Pages → React frontend (static)
Neon Cloud → PostgreSQL database
```

---

## 1. Oracle Cloud Always Free VM

### Create VM
1. Go to [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
2. Create an **Ampere A1 (ARM)** instance — 4 OCPUs, 24 GB RAM (Always Free)
3. Choose **Ubuntu 22.04 LTS**
4. Add your SSH public key
5. Enable inbound ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)

### Initial Setup
```bash
ssh ubuntu@<your-vm-ip>

# Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker ubuntu
newgrp docker

# Install Git
sudo apt install -y git

# Clone repo
git clone <your-repo-url> /opt/lead-intelligence-crm
cd /opt/lead-intelligence-crm
```

---

## 2. Neon PostgreSQL

1. Go to [Neon.tech](https://neon.tech) → Create Project → Free Tier
2. Create a database named `lead_intelligence`
3. Copy the connection string (with `?sslmode=require`)
4. Apply migrations:

```bash
# From your local machine or the VM
psql "postgresql://user:pass@host/dbname?sslmode=require" \
  -f backend/migrations/001_initial_schema.sql

# Then seed demo data
DATABASE_URL="your-neon-url" python backend/migrations/seed_data.py
```

---

## 3. Environment Configuration

```bash
cd /opt/lead-intelligence-crm
cp .env.example .env
nano .env
```

Fill in:
- `DATABASE_URL` — your Neon connection string
- `JWT_SECRET_KEY` — generate with: `openssl rand -hex 32`
- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com)
- `SMTP_*` — SendGrid or similar provider
- `CONTACTOUT_API_KEY` / `SNOVIO_*` — if using enrichment providers
- `N8N_WEBHOOK_SECRET` — generate with: `openssl rand -hex 32`
- `CADDY_DOMAIN` — your domain, e.g. `crm.yourdomain.com`

---

## 4. Docker Compose Deployment

```bash
cd /opt/lead-intelligence-crm/docker

# Build and start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f n8n
```

Services started:
| Service | Internal Port | Description |
|---------|---------------|-------------|
| `backend` | 8000 | FastAPI backend |
| `worker` | — | Playwright scraper |
| `n8n` | 5678 | Workflow automation |
| `caddy` | 80, 443 | Reverse proxy + HTTPS |

---

## 5. Caddy HTTPS Configuration

Edit `docker/Caddyfile`:
```
crm.yourdomain.com {
    reverse_proxy backend:8000
}

n8n.yourdomain.com {
    reverse_proxy n8n:5678
}
```

Caddy automatically provisions Let's Encrypt certificates.

---

## 6. Cloudflare DNS

1. Go to Cloudflare Dashboard → Your Domain → DNS
2. Add A records:
   ```
   crm.yourdomain.com  → <Oracle VM IP>  (proxied ✓)
   n8n.yourdomain.com  → <Oracle VM IP>  (proxied ✓)
   ```
3. Recommended SSL/TLS mode: **Full (strict)**

---

## 7. React Frontend — Cloudflare Pages

```bash
# From your local machine
cd frontend
npm run build
```

Then deploy `frontend/dist/` to Cloudflare Pages:

**Option A: GitHub Integration**
1. Push repo to GitHub
2. Cloudflare Dashboard → Pages → Create Project → Connect Git
3. Build settings:
   - Build command: `npm run build`
   - Build output: `dist`
   - Root directory: `frontend`
4. Environment variables:
   - `VITE_API_URL` = `https://crm.yourdomain.com`

**Option B: CLI**
```bash
npm install -g wrangler
wrangler pages deploy frontend/dist --project-name=lead-intelligence-crm
```

The `frontend/public/_redirects` file handles SPA routing:
```
/* /index.html 200
```

---

## 8. n8n Workflow Setup

1. Open `https://n8n.yourdomain.com`
2. Create admin account
3. Import workflows: Settings → Import from file
   - Import each file from `n8n/workflows/` one at a time
4. Configure credentials in n8n:
   - HTTP Basic Auth for backend webhook calls
   - Set `Authorization: Bearer <admin-jwt>` header
5. Set environment variables in n8n container (via `.env`):
   - `N8N_WEBHOOK_SECRET`
   - `BACKEND_API_URL=http://backend:8000/api/v1`
6. Activate all 9 workflows

---

## 9. Health Check

After deployment, verify:

```bash
# Backend health
curl https://crm.yourdomain.com/api/v1/health/status

# Expected: {"status": "healthy", "timestamp": "..."}
```

Login to `https://crm.yourdomain.com` with admin credentials.

---

## 10. Updating the Application

```bash
cd /opt/lead-intelligence-crm
git pull origin main
cd docker
docker compose up -d --build backend
```

For frontend:
```bash
cd frontend
npm run build
# Re-deploy to Cloudflare Pages
```

---

## Maintenance

### Logs
```bash
docker compose logs backend --tail=100 -f
docker compose logs n8n --tail=100 -f
```

### Database Backup
```bash
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d).sql
```

### Restart Services
```bash
docker compose restart backend
docker compose restart n8n
```
