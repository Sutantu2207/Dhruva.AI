# DHRUVA.AI — PRODUCTION & STAGING DEPLOYMENT GUIDE
**Institutional-Scale Deployment, Multi-Tier Topology & Release Engineering**

---

## 1. Executive Deployment Architecture

Dhruva.AI utilizes a zero-trust, multi-tier containerized architecture designed for high availability, deterministic reliability, and strict tenant isolation.

```
                                  [ INTERNET ]
                                        │
                         [ TLS 1.3 / HTTPS : Port 443 ]
                                        │
                         ┌──────────────▼──────────────┐
                         │   Nginx Edge Reverse Proxy  │
                         │   - TLS Termination         │
                         │   - Security Headers / HSTS │
                         │   - Distributed Rate Limits │
                         │   - Gzip Compression        │
                         └──────┬──────────────┬───────┘
                                │              │
           ┌────────────────────┘              └────────────────────┐
           │ /_next/*, /*                                           │ /api/*, /health/*
┌──────────▼──────────┐                                  ┌──────────▼──────────┐
│   Frontend Service  │                                  │   Backend Core API  │
│   Next.js 15 SSR    │                                  │   FastAPI / Uvicorn │
│   Port: 3000 (int)  │                                  │   Port: 8000 (int)  │
└─────────────────────┘                                  └──────────┬──────────┘
                                                                    │
                 ┌──────────────────┬───────────────────┬───────────┴───────────┐
                 │                  │                   │                       │
       ┌─────────▼────────┐ ┌───────▼────────┐ ┌────────▼────────┐    ┌─────────▼────────┐
       │   PostgreSQL 16  │ │  Redis 7 Cache │ │  Celery/Worker  │    │  Coding Sandbox  │
       │   + pgvector     │ │  & Lock Server │ │  & Scheduler    │    │  Isolated Runner │
       │   Port: 5432(int)│ │  Port: 6379(int│ │  Internal Async │    │  Port: 8080(int) │
       └──────────────────┘ └────────────────┘ └─────────────────┘    └──────────────────┘
```

### Ingress & Network Isolation Invariants
1. **Public Edge**: Only Nginx publishes external host ports (80 and 443).
2. **Internal Isolated Network**: PostgreSQL, Redis, Worker, Scheduler, and Sandbox are deployed on `dhruva_internal` with **zero external host port bindings**.
3. **Application Security Layer**: The frontend accesses the backend via Docker internal networking (`http://backend:8000/api/v1`) or client-side reverse-proxied paths (`/api/v1`).

---

## 2. Infrastructure Requirements & Pre-Requisites

### Minimum Staging Hardware
- **CPU**: 4 vCPUs (x86_64 or ARM64)
- **RAM**: 8 GB RAM
- **Disk**: 50 GB NVMe SSD (Encrypted at rest)
- **OS**: Ubuntu 22.04 LTS / Debian 12 / RHEL 9

### Recommended Production Hardware (Pilot 1,000–5,000 Students)
- **CPU**: 8–16 vCPUs
- **RAM**: 32 GB RAM
- **Disk**: 200 GB NVMe SSD (PostgreSQL WAL on separate IOPS-provisioned mount)
- **Network**: 1 Gbps+ low-latency interface with redundant uplink
- **External Object Store**: AWS S3 / Cloudflare R2 / MinIO Enterprise

---

## 3. Environment Preparation & Secret Management

### Step 3.1: Generate Cryptographically Secure Secrets
Run on the deployment host:
```bash
# 1. Generate 64-character Application Secret Key
export DHRUVA_SECRET_KEY=$(openssl rand -hex 32)

# 2. Generate Database Administrator Password
export DHRUVA_POSTGRES_PASSWORD=$(openssl rand -hex 24)

# 3. Generate Redis Password
export DHRUVA_REDIS_PASSWORD=$(openssl rand -hex 24)

# 4. Generate Sandbox Runner API Token
export DHRUVA_SANDBOX_TOKEN=$(openssl rand -hex 24)
```

### Step 3.2: Configure `.env` File
Copy `.env.example` to `.env` on the host:
```bash
cp .env.example .env
chmod 600 .env
```
Ensure the following variables are strictly populated:
```ini
ENVIRONMENT=production
APPLICATION_ENV=production
DEBUG=false
SECRET_KEY=<DHRUVA_SECRET_KEY>
COOKIE_SECURE=true
POSTGRES_USER=dhruva_admin
POSTGRES_PASSWORD=<DHRUVA_POSTGRES_PASSWORD>
POSTGRES_DB=dhruva_production
DATABASE_URL=postgresql+asyncpg://dhruva_admin:<DHRUVA_POSTGRES_PASSWORD>@postgres:5432/dhruva_production
REDIS_PASSWORD=<DHRUVA_REDIS_PASSWORD>
REDIS_URL=redis://:<DHRUVA_REDIS_PASSWORD>@redis:6379/0
REDIS_ENABLED=true
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://s3.ap-south-1.amazonaws.com
S3_BUCKET_NAME=dhruva-production-assets
S3_ACCESS_KEY_ID=<YOUR_IAM_ACCESS_KEY>
S3_SECRET_ACCESS_KEY=<YOUR_IAM_SECRET_KEY>
S3_REGION=ap-south-1
SANDBOX_API_URL=http://sandbox:8080
SANDBOX_API_TOKEN=<DHRUVA_SANDBOX_TOKEN>
GEMINI_API_KEY=<YOUR_VERTEX_OR_GEMINI_KEY>
CORS_ORIGINS=["https://app.dhruva.edu.in","https://admin.dhruva.edu.in"]
DOMAIN_NAME=app.dhruva.edu.in
```

