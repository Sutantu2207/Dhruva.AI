# DHRUVA.AI — Staging Environment Architecture & Operations

## 1. Purpose of Staging

The Staging environment is an exact mirror of Production infrastructure designed to:
- Test zero-downtime database migrations against non-critical sanitized data.
- Validate asynchronous worker workloads (RAG indexing, remediation cascades) under realistic loads.
- Verify third-party integrations (Gemini API quotas, S3 file uploads, SMTP notification delivery).
- Run full automated regression and integration test suites prior to production tagging.

---

## 2. Configuration & Isolation

- **Domain**: `staging.dhruva.ai`
- **Database**: Separate staging PostgreSQL 16 instance. Never connect Staging to Production database.
- **Data Policy**: Staging contains synthetic institution datasets and sanitized benchmarks. No real PII or real student assessment records are stored in Staging.
- **Environment Flag**: `APPLICATION_ENV=staging`
- **Secrets**: Sourced from GitHub Actions Staging Environment Secrets.

---

## 3. Staging Deployment Workflow

Staging deployments occur automatically upon push to the `main` branch via `.github/workflows/deploy.yml`:
1. CI pipeline completes quality gate checks (Lint, Bandit, Pytest, Next.js build).
2. Staging pre-migration executes: `alembic upgrade head`.
3. Staging containers update with newly built images.
4. Smoke tests probe `/health/ready` and operational dashboards.
5. Notification alerts post status to the DevOps channel.
