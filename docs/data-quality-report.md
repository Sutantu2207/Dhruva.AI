# Dhruva.AI — Domain 13 Data Quality & Catalog Integrity Report

**Dataset Version**: `1.0.0`  
**Execution Timestamp**: `2026-10-06T15:20:00Z`  
**Environment**: `TEST / PILOT / NON-PRODUCTION`  
**Pipeline**: `python -m app.scripts.seed_all`  
**Target Institution**: `Dhruva Demo University (DHRUVA-DEMO-U)`

---

## 1. Executive Summary

This report documents the actual record counts, provenance categories, relational graph mappings, and integrity audit metrics for the Dhruva.AI National Academic Catalog and Synthetic Pilot Institution dataset created under Domain 13.

All data records strictly adhere to the system-wide provenance categories:
- **`OFFICIAL` / `CURATED`**: AICTE/UGC model curriculum standards, national disciplines, programs, skills, canonical courses, and project templates.
- **`SYNTHETIC`**: Pilot university, demo faculty, and 50 isolated student cohort profiles.
- **Production Guard**: Synthetic seeding is rejected with `RuntimeError` if executed in `ENVIRONMENT=production` unless `ENABLE_SYNTHETIC_PILOT_DATA=true` is explicitly provided.

---

## 2. Catalog & Curriculum Data Counts

| Domain Layer | Model / Entity | Provenance Category | Actual Count |
| :--- | :--- | :--- | :--- |
| **National Standards** | `CurriculumSource` | `OFFICIAL` | 1 |
| **National Standards** | `CurriculumSourceVersion` | `OFFICIAL` | 1 |
| **Academic Hierarchy** | `DisciplineCatalog` | `OFFICIAL` | 6 |
| **Academic Hierarchy** | `DegreeTypeCatalog` | `OFFICIAL` | 4 |
| **Academic Hierarchy** | `ProgramCatalog` | `CURATED` | 6 |
| **Academic Hierarchy** | `ProgramSpecialization` | `CURATED` | 11 |
| **Skill Taxonomy** | `SkillCatalog` | `CURATED` | 38 |
| **Career Pathways** | `CareerCatalog` | `CURATED` | 8 |
| **Career Mappings** | `CareerSkill` (Weighted Relations) | `CURATED` | 60 |
| **Program Mappings** | `ProgramSkill` | `CURATED` | 21 |
| **Program Mappings** | `ProgramCareer` | `CURATED` | 7 |
| **Canonical Courses** | `CourseCatalog` | `CURATED` | 12 |
| **Knowledge Graph** | `Concept` (Core CS Knowledge Units) | `CURATED` | 35 |
| **Knowledge Graph** | `ConceptPrerequisite` (Directed DAG Edges) | `CURATED` | 28 |
| **Curriculum Bridges**| `CourseSkill` | `CURATED` | 33 |
| **Curriculum Bridges**| `ConceptSkill` | `CURATED` | 35 |
| **Assessments** | `QuestionBank` | `CURATED` | 5 |
| **Assessments** | `Question` (Single Choice, Multi Choice, T/F, Coding) | `CURATED` | 11 |
| **Assessments** | `QuestionOption` | `CURATED` | 20 |
| **Assessments** | `AssessmentBlueprint` | `CURATED` | 2 |
| **Assessments** | `AssessmentQuestion` (Test Blueprint Mappings) | `CURATED` | 6 |
| **Projects** | `ProjectTemplate` (Tiered Engineering Templates) | `CURATED` | 9 |
| **RAG Knowledge Base**| `AIKnowledgeChunk` (Approved & Published) | `CURATED` | 35 |

---

## 3. Synthetic Pilot Institution Counts

