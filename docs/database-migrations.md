# DHRUVA.AI — Database Migrations Guide

## 1. Migration History & Lineage

The canonical Alembic migration chain spans revisions:
1. `0001_create_core_identity_tables`
2. `0002_create_academic_taxonomy_tables`
3. `0003_create_profile_portfolio_tables`
4. `0004_create_course_delivery_tables`
5. `0005_create_assessment_tables`
6. `0006_create_concept_mastery_tables`
7. `0007_create_skill_career_tables`
8. `0008_create_project_portfolio_tables`
9. `0009_create_institutional_analytics_tables`
10. `0010_create_remediation_tables`
11. `0011_create_system_audit_tables`
12. `0012_create_ai_orchestration_tables`
13. `0013_create_production_operations_tables` (Domain 12 Canonical Extension)

---

## 2. Migration Principles

1. **Never Mutate Schema on Application Boot**:
   FastAPI lifespan handlers MUST NOT run `Base.metadata.create_all()` in production. Schema evolution is exclusively managed via explicit Alembic revisions.
2. **Backward Compatibility**:
   Columns must be added with default values or nullable flags to prevent breaking running application instances during rolling deployments.
3. **Dry-Run Validation**:
   Always inspect generated SQL before applying to production:
   ```bash
   alembic upgrade head --sql
   ```
4. **Pre-Migration Backup Policy**:
   Before running any migration in production, an automated snapshot or `pg_dump` of the PostgreSQL cluster must be captured and verified.

---

## 3. Creating New Migrations

To create a new migration for future domain requirements:
```bash
cd backend
alembic revision --autogenerate -m "describe_schema_change"
```
Always review the generated revision file in `alembic/versions/` for correctness and idempotency before committing to version control.
