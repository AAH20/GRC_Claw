# Recruitment Platform — Docker Deployment Guide

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│  Frontend   │     │   Backend   │
│  (Reverse   │     │  (Next.js)  │     │  (FastAPI)  │
│   Proxy)    │     └─────────────┘     └──────┬──────┘
└──────┬──────┘                                │
       │                                       ▼
       │                                ┌─────────────┐
       │                                │  PostgreSQL │
       │                                │    (16)     │
       │                                └─────────────┘
       │                                       ▲
       │                                ┌──────┴──────┐
       └───────────────────────────────▶│    Redis    │
                                        │    (7)      │
                                        └─────────────┘
```

## Services

| Service     | Image              | Port  | Description              |
|-------------|--------------------|-------|--------------------------|
| PostgreSQL  | postgres:16-alpine | 5432  | Primary database         |
| Redis       | redis:7-alpine     | 6379  | Cache / session store    |
| Backend     | Custom (FastAPI)   | 8000  | REST API                 |
| Frontend    | Custom (Next.js)   | 3000  | Web UI                   |
| Nginx       | nginx:1.27-alpine  | 80/443| Reverse proxy / SSL      |

## Quick Start

### 1. Prerequisites

- Docker 24.0+
- Docker Compose v2.20+
- OpenSSL (for self-signed certs in development)

### 2. Environment Setup

```bash
cd docker/
cp .env.example .env
# Edit .env with your values
```

### 3. Generate SSL Certificates (Development)

```bash
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/privkey.pem \
  -out certs/fullchain.pem \
  -subj "/CN=localhost"
```

### 4. Build & Start

```bash
# Development
docker compose up --build -d

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

### 5. Verify

```bash
# Check all services are healthy
docker compose ps

# View logs
docker compose logs -f

# Test endpoints
curl http://localhost/health
curl http://localhost/api/health
```

## Production Deployment

### Resource Limits

All services have CPU and memory limits configured. Adjust in `docker-compose.prod.yml` based on your infrastructure.

### Scaling

```bash
# Scale backend replicas
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=3
```

### SSL Certificates

For production, replace the self-signed certificates in `certs/` with certificates from a trusted CA (e.g., Let's Encrypt).

### Backups

```bash
# Database backup
docker exec recruitment-postgres pg_dump -U recruitment_user recruitment > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20240101.sql | docker exec -i recruitment-postgres psql -U recruitment_user -d recruitment
```

## Health Checks

Every service has a health check configured:

- **PostgreSQL**: `pg_isready` every 10s
- **Redis**: `redis-cli ping` every 10s
- **Backend**: HTTP GET `/health` every 30s
- **Frontend**: HTTP GET `/api/health` every 30s
- **Nginx**: HTTP GET `/health` every 30s

## Networking

All services communicate over an isolated bridge network (`app-network`, subnet `172.20.0.0/16`). Only Nginx exposes ports to the host.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Change port mapping in `docker-compose.yml` |
| SSL certificate error | Regenerate certs or check file permissions |
| Database connection failed | Verify `POSTGRES_PASSWORD` matches in `.env` |
| Container keeps restarting | Check logs: `docker compose logs <service>` |

## Stopping

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```
