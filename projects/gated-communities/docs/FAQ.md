# Frequently Asked Questions

## General

### What is Gated Communities?
Gated Communities is a unified platform for managing gated online communities with membership tiers, content management, moderation, and reputation tracking.

### What technologies does it use?
- Backend: Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL, Redis
- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Infrastructure: Docker, Kubernetes, Terraform

## API

### How do I authenticate?
Use the /api/v1/auth/login endpoint to get an access token. Include the token in the Authorization header for subsequent requests.

### What is the rate limit?
Default rate limit is 100 requests per minute per IP address.

### How do I use webhooks?
1. Create a webhook: POST /api/v1/webhooks
2. Subscribe to events
3. Receive notifications at your endpoint

## Deployment

### How do I deploy to production?
See the Deployment Guide for detailed instructions.

### How do I run migrations?
alembic upgrade head

### How do I backup the database?
See the Backup Documentation for backup procedures.
