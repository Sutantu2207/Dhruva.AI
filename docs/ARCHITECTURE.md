# Dhruva.AI Architecture & System Blueprint

Dhruva.AI is an AI-powered career intelligence, adaptive learning, course delivery, student development, and institutional education platform for engineering students.

## 1. Core Architectural Principle: Deterministic-First Hybrid Architecture

The critical architectural foundation of Dhruva.AI is that **deterministic application logic remains the single source of truth** for all business rules, evaluations, rankings, and credentials. 

The Large Language Model (LLM) is strictly an auxiliary layer for contextual synthesis, explanations, and conversational tutoring—**never the source of truth**.

### Ground Truth Separation Matrix

| Domain Capability | Source of Truth Engine | Role of AI / LLM (Auxiliary) |
|---|---|---|
| **Assessment Scoring** | Deterministic engine (exact rubrics, sub-skill weights) | Natural-language explanation of errors and solutions |
| **Concept Mastery** | Deterministic accumulation & decay models | Suggesting practice problems aligned to identified weak nodes |
| **Spaced Repetition** | SuperMemo SM-2 algorithm (deterministic intervals, EF) | Formatting flashcards and mnemonic explanations |
| **Career Recommendation** | Deterministic multi-dimensional skill gap matching | Explaining career pathways and industry context |
| **Student Readiness & Scores** | Verified course completions, code test results, projects | Summarizing portfolio highlights for resumes |
| **Role Authorization (RBAC)** | Deterministic policy evaluation & scoped JWT claims | *Zero access / strictly prohibited* |
| **Audit & Compliance** | Immutable transactional database records | *Zero access / strictly prohibited* |

---

## 2. Privacy & Context Isolation Guardrails

Student identity and privacy must be preserved across all AI invocations:
1. **Authenticated Scope Prior to AI Context**: The backend resolves authenticated student records internally.
2. **PII Sanitization**: Before passing any context to the AI orchestration layer, Personally Identifiable Information (name, email, roll number, registration ID, contact details) is stripped or replaced with anonymized session tokens.
3. **No Unbounded Memory**: Prompts are dynamically assembled per-request from validated domain state.
4. **Audit Trail**: Every AI request and response is tracked with token consumption and latency metrics in the audit domain.

---

## 3. Technology Stack

