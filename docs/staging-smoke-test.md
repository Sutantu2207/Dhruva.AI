# DHRUVA.AI — STAGING SMOKE TEST & END-TO-END VALIDATION PROTOCOL
**Systematic Cross-Role Smoke Test Suite for Staging & Pre-Production Verification**

---

## 1. Scope & Execution Rules

This document specifies the mandatory end-to-end operational test procedures that must pass in the **staging environment** before promoting any release to production.

- **Zero-Mock Policy**: Tests execute against real PostgreSQL, real Redis, and real ASGI containers.
- **Role Coverage**: All 5 primary institutional personas are validated sequentially.

---

## 2. Test Journey 1: Student Persona Workflow

| Step | Action | Endpoint / Interface | Expected Result | Verified |
| :--- | :--- | :--- | :--- | :--- |
| **STU-01** | **Registration** | `POST /api/v1/auth/register` | Account created; verification token issued. | [x] |
| **STU-02** | **Email Verification** | `POST /api/v1/auth/verify-email` | Email verified; account status activated. | [x] |
| **STU-03** | **Authentication** | `POST /api/v1/auth/login` | JWT access token + HttpOnly secure cookie issued. | [x] |
| **STU-04** | **Profile Setup** | `PUT /api/v1/profiles/me` | Academic profile, interests, and career goals saved. | [x] |
| **STU-05** | **Course Enrollment** | `POST /api/v1/enrollments` | Enrolled in active course offering; progress initialized to 0%. | [x] |
| **STU-06** | **Learning Activity** | `POST /api/v1/content/progress` | Lesson marked complete; next lesson unlocked. | [x] |
| **STU-07** | **Assessment Attempt**| `POST /api/v1/assessments/start` | Assessment attempt created; timer begins; responses saved. | [x] |
| **STU-08** | **Submission & Grade**| `POST /api/v1/assessments/submit` | Deterministic evaluator computes marks; rubric feedback issued. | [x] |
| **STU-09** | **Mastery Update** | `GET /api/v1/mastery/student-state`| Bayesian Knowledge Tracing updates concept mastery state. | [x] |
| **STU-10** | **Spaced Repetition** | `GET /api/v1/mastery/reviews/due` | SM-2 algorithm schedules next concept review interval. | [x] |
| **STU-11** | **Adaptive Remediation**| `GET /api/v1/remediation/plan` | Diagnostic gap detected; targeted remediation step generated. | [x] |
| **STU-12** | **Project Portfolio** | `POST /api/v1/portfolio/projects` | Verified code project added; public portfolio link created. | [x] |
| **STU-13** | **AI Mentor Query** | `POST /api/v1/ai/mentor/chat` | AI answers curriculum question citing textbook chunk; no hallucinations. | [x] |

---

## 3. Test Journey 2: Faculty Persona Workflow

| Step | Action | Endpoint / Interface | Expected Result | Verified |
| :--- | :--- | :--- | :--- | :--- |
| **FAC-01** | **Faculty Login** | `POST /api/v1/auth/login` | Access granted to instructor workspace. | [x] |
| **FAC-02** | **View Assigned Courses**| `GET /api/v1/faculty/courses` | Returns only courses assigned to this instructor (RBAC enforced). | [x] |
| **FAC-03** | **Student Roster** | `GET /api/v1/faculty/courses/{id}/students` | Returns enrolled cohort roster with current mastery summary. | [x] |
| **FAC-04** | **Create Content** | `POST /api/v1/content/lessons` | Draft lesson with markdown and learning objectives created. | [x] |
| **FAC-05** | **Author Assessment** | `POST /api/v1/assessments/create` | Assessment created with blueprint, questions, and rubrics. | [x] |
| **FAC-06** | **Publish Assessment**| `PUT /api/v1/assessments/{id}/publish` | Assessment state updated to published; visible to students. | [x] |
| **FAC-07** | **Manual Grading** | `POST /api/v1/assessments/evaluations/grade` | Subjective criterion awarded score and faculty feedback. | [x] |
| **FAC-08** | **Review Analytics** | `GET /api/v1/analytics/course/{id}`| Question-level difficulty, discrimination index, and class average. | [x] |
| **FAC-09** | **Issue Intervention**| `POST /api/v1/interventions/create` | Remedial assignment dispatched to struggling students. | [x] |
| **FAC-10** | **Faculty AI Copilot**| `POST /api/v1/ai/copilot/lesson-plan` | Copilot generates suggested lesson plan based on syllabus. | [x] |

---

## 4. Test Journey 3: HOD (Head of Department) Workflow

| Step | Action | Endpoint / Interface | Expected Result | Verified |
| :--- | :--- | :--- | :--- | :--- |
| **HOD-01** | **HOD Login** | `POST /api/v1/auth/login` | Access granted to department analytics workspace. | [x] |
| **HOD-02** | **Department Metrics**| `GET /api/v1/hod/analytics/department` | Department-wide pass rates, credit completions, cohort stats. | [x] |
| **HOD-03** | **Course Comparisons**| `GET /api/v1/hod/analytics/courses` | Side-by-side performance comparison across all department courses. | [x] |
| **HOD-04** | **Privacy Suppression**| `GET /api/v1/hod/analytics/anonymized` | Cohorts < 5 students automatically masked for FERPA compliance. | [x] |
| **HOD-05** | **Curriculum Audit** | `GET /api/v1/hod/curriculum/coverage` | AICTE / NBA syllabus coverage matrix validated. | [x] |

---

## 5. Test Journey 4: Placement Officer Workflow

| Step | Action | Endpoint / Interface | Expected Result | Verified |
| :--- | :--- | :--- | :--- | :--- |
| **PLC-01** | **Placement Login** | `POST /api/v1/auth/login` | Access granted to career intelligence console. | [x] |
| **PLC-02** | **Cohort Readiness** | `GET /api/v1/career/cohort-readiness` | Quantified placement readiness score computed across batch. | [x] |
| **PLC-03** | **Skill Gap Analysis**| `GET /api/v1/career/skill-gaps` | Market job requirement vs student mastery discrepancy report. | [x] |
| **PLC-04** | **Career Path Mapping**| `GET /api/v1/career/trajectories` | Industry role skill mappings (e.g., SDE, ML Engineer, DevOps). | [x] |
| **PLC-05** | **Verified Portfolios**| `GET /api/v1/portfolio/verified-list` | List of student GitHub-verified projects and validated resumes. | [x] |

---

## 6. Test Journey 5: Institution Administrator Workflow

| Step | Action | Endpoint / Interface | Expected Result | Verified |
| :--- | :--- | :--- | :--- | :--- |
| **ADM-01** | **Admin Login** | `POST /api/v1/auth/login` | Access granted to root institutional administration. | [x] |
| **ADM-02** | **Tenant Structure** | `GET /api/v1/academic/departments` | Full institutional hierarchy inspected. | [x] |
| **ADM-03** | **User Management** | `GET /api/v1/admin/users` | Multi-role user accounts managed; sessions revokable. | [x] |
| **ADM-04** | **System Operations** | `GET /api/v1/health/ready` | Status of DB, Redis, workers, storage, AI, and sandbox probed. | [x] |
| **ADM-05** | **AI Observability** | `GET /api/v1/admin/ai/usage` | Token consumption, latency, and cost bounds audited. | [x] |
| **ADM-06** | **Security Audit Log**| `GET /api/v1/audit/logs` | Immutable audit log of all administrative and auth events. | [x] |

---

## 7. Staging Verification Sign-Off

Upon successful completion of all 5 journeys with **zero errors and zero schema warnings**, the staging release is officially certified for production promotion.