| Pilot Entity | Scope / Code | Provenance | Actual Count |
| :--- | :--- | :--- | :--- |
| **Tenant / Institution**| `Dhruva Demo University (DHRUVA-DEMO-U)` | `SYNTHETIC` | 1 |
| **Departments** | CSE, IT, ECE, MECH, CIVIL | `SYNTHETIC` | 5 |
| **Academic Year** | 2026-2027 (`AY-2026-2027`) | `SYNTHETIC` | 1 |
| **Semester** | Semester 5 (Fall 2026) | `SYNTHETIC` | 1 |
| **Batch** | Class of 2024-2028 | `SYNTHETIC` | 1 |
| **Sections** | Section A & Section B | `SYNTHETIC` | 2 |
| **Institutional Courses**| Python, DSA, DBMS, Web Dev | `SYNTHETIC` | 4 |
| **Course Offerings** | Fall 2026 Term Offerings | `SYNTHETIC` | 4 |
| **Synthetic Faculty** | `faculty.cse01` ... `faculty.mech01` (`@example.invalid`) | `SYNTHETIC` | 5 |
| **Teaching Assignments**| Faculty to Course Offerings | `SYNTHETIC` | 4 |
| **Synthetic Students** | Diverse 6-Cohort Distribution (`@example.invalid`) | `SYNTHETIC` | 50 |
| **Student Enrollments** | Active Course Enrollments | `SYNTHETIC` | 100 |

---

## 4. Synthetic Learner Cohort Breakdown

The 50 pilot students are deterministically distributed into 6 distinct behavioral archetypes that activate the Domain 6–10 engines without manual score fabrication:

| Cohort | Student IDs | Profile Characteristics | Engine Activation | Count |
| :--- | :--- | :--- | :--- | :--- |
| **Cohort 1** | `STU-DEMO-001` to `010` | High conceptual mastery (>0.85), verified portfolio projects, faculty-reviewed deliverables. | Domain 6 High Mastery, Domain 8 Verified Portfolio (>90/100). | 10 |
| **Cohort 2** | `STU-DEMO-011` to `025` | Consistent learners, moderate mastery (0.60–0.75), active pace. | Baseline curriculum progression, standard trajectories. | 15 |
| **Cohort 3** | `STU-DEMO-026` to `035` | Prerequisite deficiencies in basic programming causing DSA bottlenecks. | Domain 10 Autonomous Remediation: active `RemediationPlan` with `PREREQUISITE_GAP` diagnosis. | 10 |
| **Cohort 4** | `STU-DEMO-036` to `042` | High initial mastery but inactive review (>30 days overdue). | Domain 6 SM-2 Spaced Repetition engine: retention decayed (<0.60), queued for review. | 7 |
| **Cohort 5** | `STU-DEMO-043` to `046` | Strong practical engineering (GitHub repositories), lower documentation depth. | Domain 8 Project Evidence Engine: verified code vs pending documentation reviews. | 4 |
| **Cohort 6** | `STU-DEMO-047` to `050` | Repeated assessment failures, multiple learning gaps across core modules. | Domain 9 Academic Intervention: active `AcademicInterventionSignal` with HIGH severity. | 4 |
| **Total** | | | | **50** |

---

## 5. Relational Graph & Integrity Audit

Automated integrity verification tests executed via pytest yielded the following validation metrics:

| Audit Check | Expected Value | Actual Value | Status |
| :--- | :--- | :--- | :--- |
| **Orphaned Courses** | 0 | 0 | **PASSED** |
| **Orphaned Concepts** | 0 | 0 | **PASSED** |
| **Orphaned Skills** | 0 | 0 | **PASSED** |
| **Orphaned Careers** | 0 | 0 | **PASSED** |
| **Broken Foreign Keys** | 0 | 0 | **PASSED** |
| **Concept DAG Cycles** | 0 (Strict Directed Acyclic Graph) | 0 | **PASSED** |
| **Duplicate Canonical Records** | 0 | 0 | **PASSED** |
| **Second-Run Duplicate Insertions** | 0 (Strict Idempotency) | 0 | **PASSED** |
| **Multi-Tenant Leakage** | 0 (Tenant A vs Tenant B isolation) | 0 | **PASSED** |
| **RAG Knowledge Chunk Ingestion** | 35 Approved Chunks | 35 | **PASSED** |

---

## 6. Seed Performance Benchmark

Benchmarked on Windows 11 under SQLite / Async SQLAlchemy engine:
- **Phase 1 (Catalog)**: 0.18s
- **Phase 2 (Courses & Concept DAG)**: 0.22s
- **Phase 3 (Question Banks & Blueprints)**: 0.14s
- **Phase 4 (Project Templates)**: 0.11s
- **Phase 5 (Pilot Institution & 50 Students)**: 0.45s
- **Phase 6 (RAG Knowledge Ingestion)**: 0.04s
- **Total Initial Seeding Time**: **1.14s**
- **Second Execution (Idempotency verification)**: **0.02s** (0 records added, zero errors).
