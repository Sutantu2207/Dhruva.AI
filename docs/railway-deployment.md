# DHRUVA.AI — RAILWAY BACKEND DEPLOYMENT GUIDE
**Production Configuration, Multi-Stage Dockerfile Deployment & Platform Integration**

---

## 1. Overview & Architecture

Dhruva.AI backend is deployed to [Railway](https://railway.com) as a containerized FastAPI ASGI service.

```
[ Vercel Edge CDN ]                     [ Railway PaaS ]
Frontend (Next.js 15)                   Backend (FastAPI)
         │                                      │
         │ HTTPS API Requests                   │ (Internal Private Network)
         └──────────────────────────────> ┌─────▼─────────────────────────┐
                                          │ Dockerfile.backend Container  │
                                          │ - Binds to dynamic $PORT      │
                                          │ - Non-root dhruva (UID 10001) │
                                          │ - Healthcheck /health/live    │
                                          └─────┬───────────────────┬─────┘
                                                │                   │
                                                ▼                   ▼
                                      [ Railway Postgres ]   [ Railway Redis ]
                                      PostgreSQL 16+pgvector  Redis 7 Cache
```

---

## 2. Root Cause of "Railpack failed to prepare the build"

When connecting a monorepo to Railway without configuration:
1. Railway looks for a default `Dockerfile` at the root.
2. If `Dockerfile` is absent (our backend Dockerfile is named `Dockerfile.backend`), Railway falls back to its heuristic buildpack engine ("Railpack" / Nixpacks).
3. Railpack searches the root folder for language manifests (`requirements.txt`, `package.json`, `go.mod`, etc.).
4. In Dhruva.AI, `requirements.txt` is inside `backend/` and `package.json` is inside `frontend/`.
5. Finding no manifest at root, Railpack halts with:
   ```
   Railpack failed to prepare the build
   ```

### The Solution: Repository-Level Config as Code
By adding `railway.json` and `railway.toml` at the repository root:
```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.backend"
  },
  "deploy": {
    "healthcheckPath": "/health/live",
    "healthcheckTimeout": 120,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```
Railway immediately bypasses Railpack, detects the multi-stage `Dockerfile.backend`, and builds the container from the repository root context.

---

## 3. Container Runtime & Networking Hardening

### 3.1 Dynamic `$PORT` Binding
Railway assigns a dynamic port (e.g., `PORT=6543`) to each container instance.
`Dockerfile.backend` binds dynamically via shell `exec`:
```dockerfile
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --proxy-headers --forwarded-allow-ips '*'"]
```
- **0.0.0.0 Binding**: Accessible to Railway's edge reverse proxy.
- **Single Process Default (`--workers 1`)**: Ensures unified in-process background worker queue and scheduler lifecycle without process bifurcation.
- **Signal Handling (`exec`)**: Replaces the shell process with Python, ensuring `uvicorn` receives OS signals (`SIGTERM`/`SIGINT`) for graceful shutdown.
- **Dynamic Healthcheck**: Probes `http://127.0.0.1:${PORT:-8000}/health/live`.

### 3.2 Automated Cloud `DATABASE_URL` Adaptation
Railway PostgreSQL injects connection strings in the format:
```
postgresql://postgres:password@roundhouse.proxy.rlwy.net:12345/railway
```
In `backend/app/core/config.py`, the validator `assemble_database_url` automatically adapts `postgresql://` and `postgres://` to `postgresql+asyncpg://` so that SQLAlchemy 2.0 async engine connects without manual URL editing.

---

## 4. Required Railway Environment Variables

In your Railway service settings (**Variables** tab), configure:

| Variable | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `APPLICATION_ENV` | `production` | Enables production security policies |
| `ENVIRONMENT` | `production` | Enforces production mode across all domains |
| `SECRET_KEY` | `$(openssl rand -hex 32)` | 64-char unpredictable HMAC key |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Reference to Railway PostgreSQL |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Reference to Railway Redis (Optional) |
| `REDIS_ENABLED` | `true` (if Redis added) or `false` | Distributed caching toggle |
| `COOKIE_SECURE` | `true` | Enforces HTTPS-only cookie transmission |
| `CORS_ORIGINS` | `["https://your-frontend.vercel.app"]` | Allowed frontend origins (no wildcards) |
| `GEMINI_API_KEY` | `<your-gemini-key>` | Optional Google Gemini key |

---

---

## 5. Database Migration Execution & Transaction Persistence Lifecycle

### 5.1 SQLAlchemy 2.0 Async Migration Invariants
In SQLAlchemy 2.0 with asyncpg, DDL on PostgreSQL is transactional. Alembic manages transaction demarcation via `context.begin_transaction()`.
- **Clean Connection Before Configure**: `context.configure(connection=connection, target_metadata=target_metadata)` **must** be called before any statements execute on `connection`. Executing queries prior to `context.configure()` triggers SQLAlchemy autobegin, causing Alembic to detect `_in_external_transaction = True` and render `context.begin_transaction()` a no-op (`nullcontext`). This results in uncommitted migrations that get rolled back upon connection close.
- **Transactional DDL Execution**: All DDL and version maintenance statements execute inside `with context.begin_transaction():` and commit on exit.
- **Defense in Depth**: Explicit commit safeguards (`if connection.in_transaction(): connection.commit()`) prevent uncommitted transaction leaks.

### 5.2 Executing Migrations on Railway
Execute migrations against Railway PostgreSQL using either Railway CLI or the Railway Web Console:

```bash
# Option A: Via Railway CLI
railway run alembic upgrade head

# Option B: Inside Railway Web Shell / Deployment Console
alembic upgrade head
```

### 5.3 Verification of Persisted State
Immediately after running `alembic upgrade head`, verify migration persistence:

```bash
# 1. Verify Alembic reports head revision:
alembic current -v
# Output MUST show:
# Current revision(s) for postgresql+asyncpg://...
# 0013_create_production_operations_tables (head)

# 2. Inspect Database Health Probe via CLI or HTTP:
curl -fsS https://<your-service>.up.railway.app/health/ready
```

Expected readiness output:
```json
{
  "status": "healthy",
  "database": {
    "status": "healthy",
    "database": "postgresql",
    "connected": true,
    "has_institutions": true,
    "has_user_sessions": true,
    "alembic_version": "0013_create_production_operations_tables",
    "public_tables_count": 137
  }
}
```

---

## 6. Post-Deployment Verification

Once deployed on Railway, test the public URLs:
```bash
# 1. Verify Process Liveness
curl -fsS https://<your-service>.up.railway.app/health/live
# Expected: {"status": "alive", "timestamp": "..."}

# 2. Verify Readiness & Database Connectivity
curl -fsS https://<your-service>.up.railway.app/health/ready
# Expected: {"status": "healthy", ... "has_institutions": true, "has_user_sessions": true}
```
