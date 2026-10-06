# DHRUVA.AI — PILOT INSTITUTION ONBOARDING GUIDE
**End-to-End Implementation Playbook for Real College & University Deployments**

---

## 1. Overview & Institutional Architecture

Dhruva.AI enforces a strict 15-stage hierarchical onboarding sequence for real higher education institutions. Each level guarantees referential integrity, tenant isolation, and deterministic role-based access control (RBAC).

```
[ Step 1: Institution Entity ]
             │
[ Step 2: System Administrator Account ]
             │
[ Step 3: Academic Departments (CSE, ECE, MECH, etc.) ]
             │
[ Step 4: Degree Programs (B.Tech CSE, M.Tech Data Science) ]
             │
[ Step 5: Academic Years (2025-2026, 2026-2027) ]
             │
[ Step 6: Semesters (Odd / Even Semesters) ]
             │
[ Step 7: Cohort Batches (2022-2026 Batch) ]
             │
[ Step 8: Class Sections (Section A, Section B) ]
             │
[ Step 9: Course Catalog Mapping (Curriculum / Syllabus) ]
             │
[ Step 10: Faculty Roster Provisioning & Role Assignment ]
             │
[ Step 11: Student Roster Bulk Onboarding (Enrollment Numbers) ]
             │
[ Step 12: Course Offerings Creation (Semester Offering) ]
             │
[ Step 13: Student Enrollment & Teaching Assignments ]
             │
[ Step 14: Curriculum Content, Modules, Lessons & Concepts ]
             │
[ Step 15: Assessments, Rubrics & Pilot Launch Readiness ]
```

---

## 2. Step-by-Step Onboarding Workflow

### Step 1: Institution Entity Creation
Create the primary institutional tenant in the database:
- **API Endpoint**: `POST /api/v1/academic/institutions`
- **Required Fields**:
  - `name`: Full legal college name (e.g., `"National Institute of Technology Karnataka"`)
  - `code`: Unique institutional identifier (e.g., `"NITK-SURATHKAL"`)
  - `domain`: Institutional email domain (e.g., `"nitk.edu.in"`)
  - `address`, `state`, `country`, `accreditation_details` (NAAC/NBA).

### Step 2: Primary Administrator Provisioning
Provision the founding institution super-admin account:
- **API Endpoint**: `POST /api/v1/auth/register-admin` (or backend CLI tool)
- **Role**: `INSTITUTION_ADMIN`
- **Verification**: Ensure two-factor authentication / secure password change on first login.

### Step 3: Academic Department Structure
Establish departments under the institution tenant:
- **API Endpoint**: `POST /api/v1/academic/institutions/{inst_id}/departments`
- **Examples**:
  - `CSE` — Computer Science and Engineering
  - `IT` — Information Technology
  - `ECE` — Electronics and Communication Engineering

### Step 4: Programs & Degrees
Map educational degrees to departments:
- **API Endpoint**: `POST /api/v1/academic/departments/{dept_id}/programs`
- **Fields**:
  - `name`: `"Bachelor of Technology in Computer Science and Engineering"`
  - `degree_type`: `"B.Tech"`
  - `duration_years`: `4`
  - `total_credits`: `160`

### Step 5: Academic Calendar & Academic Years
Define active academic calendars:
- **API Endpoint**: `POST /api/v1/academic/academic-years`
- **Fields**:
  - `year_name`: `"2025-2026"`
  - `start_date`: `"2025-07-01"`
  - `end_date`: `"2026-06-30"`
  - `is_active`: `true`

### Step 6: Semesters
Subdivide the academic year into instructional periods:
- **API Endpoint**: `POST /api/v1/academic/semesters`
- **Fields**:
  - `name`: `"Fall Semester 2025"`
  - `semester_number`: `5`
  - `term_type`: `"ODD"`

### Step 7: Cohort Batches
Group student entrance cohorts:
- **API Endpoint**: `POST /api/v1/academic/programs/{program_id}/batches`
- **Fields**:
  - `batch_name`: `"2022-2026 Batch"`
  - `admission_year`: `2022`
  - `graduation_year`: `2026`

### Step 8: Class Sections
Create manageable instructional clusters:
- **API Endpoint**: `POST /api/v1/academic/batches/{batch_id}/sections`
- **Fields**:
  - `section_name`: `"Section A"`
  - `capacity`: `60`

### Step 9: Canonical Course Catalog Integration
Map institutional syllabus to Dhruva's National Catalog:
- **API Endpoint**: `POST /api/v1/academic/programs/{program_id}/courses`
- **Fields**:
  - `course_code`: `"CS301"`
  - `title`: `"Design and Analysis of Algorithms"`
  - `credits`: `4`
  - `theory_hours`: `3`, `practical_hours`: `2`
  - `national_catalog_course_id`: Link to AICTE standard syllabus.

### Step 10: Faculty Accounts & Department Assignment
Provision faculty credentials:
- **API Endpoint**: `POST /api/v1/academic/departments/{dept_id}/faculty/bulk`
- **Fields**: Email, Full Name, Employee ID, Designation (Professor/Assistant Professor).
- **Assigned Role**: `FACULTY` or `HOD` (Department Chair).

### Step 11: Student Roster Ingestion
Bulk onboard student learner accounts:
- **API Endpoint**: `POST /api/v1/academic/sections/{section_id}/students/bulk-upload`
- **Format**: CSV / JSON payload containing:
  - `roll_number`: `"22CS101"`
  - `full_name`: `"Student Name"`
  - `institutional_email`: `"student@college.edu.in"`
- **Security**: System generates randomized initial verification tokens sent via transactional email.

### Step 12: Course Offerings
Instantiate running course instances for the active semester:
- **API Endpoint**: `POST /api/v1/academic/course-offerings`
- **Parameters**: `course_id`, `semester_id`, `academic_year_id`.

### Step 13: Student Enrollments & Faculty Teaching Assignments
- Link faculty instructor to course offering: `POST /api/v1/academic/course-offerings/{id}/instructors`
- Bulk enroll section students: `POST /api/v1/academic/course-offerings/{id}/enrollments`

### Step 14: Curriculum Content & Concept Graph Ingestion
Ingest instructional modules, lessons, and prerequisite dependency graphs:
- Ingest curriculum tree: Modules -> Lessons -> Concept nodes -> Prerequisite edges.
- Verify Knowledge Tracer graph connectivity in backend.

### Step 15: Assessments, Rubrics & Pilot Launch
- Publish diagnostic baseline assessment.
- Configure evaluation rubrics, test cases, and time limits.
- Release pilot schedule to faculty and students.

---

## 3. Pilot Safety & Verification Checklist

Before opening the platform to real students:
- [ ] Admin, Faculty, and Student test accounts verified in staging.
- [ ] Tenant isolation verified (cross-institution data leak impossible).
- [ ] Email verification & password reset links deliver successfully.
- [ ] Timed assessment submission locks down on timer expiry.
- [ ] Deterministic evaluation scores match rubric weights exactly.
- [ ] AI Copilot responses cite verified textbook / curriculum chunks.
- [ ] Student portfolio public visibility toggles function properly.
- [ ] Backup snapshot schedule active and verified.
