# DHRUVA.AI — Observability & Telemetry Guide

## 1. Structured Logging

DHRUVA.AI logs structured JSON records to stdout. All logs contain contextual metadata while redacting sensitive fields:

### Log Schema Example
```json
{
  "timestamp": "2026-10-06T19:30:00.123Z",
  "level": "INFO",
  "request_id": "req-9842a-f8e1",
  "environment": "production",
  "method": "POST",
  "route": "/api/v1/assessments/submit",
  "status_code": 200,
  "duration_ms": 48.2,
  "user_id": "usr_912401",
  "institution_id": "inst_001",
  "role": "STUDENT"
}
```

### Sensitive Data Redaction Rules
The logging pipeline automatically scrubs:
- `Authorization` headers and Bearer tokens.
- `Cookie` / `Set-Cookie` headers.
- Plaintext passwords and hashes.
- Database connection URLs containing embedded credentials.
- AI conversation messages containing student PII.

---

## 2. Health & Readiness Probes

The application provides RFC-compliant health probes:
1. `GET /health/live`:
   - Returns 200 OK as long as the process is alive. Used by Kubernetes/Docker liveness checks to trigger pod restarts if the loop locks up.
2. `GET /health/ready`:
   - Inspects PostgreSQL database connectivity, Redis connection, worker loop status, and Gemini AI credentials.
   - Used by load balancers before routing traffic to an instance.
3. `GET /health`:
   - Lightweight status summary for external uptime monitoring services.