---

## 4. Production Database Migration Lifecycle

Production startup must **NEVER** implicitly create schemas via `Base.metadata.create_all()`. Schema versions are strictly controlled through Alembic.

### Safe Migration Sequence (Backup -> Migrate -> Verify -> Boot)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> STEP 1: Taking Pre-Migration Safety Snapshot..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
docker compose -f docker-compose.production.yml exec -T postgres \
  pg_dump -U dhruva_admin -d dhruva_production -Fc > "backups/pre_migration_${TIMESTAMP}.dump"
echo "Backup saved to: backups/pre_migration_${TIMESTAMP}.dump"

echo "==> STEP 2: Running Alembic Migration Dry-Run / Validation..."
docker compose -f docker-compose.production.yml run --rm backend \
  alembic check || echo "Pending migrations detected. Proceeding..."

echo "==> STEP 3: Executing Database Migrations..."
docker compose -f docker-compose.production.yml run --rm backend \
  alembic upgrade head

echo "==> STEP 4: Verifying Migration Integrity..."
docker compose -f docker-compose.production.yml run --rm backend \
  alembic current
echo "Migration successful and verified."
```

### Rollback on Migration Failure
If `alembic upgrade head` aborts:
```bash
echo "CRITICAL: Migration failed. Restoring from pre-migration snapshot..."
docker compose -f docker-compose.production.yml exec -T postgres \
  pg_restore -U dhruva_admin -d dhruva_production --clean --if-exists "backups/pre_migration_${TIMESTAMP}.dump"
```

---

## 5. Container Build & Orchestration

### Step 5.1: Build Production Container Images
```bash
docker compose -f docker-compose.production.yml build --no-cache
```

### Step 5.2: Start Production Cluster with Health Dependencies
```bash
docker compose -f docker-compose.production.yml up -d
```

### Step 5.3: Monitor Cluster Startup
```bash
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs -f proxy backend frontend
```

---

## 6. TLS / HTTPS Certificate Setup

### Automated Let's Encrypt with Certbot
```bash
# Obtain certificate using Webroot challenge
docker run -it --rm --name certbot \
  -v "$(pwd)/deploy/certbot/www:/var/www/certbot" \
  -v "$(pwd)/deploy/certs:/etc/letsencrypt" \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d app.dhruva.edu.in \
  --email admin@dhruva.edu.in --agree-tos --no-eff-email

# Symlink or copy certificates into Nginx cert volume
mkdir -p ./deploy/nginx/certs
cp ./deploy/certs/live/app.dhruva.edu.in/fullchain.pem ./deploy/nginx/certs/fullchain.pem
cp ./deploy/certs/live/app.dhruva.edu.in/privkey.pem ./deploy/nginx/certs/privkey.pem
chmod 600 ./deploy/nginx/certs/privkey.pem

# Reload Nginx
docker compose -f docker-compose.production.yml exec proxy nginx -s reload
```

---

## 7. Post-Deployment Verification & Smoke Probes

Execute the verification probes immediately after deployment:

```bash
# 1. Process Liveness Check (Must return HTTP 200 alive)
curl -fsS https://app.dhruva.edu.in/health/live

# 2. Readiness Check (Must verify database connected)
curl -fsS https://app.dhruva.edu.in/health/ready | jq .

# Expected Output:
# {
#   "status": "healthy" (or "degraded" if external sandbox/AI optional keys are offline),
#   "version": "1.0.0",
#   "environment": "production",
#   "database": { "status": "healthy", "database": "postgresql", "connected": true },
#   "redis": { "status": "healthy", "connected": true },
#   "storage": { "status": "healthy" }
# }

# 3. Security Headers Audit
curl -s -I https://app.dhruva.edu.in/ | grep -E "Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options"
```

---

## 8. Rollback Procedures

If smoke probes fail or high error rates occur post-deployment:

### Immediate Application Rollback:
```bash
# Revert to previous release tag
git checkout tags/v1.0.X-stable
docker compose -f docker-compose.production.yml up -d --build
```

### Full System Disaster Recovery:
See [`docs/disaster-recovery.md`](file:///c:/Users/sutan/OneDrive/Desktop/Dhruva.AI/docs/disaster-recovery.md) for full point-in-time database restoration and state reconstruction.

---

## 9. Cloud Platform Deployment: Railway (Backend) & Vercel (Frontend)

For cloud PaaS deployment decoupling the backend and frontend:

### Railway Backend Deployment:
- **Configuration as Code**: Governed by `railway.json` and `railway.toml` at the repository root.
- **Builder**: Explicitly declared as `builder = "DOCKERFILE"` with `dockerfilePath = "Dockerfile.backend"`.
- **Runtime Port**: Binds dynamically to Railway's `$PORT` environment variable (`0.0.0.0:${PORT:-8000}`).
- **Database**: Automatically adapts Railway's `DATABASE_URL` (`postgresql://` $\rightarrow$ `postgresql+asyncpg://`).
- **Comprehensive Guide**: See [`docs/railway-deployment.md`](file:///c:/Users/sutan/OneDrive/Desktop/Dhruva.AI/docs/railway-deployment.md).

### Vercel Frontend Deployment:
- **Root Directory**: `frontend`
- **Framework Preset**: Next.js
- **Environment Variables**: `NEXT_PUBLIC_API_URL=https://<your-railway-backend>.up.railway.app/api/v1`
