# DHRUVA.AI — Production Architecture Specification

## 1. Executive Overview

DHRUVA.AI is an institution-scale higher education platform integrating adaptive learning, career intelligence, project portfolio validation, and supervised AI orchestration.

The platform architecture strictly separates:
- **Deterministic Core**: SQLAlchemy / PostgreSQL 16 models maintaining absolute canonical authority over academic records, mastery states, course progression, assessment rubrics, and accreditation data.
- **Coordination & Acceleration Layer**: Redis distributed locking, token-bucket rate limiting, and in-memory caches.
- **Asynchronous Execution**: In-process and distributed asynchronous job workers and cron schedulers executing bounded, idempotent background tasks.
- **Assisted Intelligence**: Supervised Gemini integration acting as an interactive tutor and copilot with strict output schemas, token budgets, prompt injection defenses, and fallback graceful degradation.
- **Object Storage**: S3-compatible object storage for private, presigned asset management.

---

## 2. High-Level Topology

```
                  +-----------------------------------------+
                  |         Internet / Client Devices       |
                  +--------------------+--------------------+
                                       |
                                       v
                  +-----------------------------------------+
                  |           Cloudflare CDN / WAF          |
                  |   - DDoS Mitigation & TLS Termination   |
                  |   - Security Headers & Edge Caching     |
                  +--------------------+--------------------+
                                       |
            +--------------------------+--------------------------+
            |                                                     |
            v                                                     v
+-----------------------+                             +-----------------------+
| Next.js Frontend Tier |                             | FastAPI Backend Tier  |
| - Node 20 SSR / Static|                             | - ASGI Multi-worker   |
| - Port 3000           |                             | - Port 8000           |
| - Non-root container  |                             | - RBAC & JWT Guard    |
+-----------------------+                             +-----------+-----------+
                                                                  |
                  +-----------------------------------------------+
                  |
        +---------+---------+------------------+------------------+
        |                   |                  |                  |
        v                   v                  v                  v
+---------------+   +---------------+   +--------------+   +--------------+
| Asynchronous  |   | Asia/Kolkata  |   |  PostgreSQL  |   |    Redis     |
| Job Workers   |   | Periodic      |   |  v16 + pgvec |   |  v7 Cluster  |
| - Ingestion   |   | Schedulers    |   | - Master R/W |   | - Rate Limit |
| - Remediation |   | - Retention   |   | - Connection |   | - Distributed|
| - Notifications|  | - Cleanup     |   |   Pools (20) |   |   Locks      |
+---------------+   +---------------+   +--------------+   +--------------+
        |                                       |
        v                                       v
+-------------------------+           +-------------------------+
| S3 Object Storage       |           | Gemini AI Orchestration |
| - MinIO / AWS S3        |           | - Rate-limited          |
| - Presigned URLs        |           | - Audited token budget  |
+-------------------------+           +-------------------------+
```

---

## 3. Network Zones & Security Isolation

1. **Edge Public Zone**:
   - Only Ports 80 / 443 exposed via CDN / Load Balancer.
   - Frontend and Backend reverse proxy endpoints accessible to authorized clients.
2. **Application Tier (`dhruva_edge` network)**:
   - Contains Next.js instances and FastAPI backend pods.
   - No direct database access from the public internet.
3. **Data Tier (`dhruva_internal` isolated network)**:
   - PostgreSQL 16, Redis 7, and internal worker engines.
   - Isolated from direct public routing; accessible only by the Backend and Worker services via mutual credential authentication.

---

## 4. Scalability & Sizing Targets

- **Target Capacity**: 10,000+ active university students per institution tenant.
- **Database Connection Pooling**:
  - `DATABASE_POOL_SIZE`: 20
  - `DATABASE_MAX_OVERFLOW`: 10
  - `DATABASE_POOL_TIMEOUT`: 30 seconds
- **Database Indexing**:
  - B-Tree indexes on all tenant foreign keys (`institution_id`, `department_id`, `user_id`).
  - HNSW index on pgvector embeddings for RAG document retrieval.
- **Stateless Application Tier**:
  - API and Frontend nodes run horizontally scalable containers behind round-robin load balancers.