- **Frontend**: Next.js 15+ (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide Icons.
- **Backend**: FastAPI, Python 3.14, Pydantic v2, Pydantic-Settings, Uvicorn.
- **Database**: PostgreSQL 16 with `pgvector` for vector similarity and RAG search.
- **ORM & Migrations**: SQLAlchemy 2.0 (asyncpg) + Alembic.
- **Authentication**: JWT with asymmetric/symmetric signing, bcrypt password hashing.
- **AI Orchestration**: Google Gemini via controlled, scoped API layer.
- **Testing**:
  - Backend: `pytest`, `pytest-asyncio`, `httpx`
  - Frontend: `eslint`, TypeScript strict checks, Next.js build validation

---

## 4. Modular Domain Boundaries

Dhruva.AI is organized into decoupled domains located in `backend/app/domains/` and mapped cleanly to the frontend:

1. **Identity & Authentication**: User accounts, credentials, RBAC (Student, Teacher, Mentor, HOD, Placement Officer, Institution Admin, Super Admin).
2. **Academic Management**: Institutions, departments, academic years, semesters, batches, sections.
3. **Student Management**: Profiles, academic enrollments, mentor assignments.
4. **Teacher Management**: Faculty profiles, assigned courses, section rosters.
5. **Mentor Management**: Mentorship cohorts, student check-ins, intervention alerts.
6. **Institution Management**: Campus policies, institutional grading rubrics, department hierarchies.
7. **Career Intelligence**: Career target profiles, deterministic skill-gap calculations, fit indexes.
8. **Assessment**: Deterministic rubric evaluation, automated coding tests, submission verification.
9. **Courses & Learning**: Curricula, modules, lessons, prerequisites, interactive practice.
10. **Mastery & Spaced Repetition**: Concept graph mastery values, SM-2 retention scheduler.
11. **Projects & Portfolio**: Verified repository artifacts, capstone evaluation, portfolio evidence.
12. **AI Orchestration & Retrieval**: Scoped Gemini prompts, privacy sanitizer, pgvector vector retrieval.
13. **Analytics & Reporting**: Faculty analytics, institutional accreditation metrics, student progress.
14. **Audit & Administration**: Immutable system audit logs, platform security events.

---

## 5. Directory Structure

```text
Dhruva.AI/
├── backend/
│   ├── app/
│   │   ├── core/                  # Configuration, DB connection, security, logging
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── domains/               # Modular domain engines & business logic
│   │   │   ├── identity/          # Auth, roles, user accounts
│   │   │   ├── assessment/        # Deterministic scoring engine
│   │   │   ├── mastery/           # Concept mastery & SM-2 scheduler
│   │   │   ├── career_intelligence/ # Deterministic skill-gap & recommendation
│   │   │   ├── ai_orchestration/  # Gemini client, PII scrubber, context scoping
│   │   │   └── audit/             # System audit trail
│   │   ├── api/
│   │   │   ├── deps.py            # FastAPI dependency injection (DB, Auth, RBAC)
│   │   │   └── v1/
│   │   │       ├── router.py      # Root API v1 router
│   │   │       └── endpoints/     # HTTP routes (health, system, auth)
│   │   └── main.py                # Application factory & middleware
│   ├── tests/                     # Unit and integration test suite
│   ├── requirements.txt           # Production dependencies
│   ├── pyproject.toml             # Python project configuration
│   └── .env.example               # Backend environment variable template
├── frontend/
│   ├── src/
│   │   ├── app/                   # Next.js App Router (pages & layouts)
│   │   ├── components/
│   │   │   ├── ui/                # Accessible design system primitives (buttons, cards, badges)
│   │   │   └── layout/            # Navigation, shell, status indicators
│   │   └── lib/                   # API client, types, utility helpers
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example               # Frontend environment variable template
├── docs/
│   └── ARCHITECTURE.md            # This blueprint
├── docker-compose.yml             # Local PostgreSQL + pgvector service
├── .gitignore                     # Git ignore rules
└── README.md                      # Project overview and setup instructions
```

---

## 6. Development & Validation Commands

### Backend
```bash
# Activate virtual environment (Windows PowerShell)
backend\.venv\Scripts\Activate.ps1

# Run tests
backend\.venv\Scripts\pytest -v backend/tests

# Run dev server
backend\.venv\Scripts\uvicorn app.main:app --app-dir backend --reload --port 8000
```

### Frontend
```bash
# In frontend/ directory
npm run dev      # Start dev server on port 3000
npm run build    # Verify production build and TypeScript compilation
npm run lint     # Run ESLint
```

### Infrastructure (PostgreSQL + pgvector)
```bash
docker compose up -d postgres
```

---

## 7. Domain 1: Identity & Authentication Architecture

### 7.1 Security & Role Principles
- **Strict Role Boundary**: Public self-registration (`POST /api/v1/auth/register`) enforces student accounts ONLY. Any attempted role field in public payload is discarded.
- **Controlled Staff Provisioning**: Roles such as `teacher`, `mentor`, `hod`, `placement_officer`, and `institution_admin` are created strictly through authenticated administrative workflows (`POST /api/v1/auth/admin/create-user`).
- **Backend Authority**: Authorization decisions are executed on the backend via centralized dependencies (`require_roles`, `require_self_or_roles`, `require_institution_scope`). Frontend UI guards provide UX only.

### 7.2 Password Strategy
- **Argon2id Hashing**: Uses `argon2-cffi` configured with RFC 9106 recommended parameters (time_cost=2, memory_cost=64MiB, parallelism=1).
- **Complexity Enforcement**: Minimum 8 characters, with required uppercase, lowercase, numeric digit, and special symbol.
- **Timing Side-Channel Protection**: Nonexistent user lookups run constant-time dummy password verifications to prevent user enumeration.

### 7.3 Token & Session Management
- **Short-Lived Access Tokens**: Signed JWT with 15-minute expiration, containing `sub`, `role`, `sid` (session ID), and `inst` (institution ID). Stored in browser memory only (never `localStorage`).
- **Rotating Refresh Tokens**: 7-day cryptographically random secret stored in database as a SHA-256 hash. Transmitted via `HttpOnly`, `SameSite=Lax`, and `Secure` (in production) cookies.
- **Revocation**: Password change or logout revokes sessions immediately in the database.

### 7.4 Database & Migrations
- **Database**: PostgreSQL 16.
- **Schema Migrations**: Managed via Alembic (`backend/alembic/versions/0001_create_identity_and_session_tables.py`). No implicit `create_all()` is executed in production runtime.

---

## 8. Domain 2: Academic Management & Institutional Hierarchy Architecture

### 8.1 Core Hierarchy & Data Foundation

Dhruva.AI enforces an institutional organizational hierarchy:

```text
Institution (e.g. RV College of Engineering)
    ↓
Department (e.g. Computer Science and Engineering)
    ↓
Program (e.g. B.Tech Computer Science and Engineering)
    ↓
Academic Year (e.g. 2026-27)
    ↓
Semester (e.g. Semester 5 / Odd Term)
    ↓
Batch (e.g. 2023-2027 Cohort)
    ↓
Section (e.g. Section A, Section B)
```

In parallel, curriculum subjects and delivery mechanisms link into this hierarchy:

```text
Institution
    ↓
Course (e.g. CS301 Database Systems)
    ↓
Course Offering (Course + Academic Year + Semester + Section)
    ├── Student Enrollments (StudentAcademicProfile ↔ CourseOffering)
    └── Teaching Assignments (TeacherAcademicProfile ↔ CourseOffering)
```

### 8.2 Entity Relationships & Integrity

1. **`Institution`**: Root multi-tenant entity supporting institutional isolation, official email domains, and code uniqueness (`code`).
2. **`Department`**: Belongs to an `Institution`. Department codes are unique within the institution (`institution_id`, `code`).
3. **`Program`**: Degree program belonging to a `Department` (`degree_type`, `duration_years`). Codes are unique within the department (`department_id`, `code`).
4. **`AcademicYear`**: Calendar period with strictly validated temporal bounds (`start_date < end_date`) and unique labels per institution.
5. **`Semester`**: Academic period within an `AcademicYear` with sequential numbering (`semester_number`) and unique numbering per year.
6. **`Batch`**: Student admission cohort belonging to a `Program` with strict graduation year validation (`admission_year < graduation_year`).
7. **`Section`**: Class cohort partition within a `Batch` with capped capacity (`capacity`). Section names are unique per batch (`batch_id`, `name`).
8. **`Course`**: Abstract subject specification with credit weight (`credits`) and course type (`core`, `elective`, `lab`, `project`). Codes are unique per institution.
9. **`CourseOffering`**: Delivery unit connecting a `Course` to a specific `Section` within an `AcademicYear` and `Semester`. Unique slot constraint prevents duplicate scheduling.
10. **`StudentAcademicProfile`**: 1:1 link to authenticated `User` record holding academic membership, institutional roll number (`enrollment_number`), cohort batch, and section.
11. **`TeacherAcademicProfile`**: 1:1 link to authenticated `User` record holding departmental affiliation, faculty designation, and employee code (`employee_id`).
12. **`StudentEnrollment`**: Explicit enrollment record connecting `StudentAcademicProfile` to a `CourseOffering`. Unique constraint prevents accidental duplicate enrollment.
13. **`TeachingAssignment`**: Connects `TeacherAcademicProfile` to a `CourseOffering` with assigned role (`lead_instructor`, `co_instructor`, `lab_instructor`).

### 8.3 Authorization Boundaries & Scoping Rules

Authorization is enforced centrally via FastAPI dependencies and database scoping queries:

- **Student**:
  - May view their own academic profile (`/student-profiles/me`) and own course enrollments (`/enrollments`).
  - May view only the course offerings they are actively enrolled in.
  - Cannot modify institutional structures (institutions, departments, programs, courses, sections).
  - Cannot access private academic profiles of other students (`403 Forbidden`).
  - Cannot self-assign or transfer to arbitrary institutions, batches, or sections.
- **Teacher**:
  - May view only the course offerings they are assigned to teach (`/course-offerings`).
  - May inspect the academic profiles and enrollments of students enrolled in their assigned offerings.
  - Cannot inspect private student records or offerings across unrelated departments/courses (`403 Forbidden`).
- **HOD (Head of Department)**:
  - Scoped to their assigned department and institution.
  - May create and schedule courses within their department.
  - Cannot administer resources outside their assigned institution.
- **Institution Admin**:
  - Scoped strictly to their assigned institution (`institution_id`).
  - Full management of departments, programs, academic years, semesters, batches, sections, courses, and offerings within their institution.
  - Cannot create or modify resources in other institutions (`403 Forbidden`).
- **Super Admin**:
  - Platform-wide cross-tenant access.
  - Authorized to create institutions and administer global platform resources.

### 8.4 Database Schema Migrations

- Alembic migration `0002_create_academic_management_tables.py` establishes all 13 academic tables, foreign key constraints (`ON DELETE CASCADE` / `ON DELETE RESTRICT` / `ON DELETE SET NULL`), unique constraints, and B-tree indexes for all high-frequency lookups.

---

## 9. Domain 2.5: National Academic Taxonomy & India-Wide Academic Catalog

### 9.1 Architectural Principle: National Catalog vs. Institutional Structure

Dhruva.AI is **not a CSE-only or engineering-only platform**. It supports the entire Indian higher-education ecosystem across institutions, disciplines, degrees, programs, specializations, courses, skills, and career pathways.

To prevent hardcoding giant lists or duplicating records per college, the system enforces a strict architectural separation:

```text
A. NATIONAL / GLOBAL ACADEMIC CATALOG (Authoritative & Versioned)
   India / Regulatory Body (AICTE, UGC, NMC, BCI, etc.)
       ↓
   Academic Discipline (Engineering, Sciences, Commerce, Arts, Design, Law, Medicine, Agriculture)
       ↓
   Degree Type (Certificate, Diploma, UG, PG, Doctoral)
       ↓
   Program Catalog (B.Tech, B.Sc, BCA, BBA, B.Com, B.A, B.Des, MBBS, LL.B, M.Tech, MBA, Ph.D.)
       ↓
   Program Specialization (e.g. CSE, AI & ML, Robotics, Data Science, Product Design)
       ↓
   Course Catalog (Standardized course definitions, credit weights, academic levels, prerequisites)
       ↓
   Skill Catalog & Career Catalog (Taxonomies decoupled from specific colleges)

B. INSTITUTION-SPECIFIC ACADEMIC STRUCTURE (Local Implementation)
   Institution (e.g. IIT Delhi, BITS Pilani)
       ↓
   Department (e.g. Computer Science, Mechanical)
       ├── Institution Program Mapping ───→ National ProgramCatalog (e.g. B.Tech CSE)
       └── Institution Course Mapping  ───→ National CourseCatalog (e.g. Data Structures)
           ↓
       Course Offering (Local Section + Term + Faculty)
           ↓
       Student Enrollment
```

A college **never duplicates** the national catalog; instead, it creates an explicit mapping record (`InstitutionProgramMapping` / `InstitutionCourseMapping`) binding its local program/course code to the authoritative national standard while preserving its unique curriculum titles and internal codes.

### 9.2 Domain Entities & Schema

1. **`AcademicCatalogSource`**: Regulatory or statutory academic authorities (e.g., AICTE, UGC, NMC, BCI, NBA) providing authoritative provenance for catalog datasets.
2. **`AcademicCatalogVersion`**: Immutable version release identifiers (e.g., `v2026.1`, `National Model Curriculum 2026`) tracking dataset releases, effective dates, and status (`draft`, `active`, `superseded`, `archived`).
3. **`AcademicDiscipline`**: Broad fields of higher learning (Engineering & Technology, Science, Commerce & Management, Arts & Humanities, Design, Law, Medicine, Agriculture, etc.). Supports aliases and slug lookups.
4. **`DegreeType`**: Data-driven academic level classifications (Certificate, Diploma, Undergraduate, Postgraduate, Doctoral) with typical durations and level hierarchy.
5. **`ProgramCatalog`**: Standardized national degree programs (B.Tech, B.Sc, BCA, BBA, B.Com, B.A, B.Des, MBBS, LL.B, M.Tech, MBA, Ph.D.) linked to a discipline and degree type.
6. **`ProgramSpecialization`**: Program sub-disciplines (e.g. AI & ML, Data Science, Robotics) supporting institution-specific nomenclature and aliases.
7. **`CourseCatalog`**: Standardized national courses with credit recommendations, academic levels (`introductory`, `intermediate`, `advanced`, `research`), and prerequisite specifications.
8. **`SkillCatalog`**: Granular, reusable skill entities classified by category (`technical`, `cognitive`, `soft`, `domain`).
9. **`CareerCatalog`**: Real-world career roles (Software Engineer, Data Scientist, UX Designer, Robotics Engineer) classified by industry sector.
10. **Multi-Dimensional Mappings**:
    - `ProgramSkillMapping`: Core and elective skills developed by a program.
    - `CourseSkillMapping`: Skills acquired through specific course curricula with depth levels.
    - `CareerSkillMapping`: Required and optional skills demanded by specific career pathways.
    - `ProgramCareerMapping`: Alignment scoring between degree programs and target career options.
11. **Institutional Bridge Mappings**:
    - `InstitutionProgramMapping`: Connects a college's internal `Program` to a national `ProgramCatalog`.
    - `InstitutionCourseMapping`: Connects a college's internal `Course` to a national `CourseCatalog`.
12. **`CatalogImportJob`**: Ingestion audit tracking for bulk JSON/CSV imports, tracking processed records, validation failures, duplicate records, and dry-run execution reports.

### 9.3 Ingestion Pipeline & Importer Architecture

The system features an automated, extensible import architecture (`CatalogImporter`):
- **Supported Formats**: CSV, JSON, and future REST API feeds.
- **Validation**: Strict Pydantic V2 schema validation before any database persistence.
- **Dry-Run Mode**: Allows testing datasets without mutating production database tables.
- **Idempotency**: Prevents duplicate records; existing entities are safely identified via unique code/slug constraints.
- **Failed-Record Reporting**: Returns structured audit trails detailing row-level errors and non-blocking failure logs.

### 9.4 Role-Based Access Control (RBAC) & Security Scoping

- **Super Admin**: Full administrative control to curate catalog items, manage statutory source provenance, release versions, and execute import jobs.
- **Institution Admin**: Browses the national catalog and maps internal institutional programs and courses. Cannot modify or delete national records. Cannot map resources belonging to another institution (`403 Forbidden` / `404 Not Found`).
- **Teachers & Students**: Authenticated read-only access to browse and search the national taxonomy, explore career skill pathways, and understand prerequisite course structures.
- **Critical AI Guardrail**: Google Gemini / LLMs are strictly forbidden from acting as the source of truth for academic programs, courses, degrees, or institutional eligibility. AI may summarize or explain catalog records fetched from the database, but may never hallucinate or invent non-existent curriculum records.

### 9.5 Database Migrations & Validation

- Migration `0003_create_national_academic_catalog_tables.py` creates all 16 catalog and mapping tables with foreign keys, cascading deletes, unique constraints, and B-tree indexes.
- Validated with 68/68 passing backend unit and integration tests, 0 ESLint warnings, and a complete Next.js production build.

---

## 10. Domain 3 — Student & Faculty Management, Onboarding & Academic Profiles

Domain 3 establishes individual, auditable, and securely scoped workspaces for every legitimate institutional actor (Students, Faculty, Mentors, HODs, Institution Admins, Placement Officers, and Super Admins).

### 10.1 Core Principles & Architecture
- **Single Source of Truth**: User identity originates from Domain 1 (`User`), academic relationships are governed by Domain 2 (`StudentAcademicProfile`, `TeacherAcademicProfile`, `TeachingAssignment`), and skill/career canonical records reference Domain 2.5 (`SkillCatalog`, `CareerCatalog`).
- **Deterministic-First Calculations**: Profile completion (0.0% to 100.0%) is computed strictly from actual persisted records across 8 weighted sections via `calculate_profile_completion`. LLMs are **never** permitted to evaluate completion, grant skill verifications, or modify academic status.
- **Privacy & Minimization**: Mentor observation notes default to `private_mentor` and are strictly concealed from student query scopes. Students cannot view or access records belonging to other students. Faculty access is bounded by assigned course offerings and mentee relations.
- **Security in Bulk Ingestion**: The bulk onboarding engine sanitizes CSV input against Formula Injection attacks (`=`, `+`, `-`, `@`, `\t`, `\r`), enforces institution binding from the authenticated admin token, prevents cross-institution injections, and provides dry-run preview validation.

### 10.2 Persisted Data Models (Alembic Migration 0004)
1. **`StudentProfileDetail`**: Biographical headline, bio, learning preferences, and professional contact links.
2. **`StudentAcademicStatusHistory`**: Auditable record of academic status transitions (`active`, `on_leave`, `suspended`, `graduated`, `withdrawn`, `transferred`, `completed`, `inactive`) with effective dates and actor metadata.
3. **`StudentSkill`**: Bridges students to canonical `SkillCatalog` entries with proficiency ratings and verification states (`self_declared`, `assessment_verified`, `course_verified`, `project_verified`, `faculty_verified`).
4. **`StudentInterest`**: Exploration interest records linked to `AcademicDiscipline` or `CareerCatalog`.
5. **`StudentCareerGoal`**: Target career pathways referencing canonical `CareerCatalog` records with priority ranking.
6. **`StudentProject` & `StudentProjectSkill`**: Capstone and open-source project artifacts connected to demonstrated skill catalog nodes.
7. **`StudentCertification` & `StudentAchievement`**: Audited credentials and recognitions with explicit verification state machines.
8. **`StudentPortfolio` & `StudentResume`**: Presentation-ready structured representations referencing real verified items rather than duplicated mock data.
9. **`TeacherProfileDetail`**: Extended faculty qualifications, expertise areas, and office locations.
10. **`MentorshipRelation`, `MentorGroup`, `MentorGroupMember`, `MentorNote`**: 1:1 and cohort-based mentorship with permission-controlled notes.
11. **`StudentIntervention`**: Structured follow-ups for academic, attendance, course, and career support with audit trails.
12. **`OnboardingImportJob` & `DomainAuditLog`**: Audit tracking for bulk operations and profile mutations.

### 10.3 API Endpoints
- `/api/v1/students/me`: Student self profile details and dashboard overview.
- `/api/v1/students/me/skills`: Mapped skills management referencing canonical SkillCatalog.
- `/api/v1/students/me/projects`: Capstone and technical project evidence tracking.
- `/api/v1/students/me/certifications`: Third-party credentials with verification states.
- `/api/v1/students/me/career-goals`: Target career pathways anchored to CareerCatalog.
- `/api/v1/students/me/portfolio` & `/resume`: Structured portfolio and resume records.
- `/api/v1/faculty/me` & `/overview`: Faculty profile, assigned offerings, and enrolled students.
- `/api/v1/mentorship/me`: Assigned student mentees and notes management.
- `/api/v1/interventions`: Student support tracking and resolution.
- `/api/v1/imports/students` & `/imports/faculty`: Bulk CSV/JSON onboarding with dry-run support.
- `/api/v1/imports/admin/overview`: Institutional database-calculated metrics and status distributions.

---

## 11. Domain 4 — Course Delivery, Curriculum Structure & Learning Content Engine

Domain 4 forms the core LMS (Learning Management System) foundation of Dhruva.AI, delivering structured, version-aware, and institutional curriculum content to enrolled students.

### 11.1 Architectural Separation of Concerns
To ensure high scalability and prevent entity confusion, the system strictly separates:
- **National Course Catalog (Domain 2.5 `CourseCatalog`)**: India-wide standardized canonical definitions.
- **Institution Course (Domain 2 `Course`)**: Local college course offering catalogue.
- **Course Offering (Domain 2 `CourseOffering`)**: Specific semester, academic year, section, and faculty delivery instance.
- **Course Content & Curriculum (Domain 4 `CourseContent`, `Curriculum`, `Module`, `Lesson`)**: Reusable learning content trees and structured blocks.
- **Student Learning Progress (Domain 4 `LessonProgress`, `CourseProgress`)**: Deterministic completion and time tracking tied to specific course offerings and content versions.

### 11.2 Core Data Models & Relationships (Alembic Migration 0005)
1. **`CourseContent` & `CourseContentVersion`**:
   - Reusable content containers with titles, descriptions, difficulty levels, target audiences, and lifecycle states (`draft`, `in_review`, `published`, `archived`).
   - Immutable versions preserve historical student progress across curriculum revisions.
2. **`Curriculum`, `Module`, `Lesson`, `LessonContentBlock`**:
   - Deterministic ordering using integer `order_index` fields with unique constraints and two-pass reordering algorithms.
   - Lessons support modular types: `text`, `video`, `article`, `interactive`, `coding`, `quiz`, `assignment`, `project`, `mixed`.
   - Content blocks support structured representations (`heading`, `paragraph`, `code`, `callout`, `quote`, `video`, `image`, `resource`, `embed`) rather than opaque unmanaged HTML blobs.
3. **`LearningObjective`**:
   - Explicit measurable student learning outcomes associated with concepts and skills.
4. **`Concept`, `ConceptPrerequisite`, `LessonConcept`, `ConceptSkill`, `LessonSkill`, `CourseSkill`**:
   - Canonical knowledge graph representing atomic units of knowledge.
   - Cross-course concept reusability with explicit directed acyclic prerequisite relationships.
   - Bridges lessons and concepts directly to Domain 2.5 `SkillCatalog`.
5. **`LearningResource`, `ResourceVersion`, `LessonResource`**:
   - Polymorphic resource attachments (`document`, `pdf`, `video`, `dataset`, `reference_book`, `code_repository`).
   - S3-compatible and local file storage abstraction with SHA-256 checksums, MIME verification, and temporary signed access URLs.
   - Strict server-side access level gating (`public`, `institution_only`, `course_only`, `enrolled_students`, `faculty_only`).
6. **`ContentReview` & `ContentReviewComment`**:
   - Formal audit trail and peer-review state machine (`draft` -> `in_review` -> `published` / `changes_requested`).
   - Preserves reviewer feedback notes and line-item comments.
7. **`LessonProgress`, `ModuleProgress`, `CourseProgress`**:
   - Completely deterministic progress engine tracking started/completed states, timestamps, and active engagement seconds.
   - Server-side roll-up calculations (`completed_lessons / total_required_lessons * 100`).
8. **`StudentBookmark` & `StudentLearningNote`**:
   - Private personal learning workspaces strictly isolated per student.

### 11.3 Security, Rich Text Sanitization & Access Boundaries
- **HTML Sanitization**: Zero-dependency `SafeHTMLSanitizer` based on Python `html.parser` strips malicious elements (`<script>`, `<style>`, `<iframe>`, `<object>`, `<embed>`), removes unsafe `javascript:`/`vbscript:` URI protocols, and disallows dangerous inline attributes (`onload`, `onerror`, `onclick`).
- **Institutional & Enrollment Scoping**:
   - Students cannot read unpublished or draft course content under any circumstance.
   - Students can only access course delivery materials if they hold an active enrollment in the associated `CourseOffering` belonging to their authorized institution.
   - Cross-institution content tampering and cross-student progress alterations are strictly forbidden at the database query layer.
- **Faculty Scoping**:
   - Faculty can only edit course content if assigned to the course offering or possessing departmental/institutional administrative privileges (`HOD`, `Institution Admin`, `Super Admin`).

### 11.4 AI Boundary & Determinism Policy
- **Zero AI Control Over Authoritative State**: LLMs/AI models are strictly prohibited from determining course completion, lesson completion, progress percentages, published states, or enrollment authorizations.
- **Future AI Drafting Gate**: Any future AI-generated lesson content or objective drafting will be explicitly tagged as `is_ai_generated: true` and remain in `draft` status until explicitly reviewed, edited, and approved by a certified human instructor.

### 11.5 Quality Verification & Baseline
- Backend test suite: **92/92 passed** across unit, RBAC, isolation, workflow, sanitization, and regression suites.
- Frontend: 0 ESLint errors, 0 ESLint warnings, TypeScript strict compilation passed, production build passed.
- Alembic migration `0005_create_course_content_and_learning_tables.py` fully verified for PostgreSQL 16 compatibility.

---

## 12. Domain 5: Assessment Engine, Question Banks, Evaluation & Deterministic Evidence

Domain 5 establishes the authoritative, enterprise-grade assessment layer for Dhruva.AI. It guarantees institutional assessment integrity across quizzes, diagnostic tests, assignments, midterms, semester examinations, and coding assessments.

### 12.1 Core Architectural Principles
1. **Clean Ground Truth Separation**:
   - **Question Bank & Authoring**: Isolated institutional question repositories with review governance (`draft` -> `in_review` -> `approved` -> `archived`).
   - **Question Versions (`QuestionVersion`)**: Strictly immutable once used in any assessment attempt. Editing a question creates a new version; historical attempts are never mutated.
   - **Assessment Definition & Versions (`AssessmentVersion`)**: Freezes question set, order, points, timing, rules, and blueprints into an immutable snapshot upon publication.
   - **Assessment Attempts (`AssessmentAttempt`)**: Strictly student-scoped with authoritative server-calculated expiry timers (`expires_at`). Never trust client clocks.
   - **Responses (`AssessmentResponse`)**: Version-bound, idempotent autosave, and transactional freeze on submission.
   - **Authoritative Evaluations (`AssessmentEvaluation`)**: 100% deterministic strategy pattern using exact `Decimal` arithmetic.
   - **Assessment Results (`AssessmentResult`)**: Authoritative scores, grades, pass/fail status, and controlled release workflows (`draft_result`, `internal`, `released`, `recalled`).
   - **Canonical Evidence (`ConceptEvidence`, `SkillEvidence`)**: Append-only provenance records feeding future Domain 6 Knowledge State & Mastery systems.

2. **Zero-Trust Delivery Redaction**:
   - The student delivery API (`/attempts/{id}/delivery`) delivers only the question prompt, sanitized options (without answer keys), point values, and interaction metadata.
   - Answer keys, explanations, evaluator configurations, and hidden test cases are strictly redacted before submission and official grade release.

3. **Pure Evaluation Strategy Pattern**:
   - Evaluators reside under `backend/app/domains/assessment/evaluators/`:
     - `SingleChoiceEvaluator`: Deterministic option matching with configurable negative marking.
     - `MultipleChoiceEvaluator`: Deterministic selection matching supporting all-or-nothing and partial credit with penalty subtraction.
     - `TrueFalseEvaluator`: Exact boolean matching.
     - `NumericEvaluator`: Exact decimal comparison within configurable absolute tolerance (`epsilon`).
     - `FillBlankEvaluator`: Case-insensitive/trimmed token matching with optional aliases.
     - `OrderingEvaluator`: Exact sequence and partial Kendall-tau alignment.
     - `MatchingEvaluator`: Key-value pair alignment.
     - `ManualRubricEvaluator`: Certified human faculty grading against immutable rubric criteria (`EvaluationRubric`, `RubricCriterion`, `ManualEvaluation`).
     - `CodingEvaluator` (`CodeExecutionProvider`): Architectural sandbox abstraction preventing arbitrary student code execution directly in the API process.

4. **Exact Decimal Scoring & Grading Schemes**:
   - `AssessmentScoringEngine` computes authoritative earned marks using Python `Decimal` and database `NUMERIC(10, 4)` types to prevent floating-point drift.
   - Grade assignment relies on configurable grading rules (`GradeScheme`, `GradeRule`), calculating grades (e.g., O, A+, A, B+, B, C, F) and pass/fail thresholds deterministically.

5. **Canonical Evidence Generation & Provenance**:
   - Every evaluated question deterministically emits:
     - `ConceptEvidence` linked to Domain 4 canonical `Concept`.
     - `SkillEvidence` linked to Domain 2.5 `SkillCatalog`.
   - Complete provenance answers: *Who? What? When? Which assessment? Which question version? Which concept? Which skill? What score? What evaluation method?*
   - Domain 5 does NOT calculate mastery or modify `StudentSkill` records; it produces the immutable evidence for Domain 6 to consume.

6. **AI Boundary Policy**:
   - AI/LLM models are **strictly prohibited** from:
     - Determining objective answers or correctness.
     - Overriding authoritative marks or scores.
     - Determining pass/fail status or assigning grades.
     - Changing question difficulty or completion states.
     - Releasing results or generating authoritative evidence.
   - Future AI capabilities (such as question drafting or subjective feedback suggestions) are strictly auxiliary and require certified human review before entering the system.

### 12.2 Database Schema & Alembic Migration 0006
Implemented in `backend/alembic/versions/0006_create_assessment_and_evaluation_tables.py`:
- `question_banks`, `questions`, `question_versions`, `question_options`, `question_concepts`, `question_skills`
- `evaluation_rubrics`, `rubric_criteria`, `manual_evaluations`
- `coding_configurations`, `coding_test_cases`
- `assessments`, `assessment_blueprints`, `blueprint_rules`, `assessment_versions`, `assessment_questions`
- `grade_schemes`, `grade_rules`
- `assessment_attempts`, `assessment_responses`, `assessment_evaluations`, `assessment_results`, `assessment_reviews`
- `concept_evidences`, `skill_evidences`

### 12.3 Quality Verification & Baseline
- Backend test suite: **95/95 passed** (100% pass rate across Domains 1–5).
- Frontend: **0 ESLint errors, 0 ESLint warnings**, TypeScript strict compilation passed, Next.js App Router production build passed.
- Alembic migration `0006` verified via `alembic upgrade head --sql` with 0 syntax errors on PostgreSQL 16.

---

## 13. Domain 6: Knowledge State, Concept Mastery Engine & Spaced Repetition (SM-2)

### 13.1 Architecture Overview & Core Principle
Domain 6 transforms authoritative learning evidence emitted by Domain 5 into a deterministic, explainable representation of what a student knows, what they are forgetting, and what should be reviewed next.

```
Assessment / Learning Evidence (Domain 5)
                 ↓
      Concept Evidence (Immutable)
                 ↓
     Student Knowledge State (Domain 6)
                 ↓
        Mastery Calculation (M ∈ [0, 1])
                 ↓
        Retention / Decay (R ∈ [0, 1])
                 ↓
      Review Scheduling (SuperMemo SM-2)
                 ↓
      Adaptive Learning Queue (Daily Mission)
```

#### Absolute Invariants
1. **Evidence Immutability**: Historical `ConceptEvidence` records from Domain 5 are never modified, deleted, or re-evaluated.
2. **Deterministic Computation**: Given identical evidence, configuration, and clock reference, the engine produces identical mastery, confidence, retention, and review schedules.
3. **Zero AI Authority**: Gemini or any LLM is strictly prohibited from assigning mastery, setting confidence, calculating retention, creating review dates, or overriding the learning queue.
4. **Mastery vs. Retention Decoupling**:
   - **Mastery ($M$)**: How well the student acquired the concept. Remains relatively stable.
   - **Retention ($R$)**: Likelihood of active recall at the current moment. Decays over elapsed time via Ebbinghaus exponential decay.
5. **Client Write Protection**: Frontend clients cannot submit mastery values, retention estimates, or review dates. Clients only submit learning events (e.g., recall trial rating 0–5).
6. **Student-Concept Uniqueness**: Exactly one authoritative active knowledge state exists per `(student_profile_id, concept_id)`. Changes are tracked in append-only history tables.

### 13.2 Pure Engine Components
1. **`ConceptMasteryEngine` (`mastery_engine.py`)**:
   - Computes weighted mastery $M \in [0, 1]$:
     $$M = \frac{\sum w_i \cdot d_i \cdot r_i \cdot s_i}{\sum w_i \cdot d_i \cdot r_i}$$
     where $w_i$ is evidence source weight (assessment: 1.0, practice: 0.8), $d_i$ is question difficulty multiplier (easy: 0.85, medium: 1.0, hard: 1.15, expert: 1.3), $r_i = e^{-\lambda \cdot \Delta t}$ is recency decay factor, and $s_i$ is normalized evidence score.
   - Computes Confidence $C \in [0, 1]$ based on sample size saturation and variance penalty:
     $$C = \min\left(1.0, \frac{N}{N_{\text{threshold}}}\right) \cdot (1 - \min(1.0, \text{variance} \cdot 2))$$
   - Classifies deterministic states: `unknown` (insufficient evidence), `introduced`, `developing` ($M < 0.60$), `proficient` ($0.60 \le M < 0.80$), `mastered` ($M \ge 0.80$), and `at_risk` ($R < 0.50$ or sudden negative shift).
   - Classifies deterministic trend: `strongly_improving`, `improving`, `stable`, `declining`, `strongly_declining`, or `insufficient_data`.

2. **`RetentionEngine` (`retention_engine.py`)**:
   - Implements Ebbinghaus-derived exponential decay:
     $$R = e^{-\frac{\Delta t}{S}}$$
     where $\Delta t$ is elapsed days since last recall, and memory stability $S = S_0 \cdot (1 + \text{repetition} \cdot 1.5) \cdot (\text{ease factor} / 2.5) \cdot M$.

3. **`SM2Scheduler` (`sm2_scheduler.py`)**:
   - Pure implementation of the SuperMemo SM-2 algorithm:
     - Repetition 1: Interval = 1 day.
     - Repetition 2: Interval = 6 days.
     - Repetition $n \ge 3$: $\text{Interval}_n = \text{round}(\text{Interval}_{n-1} \cdot \text{Ease Factor})$.
     - Ease Factor update:
       $$\text{EF}' = \max\left(1.3000, \text{EF} + (0.1 - (5 - q) \cdot (0.08 + (5 - q) \cdot 0.02))\right)$$
     - Quality $q \in [0, 5]$: If $q < 3$, recall failed: repetition resets to 0 and interval resets to 1 day. Historical schedule is preserved.

4. **`PrerequisiteReadinessEngine` (`prerequisite_engine.py`)**:
   - Traverses the Domain 4 `ConceptPrerequisite` directed acyclic graph (DAG).
   - Detects cycles via visited sets to prevent infinite loops.
   - Computes prerequisite readiness score $P \in [0, 1]$ and classifies health: `healthy` ($P \ge 0.70$), `partial` ($0.50 \le P < 0.70$), `weak` ($P < 0.50$), or `unknown`.

5. **`LearningPriorityEngine` (`priority_engine.py`)**:
   - Synthesizes student priority score $P_{\text{score}} \in [0, 1]$ from:
     - Overdue status (weight 0.35)
     - Retention risk (weight 0.25)
     - Mastery gap (weight 0.20)
     - Prerequisite weakness (weight 0.15)
     - Recent failure (weight 0.05)
   - Emits structured, machine-readable reason codes (`REVIEW_OVERDUE`, `RETENTION_LOW`, `MASTERY_LOW`, `PREREQUISITE_WEAK`, `RECENT_FAILURE`, `INSUFFICIENT_EVIDENCE`).
   - Generates deduplicated Daily Mission tasks linking to canonical Domain 4 lessons and assessments.

### 13.3 Database Models & Alembic Migration 0007
Implemented in `backend/alembic/versions/0007_create_knowledge_state_and_sm2_tables.py`:
- `student_concept_knowledge_states`: Authoritative current state per student and concept.
- `knowledge_state_histories`: Append-only audit history of every recalculation and state transition.
- `concept_evidence_processings`: Idempotent deduplication ledger preventing double-counting evidence.
- `concept_review_states`: Current SM-2 spaced repetition schedule state.
- `concept_review_histories`: Append-only review trial history recording recall quality ratings.
- `learning_priority_snapshots`: Persisted priority scores and reason codes.
- `mastery_adjustments`: Certified manual override ledger preserving original calculated scores.

### 13.4 Frontend Experience
- `/knowledge`: Student Knowledge Dashboard with summary metrics, mastery distribution, developing/at-risk watchlists, Daily Mission tasks, search/filtering, and deterministic recompute.
- `/knowledge/concepts/[id]`: Concept Detail View with mastery/confidence/retention gauges, prerequisite readiness badges, and complete evidence/mastery audit histories.
- `/review`: Spaced Repetition Review Center with active flashcard trial, 0–5 SM-2 recall rating buttons, and upcoming schedule queue.

### 13.5 Verification & Quality Baseline
- Backend test suite: **102/102 passed** (100% pass rate across Domains 1–6).
- Frontend: **0 ESLint errors, 0 ESLint warnings**, Next.js App Router production build passed.
- PostgreSQL compatibility: `alembic upgrade head --sql` validated cleanly with 0 errors.

---

## 14. Domain 7: Skill Intelligence, Career Trajectories & Placement Readiness Engine

### 14.1 Core Mission & Principle
Dhruva.AI operates on the foundational principle that **it must never pretend to know something it does not know**. Domain 7 converts the Career Intelligence module from an early visual prototype into an authoritative, deterministic, backend-derived production engine.
- **Zero Mock / Demo Data**: All hardcoded readiness numbers (e.g. 78%), static skill lists, fake enterprise posting percentages (e.g. "required in 82% of enterprise job postings"), and synthetic trajectory steps are completely eradicated.
- **Zero AI Authority**: LLM/Gemini has zero authority over skill evaluation, readiness scores, gap severity, or trajectory step sequencing. AI is strictly confined to explaining authoritative results and student coaching.
- **Separation of Concerns**: Canonical `StudentSkill` records student-declared competencies. `StudentSkillIntelligenceState` records authoritative deterministic intelligence derived from multi-source empirical evidence.

### 14.2 Deterministic Engines & Mathematical Formulas
All algorithms execute deterministically with explicit version tracking (`algorithm_version = "v1.0.0-deterministic"`):
1. **SkillIntelligenceEngine**:
   - Aggregates multi-source evidence with hierarchical source weights:
     $$\text{assessment} (1.0) > \text{verified project} (0.9) > \text{faculty verification} (0.85) > \text{course completion} (0.75) > \text{certification} (0.7) > \text{self-report} (0.25)$$
   - Evaluates observed proficiency as weighted average:
     $$\text{observed\_proficiency} = \frac{\sum (s_i \cdot w_i)}{\sum w_i}$$
   - Penalizes empirical variance to compute verified proficiency:
     $$\text{verified\_proficiency} = \text{observed\_proficiency} \cdot (1.0 - 0.5 \cdot \text{variance})$$
   - Computes confidence based on evidence count and source diversity:
     $$\text{confidence} = \min(1.0, 0.4 \cdot \frac{N}{5} + 0.6 \cdot \frac{D}{3})$$
   - Maps normalized verified proficiency to versioned tiers:
     $$[0.00, 0.20) \to \text{exposure}, [0.20, 0.40) \to \text{beginner}, [0.40, 0.60) \to \text{developing}, [0.60, 0.80) \to \text{proficient}, [0.80, 1.00] \to \text{advanced}$$
2. **CareerReadinessEngine**:
   - Evaluates canonical `CareerSkillMapping` without duplicating catalog tables.
   - Calculates Required, Preferred, and Critical skill coverage.
   - Composite Career Readiness:
     $$\text{readiness\_score} = 0.50 \cdot \text{req\_cov} + 0.35 \cdot \text{crit\_cov} + 0.15 \cdot \text{pref\_cov}$$
   - Clearly separates **Career Fit** (academic alignment & declared aspirations) from **Career Readiness** (current competency preparation).
3. **SkillGapEngine**:
   - Classifies gap severity deterministically: `critical` (critical skill below cutoff), `high` (required skill deficit $\ge 0.40$), `medium` ($0.20 \le \text{gap} < 0.40$), `low` ($\text{gap} < 0.20$), or `none`.
4. **CareerTrajectoryEngine**:
   - Sequentially addresses critical and high gaps first.
   - Maps milestones to canonical Domain 4 lessons/concepts and Domain 5 assessments.
   - Enforces honesty: when curriculum mappings are missing, marks step as `"not_available"` with explanation `"No mapped learning content available yet."` (zero hallucinated courses).
5. **PlacementReadinessEngine**:
   - Evaluates 6 distinct components: Technical Readiness, Assessment Readiness, Project Evidence, Communication, Resume, and Interview.
   - Never fabricates employment probabilities (e.g. "85% placement chance").
   - Unassessed dimensions are strictly recorded and rendered as `"not_assessed"`. Status transitions honestly: `not_yet_assessed` $\to$ `needs_portfolio` $\to$ `assessing` $\to$ `ready_for_review` $\to$ `placement_ready`.

### 14.3 Database Architecture & Migration
Implemented in migration `0008_complete_skill_intelligence_and_career_readiness.py`:
- `student_skill_intelligence_states`: Unique on `(student_profile_id, skill_id)` with check constraints $[0, 1]$ on proficiencies and confidence.
- `student_skill_evidence_records`: Immutable evidence ledger tracking source type, provenance, weight, and verification status.
- `student_career_readiness_states`: Unique on `(student_profile_id, career_id)` with explainability breakdown.
- `career_trajectories` & `career_trajectory_steps`: Sequenced milestones linking directly to canonical curriculum items.
- `placement_readiness_states`: Unique on `student_profile_id` with granular component statuses.

### 14.4 Centralized RBAC & API Endpoints
All endpoints enforce centralized RBAC and derive student identity server-side:
- `GET /api/v1/career/intelligence`: Student career overview, fit, readiness, strengths, gaps, and trajectory.
- `GET /api/v1/career/readiness`: Dedicated readiness and explainability breakdown.
- `GET /api/v1/career/gaps`: Prioritized career skill gaps.
- `GET /api/v1/career/trajectory`: Sequenced learning trajectory steps.
- `GET /api/v1/career/compare?career_ids=...`: Multi-career side-by-side comparison matrix.
- `GET /api/v1/career/placement-readiness`: Honest institutional placement preparedness framework.
- `GET /api/v1/skills`: Authenticated student's verified skills list.
- `GET /api/v1/skills/{id}`: Detailed skill provenance and evidence audit trail.
- `POST /api/v1/career/recompute/skills`: Invalidate and recompute verified skills.
- `POST /api/v1/career/recompute/career/{career_id}`: Recompute career readiness.
- `GET /api/v1/students/{student_profile_id}/skills`: Scoped for authorized faculty, mentors, HODs, placement officers, and admins.
- `GET /api/v1/students/{student_profile_id}/career/{career_id}/readiness`: Scoped faculty/placement officer inspection.

### 14.5 Frontend Routes
- `/skills`: Verified Skill Intelligence dashboard with tier filters, search, and provenance metrics.
- `/skills/[id]`: Skill detail view with complete multi-source evidence ledger.
- `/career`: Career Intelligence hub mounting dynamic `CareerIntelligenceCard`.
- `/career/[id]`: Career requirements and readiness for specific catalog careers.
- `/career/readiness`: Dedicated deep dive with explainability breakdown and honest placement framework.
- `/career/trajectory`: Step-by-step learning sequence with prerequisite checks.
- `/career/compare`: Multi-career comparative matrix.

### 14.6 Verification & Quality Baseline
- Backend test suite: **108/108 passed** (100% pass rate across Domains 1–7 with 0 regressions).
- Frontend ESLint: **0 errors, 0 warnings** (`npm run lint`).
- Frontend production build: **Passed cleanly** (`npm run build`).
- PostgreSQL compatibility: `alembic upgrade head --sql` validated cleanly with 0 errors.
