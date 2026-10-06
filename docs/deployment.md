# DHRUVA.AI — Deployment Guide

## 1. Prerequisites

Before deploying DHRUVA.AI to production, ensure the target host environment meets the following specifications:
- **Operating System**: Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9 recommended).
- **Compute**: Minimum 4 vCPU, 16 GB RAM (Production baseline).
- **Storage**: Minimum 100 GB SSD (NVMe preferred) for database and local cache.
- **Runtimes**: Docker 26+, Docker Compose v2.27+, Python 3.12, Node.js 20 LTS.
- **External Dependencies**:
  - PostgreSQL 16 with `pgvector` extension enabled.
  - Redis 7.0+ with password authentication.
  - S3-compatible bucket (AWS S3, Cloudflare R2, MinIO).
  - Gemini API Key with Tier 2+ quotas.

---

## 2. Configuration Setup

Copy the production configuration template and supply verified credentials:

```bash
cd backend
cp .env.production.example .env.production
chmod 600 .env.production
```

Ensure all mandatory production variables are populated:
- `SECRET_KEY`: Minimum 32-character high-entropy cryptographic secret.
- `DATABASE_URL`: `postgresql+psycopg://<USER>:<PASSWORD>@<HOST>:5432/<DB>`
- `REDIS_URL`: `redis://:<PASSWORD>@<HOST>:6379/0`
- `STORAGE_BACKEND`: `s3`
- `S3_BUCKET_NAME`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`
- `GEMINI_API_KEY`: Real Google AI Studio or Vertex AI Gemini API key.

---

## 3. Deployment Procedure

### Step 1: Database Migration
Always run database migrations prior to starting application pods:

```bash
cd backend
# Dry run verification:
alembic upgrade head --sql > pre_deploy.sql
# Execute migration:
alembic upgrade head
```

### Step 2: Container Topology Deployment
Using Docker Compose:

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Step 3: Deployment Verification
Verify running container status and health endpoints:

```bash
# Check containers:
docker compose -f docker-compose.prod.yml ps

# Live probe (verifies process is running):
curl -f http://localhost:8000/health/live

# Ready probe (verifies DB, Redis, and workers are healthy):
curl -f http://localhost:8000/health/ready

# Frontend probe:
curl -f http://localhost:3000/status
```

---

## 4. Rollback Procedure

If any health check fails during deployment:
1. Revert to the prior container image tag:
   ```bash
   docker compose -f docker-compose.prod.yml down
   docker compose -f docker-compose.prod.yml up -d <PREVIOUS_IMAGE_TAG>
   ```
2. If database schema was modified and downgrade is required:
   ```bash
   cd backend
   alembic downgrade -1
   ```
3. Verify recovery via `/health/ready`.
