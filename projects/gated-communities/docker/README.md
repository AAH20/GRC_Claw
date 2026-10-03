# Gated Communities — Docker Compose Stack

Production-grade Docker Compose stack for the Gated Communities platform.

## Architecture

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│  Nginx  │────▶│ Frontend│────▶│ Backend  │
│  :80    │     │  :3000  │     │  :8000   │
└─────────┘     └─────────┘     └────┬─────┘
                                     │
                              ┌──────┴──────┐
                              │             │
                         ┌────▼───┐   ┌────▼───┐
                         │Postgres│   │ Redis  │
                         │  :5432 │   │  :6379 │
                         └────────┘   └────────┘
```

## Services

| Service    | Image              | Port | Description          |
|------------|--------------------|------|----------------------|
| PostgreSQL | postgres:16-alpine  | 5432 | Primary database     |
| Redis      | redis:7-alpine      | 6379 | Cache / sessions     |
| Backend    | FastAPI (custom)   | 8000 | REST API             |
| Frontend   | Next.js (custom)   | 3000 | Web UI               |
| Nginx      | nginx:1.27-alpine  | 80   | Reverse proxy        |

## Prerequisites

- Docker Engine 24+
- Docker Compose v2+
- `curl` (for health checks)

## Quick Start

```bash
cd docker/

# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your secrets

# 2. Create required directories
mkdir -p certs

# 3. Build and start
docker compose up -d --build

# 4. Check status
docker compose ps

# 5. View logs
docker compose logs -f
```

## Production Deployment

```bash
# Use production overrides
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Or set COMPOSE_PROJECT_NAME
export COMPOSE_PROJECT_NAME=gated-communities
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Production Checklist

- [ ] Change all default passwords in `.env`
- [ ] Generate strong `SECRET_KEY` and `JWT_SECRET`
- [ ] Place TLS certificates in `./certs/`
- [ ] Uncomment HTTPS server block in `nginx.conf`
- [ ] Set `CORS_ORIGINS` to your domain
- [ ] Set `LOG_LEVEL=warning`
- [ ] Configure `BACKEND_WORKERS` based on CPU cores
- [ ] Set up log rotation (handled by prod overrides)
- [ ] Enable Docker content trust

## Environment Variables

| Variable               | Default                  | Description                |
|------------------------|--------------------------|----------------------------|
| `POSTGRES_DB`          | `gated_communities`      | Database name              |
| `POSTGRES_USER`        | `gc_user`                | Database user              |
| `POSTGRES_PASSWORD`    | *(required)*             | Database password          |
| `REDIS_PASSWORD`       | *(required)*             | Redis password             |
| `SECRET_KEY`           | *(required)*             | App secret key             |
| `JWT_SECRET`           | *(required)*             | JWT signing secret         |
| `CORS_ORIGINS`         | `http://localhost:3000`  | Allowed CORS origins       |
| `LOG_LEVEL`            | `info`                   | Logging level              |
| `BACKEND_WORKERS`      | `4`                      | Uvicorn worker count       |
| `NEXT_PUBLIC_API_URL` | `http://localhost/api`   | Public API URL             |
| `NGINX_PORT`           | `80`                     | HTTP port                  |
| `NGINX_HTTPS_PORT`     | `443`                    | HTTPS port                 |

## Networking

- **`gc-frontend`** — External-facing network (Nginx ↔ Frontend)
- **`gc-backend`** — Internal-only network (Backend ↔ PostgreSQL/Redis)

PostgreSQL and Redis are not exposed to the host. All traffic flows through Nginx.

## Volumes

| Volume         | Purpose                    |
|----------------|----------------------------|
| `postgres_data` | PostgreSQL data directory |
| `redis_data`    | Redis AOF persistence     |

## Health Checks

All services define health checks:

- **PostgreSQL** — `pg_isready`
- **Redis** — `redis-cli ping`
- **Backend** — `GET /health`
- **Frontend** — `GET /api/health`
- **Nginx** — `GET /healthz`

Services with `depends_on` wait for healthy status before starting.

## Resource Limits

| Service    | CPU Limit | Memory Limit |
|------------|-----------|--------------|
| PostgreSQL | 1.0       | 512M         |
| Redis      | 0.5       | 256M         |
| Backend    | 1.0       | 512M         |
| Frontend   | 1.0       | 512M         |
| Nginx      | 0.25      | 128M         |

## Useful Commands

```bash
# View logs
docker compose logs -f [service]

# Restart a service
docker compose restart backend

# Run migrations
docker compose exec backend alembic upgrade head

# Database shell
docker compose exec postgres psql -U gc_user -d gated_communities

# Redis CLI
docker compose exec redis redis-cli -a $REDIS_PASSWORD

# Stop everything
docker compose down

# Stop and remove volumes (WARNING: data loss)
docker compose down -v

# Rebuild a specific service
docker compose up -d --build backend
```

## Troubleshooting

### Services won't start
```bash
docker compose logs
docker compose config  # Validate config
```

### Port conflicts
Edit `.env` to change `NGINX_PORT` and `NGINX_HTTPS_PORT`.

### Health check failures
```bash
docker compose ps
docker compose exec backend curl -f http://localhost:8000/health
```

### Reset everything
```bash
docker compose down -v
docker compose up -d --build
```
