# DHRUVA.AI — Backups and Disaster Recovery Restore Runbook

## 1. Backup Strategy

DHRUVA.AI implements a tiered backup schedule to ensure maximum data durability and business continuity:

| Data Asset | Backup Mechanism | Frequency | Retention | Storage Location |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL 16 DB** | `pg_dump` compressed / WAL archiving | Hourly incremental, Daily full | 30 days daily, 12 months monthly | Dedicated encrypted S3 bucket (versioned) |
| **S3 Object Storage** | S3 Cross-Region Replication (CRR) | Continuous / Event-driven | Indefinite with lifecycle archival | Secondary Cloud Region |
| **Redis Cache** | RDB / AOF snapshots | Daily | 7 days | Local attached volume |

---

## 2. Automated PostgreSQL Backup Script

The standard backup procedure utilizes `pg_dump` with gzip compression and SHA256 checksum generation:

```bash
#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/var/backups/dhruva"
BACKUP_FILE="${BACKUP_DIR}/dhruva_db_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "Starting database backup at ${TIMESTAMP}..."
pg_dump -U "${POSTGRES_USER}" -h "${POSTGRES_HOST}" -d "${POSTGRES_DB}" --no-owner --clean | gzip -9 > "${BACKUP_FILE}"

# Generate checksum
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"

# Sync to off-site backup vault
aws s3 cp "${BACKUP_FILE}" "s3://${BACKUP_S3_BUCKET}/db-backups/" --sse aws:kms

echo "Backup complete: ${BACKUP_FILE}"
```

---

## 3. Verified Restore Procedure

> **CRITICAL RULE**: A backup that has never been restored into an isolated sandbox environment is considered unverified.

### Step 1: Provision Isolated Restore Target
```bash
docker run -d --name dhruva_restore_test \
  -e POSTGRES_USER=dhruva_admin \
  -e POSTGRES_PASSWORD=restore_secret \
  -e POSTGRES_DB=dhruva_restore_db \
  pgvector/pgvector:pg16
```

### Step 2: Download and Validate Checksum
```bash
aws s3 cp "s3://${BACKUP_S3_BUCKET}/db-backups/dhruva_db_20261006_000000.sql.gz" ./
sha256sum -c "dhruva_db_20261006_000000.sql.gz.sha256"
```

### Step 3: Decompress and Execute Restore
```bash
gunzip -c "dhruva_db_20261006_000000.sql.gz" | \
  docker exec -i dhruva_restore_test psql -U dhruva_admin -d dhruva_restore_db
```

### Step 4: Verification Queries
Verify row count and integrity of core tables:
```sql
SELECT count(*) FROM users;
SELECT count(*) FROM courses;
SELECT count(*) FROM concept_mastery;
```
