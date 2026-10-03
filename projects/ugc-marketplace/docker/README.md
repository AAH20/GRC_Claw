# UGC Marketplace — Docker Deployment Guide

## Architecture

```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌──────────┐
│  Nginx  │────▶│Frontend │     │ Backend  │────▶│ Postgres │
│  :443   │     │Next.js  │     │ FastAPI  │     │   :5432  │
│  :80    │     │  :3000  │     │  :8000   │     └──────────┘
└─────────┘     └─────────┘     └────┬─────┘
                                     │
                                ┌────▼─────┐
                                │  Redis   │
                                │  :6379   │
                                └──────────┘
```

## Prerequisites

- Docker Engine 24+
- Docker Compose v2 (`docker compose`, not `docker-compose`)
- OpenSSL (for self-signed certs in development)

## Quick Start (Development)

```bash
cd docker/

# 1. Copy and edit environment variables
cp .env.example .env
# Edit .env — set strong passwords and secret key

# 2. Generate self-signed certificates (dev only)
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/privkey.pem \
  -out certs/fullchain.pem \
  -subj "/CN=localhost"

# 3. Build and start all services
docker compose up -d --build

# 4. Check service health
docker compose ps
docker compose logs -f

# 5. Access the application
#   Frontend: http://localhost
#   API:      http://localhost/api/
```

## Production Deployment

```bash
cd docker/

# 1. Copy and edit environment variables
cp .env.example .env
# Set ENVIRONMENT=production and all secrets

# 2. Obtain real SSL certificates (Let's Encrypt recommended)
#    Place fullchain.pem and privkey.pem in ./certs/

# 3. Start with production overrides
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 4. Verify
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

## Service Details

| Service    | Image              | Port (host) | Health Check          |
|------------|--------------------|-------------|-----------------------|
| PostgreSQL | postgres:16-alpine | 5432        | pg_isready            |
| Redis      | redis:7-alpine      | 6379        | redis-cli ping        |
| Backend    | custom (FastAPI)   | —           | GET /health           |
| Frontend   | custom (Next.js)   | —           | GET /api/health       |
| Nginx      | nginx:1.27-alpine  | 80, 443     | GET /health           |

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable               | Required | Description                          |
|------------------------|----------|--------------------------------------|
| `POSTGRES_PASSWORD`    | Yes      | PostgreSQL password                  |
| `REDIS_PASSWORD`       | Yes      | Redis password                       |
| `SECRET_KEY`           | Yes      | FastAPI secret key (min 32 chars)    |
| `ENVIRONMENT`          | No       | `development` or `production`        |
| `CORS_ORIGINS`         | No       | Allowed CORS origins (comma-separated) |
| `BACKEND_WORKERS`      | No       | Uvicorn worker count (default: 4)    |

## Networking

- **backend** network: PostgreSQL, Redis, Backend (internal communication)
- **frontend** network: Backend, Frontend, Nginx (proxy routing)
- Only Nginx exposes ports to the host (80/443)
- PostgreSQL and Redis are bound to `127.0.0.1` only

## Resource Limits

| Service    | CPU Limit | Memory Limit |
|------------|-----------|--------------|
| PostgreSQL | 1.0       | 512M         |
| Redis      | 0.5       | 256M         |
| Backend    | 1.0       | 512M         |
| Frontend   | 1.0       | 512M         |
| Nginx      | 0.5       | 128M         |

Production overrides double these limits.

## Backup & Restore

```bash
# Backup PostgreSQL
docker exec ugc-postgres pg_dump -U ugc_user ugc_marketplace > backup.sql

# Restore PostgreSQL
cat backup.sql | docker exec -i ugc-postgres psql -U ugc_user ugc_marketplace

# Backup Redis
docker exec ugc-redis redis-cli -a $REDIS_PASSWORD BGSAVE
docker cp ugc-redis:/data/dump.rdb ./dump.rdb
```

## Troubleshooting

```bash
# View logs for all services
docker compose logs -f

# View logs for a specific service
docker compose logs -f backend

# Restart a single service
docker compose restart backend

# Check resource usage
docker stats

# Enter a container for debugging
docker exec -it ugc-backend /bin/sh

# Rebuild after code changes
docker compose up -d --build backend
```

## Security Notes

- All secrets are passed via environment variables, never hardcoded
- PostgreSQL and Redis are not exposed to external networks
- Nginx enforces TLS 1.2+ with strong cipher suites
- Security headers (CSP, X-Frame-Options, etc.) are set by Nginx
- Rate limiting is applied to API and general traffic
- Production containers run with `read_only: true` root filesystem
- Containers use `restart: unless-stopped` for resilience
