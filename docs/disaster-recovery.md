# DHRUVA.AI — DISASTER RECOVERY & BUSINESS CONTINUITY PLAN
**PostgreSQL 16 Enterprise Strategy, Continuous WAL Archiving & Point-In-Time Restoration**

---

## 1. Objectives & SLA Metrics

| Metric | Target SLA | Definition |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | **≤ 15 Minutes** (with WAL streaming) / **≤ 1 Hour** (snapshot baseline) | Maximum tolerable academic and evaluation data loss window. |
| **RTO (Recovery Time Objective)** | **≤ 60 Minutes** | Maximum allowable downtime from disaster declaration to fully verified student service restoration. |
| **Data Integrity Invariant** | **100% Deterministic** | Evaluation records, mastery states, exam submissions, and student audit trails must be verifiable via cryptographic hashes. |

---

## 2. Backup Topology & Architecture

Dhruva.AI enforces a tiered backup strategy separating relational state, vector embeddings, and object storage assets:

```
[ Primary PostgreSQL 16 ]
       │
       ├── (Every 1 Hour) ──> pg_dump Custom Format (-Fc) ──> AES-256 Encrypted Cold S3 Vault
       │
       └── (Continuous)  ──> WAL Archiving (pg_receivewal) ─> Off-site Secondary Storage (PITR)
```

### Backup Schedule & Retention Policy

| Tier | Frequency | Retention Window | Destination |
| :--- | :--- | :--- | :--- |
| **Hourly Snapshots** | Every 60 minutes | 48 Hours | Encrypted local backup mount + S3 primary |
| **Daily Full Snapshots** | Daily at 02:00 UTC | 30 Days | Geographically isolated cloud bucket (AWS ap-south-1) |
| **Weekly Archives** | Sunday at 03:00 UTC | 90 Days | Immutable Object Lock / WORM S3 Storage |
| **Continuous WAL** | Real-time streaming | 7 Days | Continuous Archive for Point-in-Time Recovery |

---

## 3. Practical Backup Execution

### Automated Snapshot Script (`scripts/backup_database.sh`)
```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/var/backups/dhruva"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="${BACKUP_DIR}/dhruva_db_${TIMESTAMP}.dump"
CHECKSUM_FILE="${FILENAME}.sha256"

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Initiating compressed database backup..."
docker compose -f docker-compose.production.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  -Fc --compress=9 --verbose > "${FILENAME}"

echo "[$(date)] Generating cryptographic SHA-256 checksum..."
sha256sum "${FILENAME}" > "${CHECKSUM_FILE}"

echo "[$(date)] Syncing to off-site encrypted backup vault..."
aws s3 cp "${FILENAME}" "s3://${S3_BACKUP_BUCKET}/db_backups/${TIMESTAMP}/" --sse aws:kms
aws s3 cp "${CHECKSUM_FILE}" "s3://${S3_BACKUP_BUCKET}/db_backups/${TIMESTAMP}/" --sse aws:kms

echo "[$(date)] Purging local snapshots older than 7 days..."
find "${BACKUP_DIR}" -type f -name "*.dump" -mtime +7 -delete
find "${BACKUP_DIR}" -type f -name "*.sha256" -mtime +7 -delete

echo "[$(date)] Backup completed successfully: ${FILENAME}"
```

---

## 4. Disaster Restoration Procedure

### Scenario 1: Primary Database Corruption or Catastrophic Server Loss

#### Step 1: Put System into Maintenance Mode
Block edge traffic at Nginx reverse proxy to prevent inconsistent student submissions during restoration:
```bash
docker compose -f docker-compose.production.yml exec proxy nginx -s stop
```

#### Step 2: Provision Fresh Target Instance
```bash
docker compose -f docker-compose.production.yml up -d postgres
```

#### Step 3: Verify Snapshot Integrity
Verify SHA-256 checksum before restoration:
```bash
sha256sum -c "dhruva_db_20261006_020000.dump.sha256"
# Output must read: OK
```

#### Step 4: Execute Restoration via `pg_restore`
```bash
docker compose -f docker-compose.production.yml exec -T postgres \
  pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  --clean --if-exists --verbose --exit-on-error \
  < "dhruva_db_20261006_020000.dump"
```

#### Step 5: Verify Schema & Migration Head
```bash
docker compose -f docker-compose.production.yml run --rm backend \
  alembic current
# Must verify exact matching head revision with codebase
```

#### Step 6: Run Academic Data Integrity Audit
```bash
docker compose -f docker-compose.production.yml run --rm backend \
  python -c "
import asyncio
from app.core.database import async_session_maker
from sqlalchemy import text

async def check():
    async with async_session_maker() as s:
        res = await s.execute(text('SELECT count(*) FROM users'))
        print(f'Restored Users Count: {res.scalar()}')
asyncio.run(check())
"
```

#### Step 7: Resume Application Services & Ingress
```bash
docker compose -f docker-compose.production.yml up -d backend worker scheduler frontend proxy
```

---

## 5. Non-Database Component Failures

### Redis Cluster Failure
- **Behavior**: Application degrades gracefully to in-memory rate limiting and local task queues.
- **Data Risk**: **ZERO**. Relational records and student grades are never stored exclusively in Redis.
- **Recovery**: `docker compose restart redis`.

### Object Storage Outage (AWS S3)
- **Behavior**: Uploads return HTTP 503 `STORAGE_UNAVAILABLE`. Reads of cached assets continue via CDN edge.
- **Recovery**: Switch DNS CNAME to secondary cross-region replica bucket or fallback storage mount.

### External AI / Gemini Outage
- **Behavior**: Platform returns honest status: `AI Assistant is temporarily unavailable. Academic evaluation is unaffected.`
- **Data Risk**: **ZERO**. Core exams, rubrics, SM-2 calculations, and mastery scoring proceed deterministically.

---

## 6. Disaster Recovery Drill Schedule

To guarantee RPO and RTO SLA adherence, the engineering team executes scheduled drills:
1. **Cadence**: Quarterly (every 90 days).
2. **Procedure**: Spin up an isolated staging replica, restore random weekly production snapshot, run automated test suite against restored database.
3. **Success Criteria**: 100% of test suite passes against restored database with zero manual schema fixes required.
