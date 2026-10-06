# DHRUVA.AI — PRODUCTION OPERATIONS RUNBOOK
**Incident Response Playbooks, Triaging Protocols & Root-Cause Remediation**

---

## Index of Operational Incidents

1. [INC-01: API Endpoint Unavailable / 502 Bad Gateway](#inc-01-api-endpoint-unavailable--502-bad-gateway)
2. [INC-02: PostgreSQL Primary Unreachable / 503 Service Unavailable](#inc-02-postgresql-primary-unreachable--503-service-unavailable)
3. [INC-03: Redis Coordination Failure / Degraded Cache](#inc-03-redis-coordination-failure--degraded-cache)
4. [INC-04: Async Worker or Scheduler Process Stopped](#inc-04-async-worker-or-scheduler-process-stopped)
5. [INC-05: High Error Rate Spike (HTTP 5xx > 1%)](#inc-05-high-error-rate-spike-http-5xx--1)
6. [INC-06: High Latency / Slow Assessment Submission (p95 > 2000ms)](#inc-06-high-latency--slow-assessment-submission-p95--2000ms)
7. [INC-07: Authentication Brute-Force / Credential Stuffing Surge](#inc-07-authentication-brute-force--credential-stuffing-surge)
8. [INC-08: S3 / Object Storage Evidence Upload Failure](#inc-08-s3--object-storage-evidence-upload-failure)
9. [INC-09: Gemini AI Provider Outage or Rate Limit Quota Exhaustion](#inc-09-gemini-ai-provider-outage-or-rate-limit-quota-exhaustion)
10. [INC-10: Coding Sandbox Runner Offline (REQUIRES_SANDBOX)](#inc-10-coding-sandbox-runner-offline-requires_sandbox)
11. [INC-11: Database Migration Failure During Deployment](#inc-11-database-migration-failure-during-deployment)

---

### INC-01: API Endpoint Unavailable / 502 Bad Gateway

- **WHAT HAPPENED?**
  Nginx reverse proxy is returning HTTP 502 Bad Gateway to clients. The backend FastAPI Uvicorn process is either crashed, restarting, or unresponsive.
- **WHAT TO CHECK?**
  1. Process status: `docker compose -f docker-compose.production.yml ps backend`
  2. Crash logs: `docker compose -f docker-compose.production.yml logs --tail=100 backend`
  3. Liveness probe: `curl -I http://127.0.0.1:8000/health/live`
  4. Memory limits: `docker stats dhruva_prod_backend` (check for OOMKilled flag).
- **WHAT TO DO?**
  1. If container exited: `docker compose -f docker-compose.production.yml restart backend`
  2. If blocked on file descriptor / resource exhaustion: Restart with increased worker limits.
  3. Inspect recent deployment diffs for unhandled startup exceptions.
- **WHEN TO ROLLBACK?**
  Roll back immediately if container crash-loops repeatedly due to a code regression in the latest release.

---

### INC-02: PostgreSQL Primary Unreachable / 503 Service Unavailable

- **WHAT HAPPENED?**
  `/health/ready` returns `status: unhealthy` with `database: connected: false`. Write operations fail.
- **WHAT TO CHECK?**
  1. Postgres container status: `docker compose -f docker-compose.production.yml ps postgres`
  2. Database logs: `docker compose -f docker-compose.production.yml logs --tail=100 postgres`
  3. Disk space: `df -h` (check if postgres volume is 100% full).
  4. Connection limit: `docker exec dhruva_prod_postgres psql -U dhruva_admin -c "SELECT count(*) FROM pg_stat_activity;"`
- **WHAT TO DO?**
  1. If disk is full: Expand host EBS/NVMe disk volume; clean old archive logs.
  2. If connection pool exhausted: Terminate idle connections:
     `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < current_timestamp - INTERVAL '15 minutes';`
  3. Restart postgres: `docker compose -f docker-compose.production.yml restart postgres`
- **WHEN TO ROLLBACK?**
  Do not roll back code unless a bad migration locked tables or caused transaction deadlock.

---

### INC-03: Redis Coordination Failure / Degraded Cache

- **WHAT HAPPENED?**
  `/health/ready` reports Redis degraded. Distributed rate limiting and background task enqueueing switch to local fallback.
- **WHAT TO CHECK?**
  1. Container status: `docker compose -f docker-compose.production.yml ps redis`
  2. Memory usage: `docker exec dhruva_prod_redis redis-cli -a "$REDIS_PASSWORD" info memory`
  3. Authenticate manually: `docker exec dhruva_prod_redis redis-cli -a "$REDIS_PASSWORD" ping`
- **WHAT TO DO?**
  1. If OOM occurred: Check `maxmemory` policy in `redis.conf` (ensure `volatile-lru` or `allkeys-lru` is set).
  2. Restart Redis: `docker compose -f docker-compose.production.yml restart redis`
  3. Re-verify health: `curl -s http://127.0.0.1:8000/health/ready | jq .redis`
- **WHEN TO ROLLBACK?**
  Never rollback code for transient Redis network drops; academic state is stored in PostgreSQL.

---

### INC-04: Async Worker or Scheduler Process Stopped

- **WHAT HAPPENED?**
  Scheduled analytics recomputation, mastery decay processing, or background email delivery queue is stalled.
- **WHAT TO CHECK?**
  1. Process state: `docker compose -f docker-compose.production.yml ps worker scheduler`
  2. Worker logs: `docker compose -f docker-compose.production.yml logs --tail=100 worker`
  3. Unprocessed jobs in queue: Inspect Redis keys `queue:default` or Celery task backlog.
- **WHAT TO DO?**
  1. Restart worker: `docker compose -f docker-compose.production.yml restart worker scheduler`
  2. If memory leak detected: Tune worker lifecycle to recycle workers after N tasks.
- **WHEN TO ROLLBACK?**
  Roll back if a newly released background task handler consistently raises fatal unhandled exceptions.

---

### INC-05: High Error Rate Spike (HTTP 5xx > 1%)

- **WHAT HAPPENED?**
  Alert triggers due to 5xx rate exceeding 1% over a 5-minute window.
- **WHAT TO CHECK?**
  1. Error class distribution in structured logs:
     `docker compose -f docker-compose.production.yml logs --since 10m backend | grep -i "error"`
  2. Filter by endpoint: Determine whether error is isolated to specific routes (e.g. `/api/v1/assessments/submit`).
- **WHAT TO DO?**
  1. If isolated to a specific third-party integration (e.g. S3 or AI), verify fallback handlers engage.
  2. If widespread due to bad SQL query syntax or broken validation schema, initiate rollback.
- **WHEN TO ROLLBACK?**
  Roll back immediately if error rate persists > 2 minutes following a new deployment.

---

### INC-06: High Latency / Slow Assessment Submission (p95 > 2000ms)

- **WHAT HAPPENED?**
  Assessment submission or analytics endpoint p95 latency spikes above 2 seconds.
- **WHAT TO CHECK?**
  1. PostgreSQL slow queries:
     `SELECT query, total_exec_time, calls FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 5;`
  2. Database locks:
     `SELECT relation::regclass, mode, granted FROM pg_locks WHERE NOT granted;`
  3. CPU utilization: `top` or `htop` on host.
- **WHAT TO DO?**
  1. Kill long-running blocking queries exceeding statement timeout (15000ms default).
  2. Verify missing index on large tables via `EXPLAIN ANALYZE`.
  3. Scale up backend API worker count if CPU saturated.
- **WHEN TO ROLLBACK?**
  Roll back if an unindexed query was introduced in the latest release that causes sequential table scans.

---

### INC-07: Authentication Brute-Force / Credential Stuffing Surge

- **WHAT HAPPENED?**
  Spike in HTTP 401/429 responses from `/api/v1/auth/login`. Potential credential stuffing attack.
- **WHAT TO CHECK?**
  1. Source IPs in Nginx access log:
     `tail -n 1000 /var/log/nginx/access.log | grep "/api/v1/auth/login" | awk '{print $1}' | sort | uniq -c | sort -nr | head -n 10`
  2. Target email patterns in audit logs.
- **WHAT TO DO?**
  1. Block abusive IP CIDR blocks at edge firewall (UFW / AWS Security Group / Cloudflare WAF).
  2. Verify Dhruva account lockout policy engaged (`ACCOUNT_LOCKOUT_MINUTES=15`).
  3. Temporary increase Nginx auth rate limit restriction in `deploy/nginx/conf.d/dhruva.conf`.
- **WHEN TO ROLLBACK?**
  Not applicable. Attack mitigation is an infrastructure firewall action.

---

### INC-08: S3 / Object Storage Evidence Upload Failure

- **WHAT HAPPENED?**
  Student project file uploads, resumes, or certificates return storage errors.
- **WHAT TO CHECK?**
  1. Backend logs: `grep -i "S3 STORAGE" logs/dhruva.log`
  2. AWS S3 IAM credentials expiration or permission policy changes.
  3. S3 bucket CORS and bucket policy.
- **WHAT TO DO?**
  1. If AWS credentials expired: Rotate `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY` in `.env`.
  2. If cloud provider outage: Switch `STORAGE_BACKEND=local` temporarily for offline storage.
- **WHEN TO ROLLBACK?**
  Do not roll back application code.

---

### INC-09: Gemini AI Provider Outage or Rate Limit Quota Exhaustion

- **WHAT HAPPENED?**
  AI Mentor / Copilot endpoints return 503 or "AI service unavailable".
- **WHAT TO CHECK?**
  1. Google Cloud / Vertex API status dashboard.
  2. Health probe: `curl -s http://127.0.0.1:8000/health/ready | jq .ai_provider`
  3. Backend logs for HTTP 429 Quota Exceeded.
- **WHAT TO DO?**
  1. Verify platform honest fallback behavior: academic evaluation, grading, and tests must continue normally.
  2. If quota exceeded: Request quota increase in Google Cloud console or rotate to fallback Gemini API key.
- **WHEN TO ROLLBACK?**
  Do not roll back. AI is assistive only; deterministic truth is intact.

---

### INC-10: Coding Sandbox Runner Offline (REQUIRES_SANDBOX)

- **WHAT HAPPENED?**
  Student code evaluations return `compile_status: unavailable`, `error_message: REQUIRES_SANDBOX`.
- **WHAT TO CHECK?**
  1. Sandbox runner status: `curl -I $SANDBOX_API_URL/health`
  2. Network connectivity between backend and sandbox container.
  3. Health probe: `curl -s http://127.0.0.1:8000/health/ready | jq .sandbox`
- **WHAT TO DO?**
  1. Restart sandbox container: `docker compose -f docker-compose.production.yml restart sandbox`
  2. Submissions submitted during outage are safely stored in database for offline re-evaluation once runner resumes.
- **WHEN TO ROLLBACK?**
  Do not roll back. Never fake code execution.

---

### INC-11: Database Migration Failure During Deployment

- **WHAT HAPPENED?**
  Deployment pipeline fails at `alembic upgrade head`.
- **WHAT TO CHECK?**
  1. Migration error output in deployment log.
  2. Current revision: `docker compose run --rm backend alembic current`
- **WHAT TO DO?**
  1. Restore pre-migration backup snapshot taken before deployment:
     `pg_restore -U dhruva_admin -d dhruva_production --clean pre_migration_backup.dump`
  2. Revert deployment image to previous release tag.
- **WHEN TO ROLLBACK?**
  **MANDATORY ROLLBACK IMMEDIATELY**. Never leave the database in a partially migrated state.
