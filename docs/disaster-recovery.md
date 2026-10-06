# DHRUVA.AI — Disaster Recovery Plan (DRP)

## 1. Objectives & Metrics

- **RPO (Recovery Point Objective)**: <= 1 Hour (maximum acceptable data loss window).
- **RTO (Recovery Time Objective)**: <= 4 Hours (maximum acceptable downtime window).

---

## 2. Failure Scenarios and Mitigations

### Scenario A: Primary Database Node Corruption or Unavailability
- **Symptom**: `/health/ready` returns `database: down`. HTTP 503 errors across all write endpoints.
- **Immediate Response**:
  1. Trigger failover to read-replica promoted to primary master.
  2. If data corruption occurred, restore from the latest verified point-in-time snapshot.
  3. Re-point `DATABASE_URL` environment variable and perform rolling restart of backend pods.

### Scenario B: Redis Cluster Outage
- **Symptom**: Redis health probe fails.
- **Mitigation Architecture**:
  - The application automatically degrades to in-process memory-backed rate limiting and local task queues.
  - No academic state or canonical student data is lost.
  - Restart Redis container via `docker compose restart redis`.

### Scenario C: Gemini AI Provider Outage or Quota Depletion
- **Symptom**: AI queries return HTTP 503 or quota exceeded.
- **Mitigation Architecture**:
  - The platform **NEVER** fabricates artificial AI answers.
  - Return explicit deterministic status: `{"error": "AI service is temporarily unavailable. Please retry in a few moments."}`
  - Deterministic evaluation, rubrics, exams, and grading proceed unaffected.

### Scenario D: S3 Object Storage Outage
- **Symptom**: Project evidence, resumes, and assignment uploads fail.
- **Mitigation Architecture**:
  - Upload endpoints reject requests cleanly with `STORAGE_UNAVAILABLE` error code.
  - Direct student to retry upload when storage provider resumes normal operation.
  - Switch to secondary backup S3 bucket or local disk fallback if prolonged outage.
