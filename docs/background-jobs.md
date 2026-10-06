# DHRUVA.AI — Background Job Processing Architecture

## 1. Architecture Overview

Heavy operations must never block the client-facing HTTP request/response cycle.
The background job processing system (`app.core.worker`) executes bounded, asynchronous tasks with:
- **Idempotency**: Prevents repeated execution of the same job key.
- **Exponential Backoff**: Transient errors automatically retry with progressive delays.
- **Dead-Letter Accounting**: Exhausted jobs are recorded with failure exceptions for administrative review.
- **Observable Lifecycle**: States include `QUEUED`, `RUNNING`, `COMPLETED`, and `FAILED`.

---

## 2. Standard Background Tasks

1. **RAG Document Indexing**:
   - Ingests uploaded syllabi and course resources, splits text into semantic chunks, and creates vector embeddings.
2. **Deterministic Remediation Signal Scans**:
   - Scans assessment records to identify concept deficiencies and generate adaptive learning paths.
3. **Mastery Recalculation & Spaced Repetition Updates**:
   - Evaluates SM-2 memory retention schedules and updates student knowledge states.
4. **Institutional Analytics Snapshots**:
   - Computes daily department, course, and section aggregate performance metrics.
5. **Notification & Email Dispatch**:
   - Fanout delivery of reminders, deadlines, and intervention alerts.

---

## 3. Administrative Job Inspection API

Administrators can inspect queue status and history via:
- `GET /api/v1/admin/operations/jobs?limit=50`: Returns recent job executions and status.
- `GET /api/v1/admin/operations/overview`: Returns worker throughput and dead-letter count.
