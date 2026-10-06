# DHRUVA.AI — Operations Runbook

## 1. Application Startup & Restart Procedures

### Full Stack Startup (Production Containers)
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Restarting Specific Services
```bash
# Restart background worker only:
docker compose -f docker-compose.prod.yml restart worker

# Restart periodic scheduler only:
docker compose -f docker-compose.prod.yml restart scheduler

# Restart API gateway only:
docker compose -f docker-compose.prod.yml restart backend
```

---

## 2. Emergency Operational Playbooks

### Playbook A: High Database Connection Pool Usage
1. Inspect connection counts:
   ```sql
   SELECT count(*), state FROM pg_stat_activity GROUP BY state;
   ```
2. Identify idle-in-transaction connections:
   ```sql
   SELECT pid, now() - state_change AS duration, query 
   FROM pg_stat_activity 
   WHERE state = 'idle in transaction' ORDER BY duration DESC;
   ```
3. Terminate runaway connection:
   ```sql
   SELECT pg_terminate_backend(<PID>);
   ```

### Playbook B: Background Job Queue Congestion
1. Inspect dead-letter jobs:
   ```bash
   curl -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/api/v1/admin/operations/jobs
   ```
2. Scale up worker container instances:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --scale worker=3
   ```

### Playbook C: Gemini AI Service Degraded
1. Toggle AI feature flag off if experiencing cascading errors:
   - Update `FEATURE_AI_ASSISTANCE=False` in `backend/.env.production`.
   - Reload backend pods: `docker compose -f docker-compose.prod.yml restart backend`.
2. Confirm deterministic learning operations remain available.
