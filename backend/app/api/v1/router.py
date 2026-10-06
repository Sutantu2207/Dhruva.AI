"""Root API v1 router mounting all domain endpoints."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    system,
    auth,
    academic,
    catalog,
    students,
    faculty,
    mentorship,
    interventions,
    onboarding,
    learning_content,
    assessments,
    knowledge,
    career,
    projects,
    portfolio,
    skill_graph,
    institutional_analytics,
    remediation,
    ai,
    notifications,
    admin_operations,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(academic.router)
api_router.include_router(catalog.router)
api_router.include_router(students.router)
api_router.include_router(faculty.router)
api_router.include_router(mentorship.router)
api_router.include_router(interventions.router)
api_router.include_router(onboarding.router)

# Domain 4: Course Delivery, Curriculum Structure & Learning Content Engine
api_router.include_router(learning_content.courses_router)
api_router.include_router(learning_content.curriculum_router)
api_router.include_router(learning_content.modules_router)
api_router.include_router(learning_content.lessons_router)
api_router.include_router(learning_content.concepts_router)
api_router.include_router(learning_content.resources_router)
api_router.include_router(learning_content.learning_router)
api_router.include_router(learning_content.bookmarks_router)
api_router.include_router(learning_content.notes_router)
api_router.include_router(learning_content.review_router)

# Domain 5: Assessment Engine, Question Banks, Evaluation & Deterministic Evidence
api_router.include_router(assessments.router)

# Domain 6: Knowledge State, Concept Mastery Engine & Spaced Repetition
api_router.include_router(knowledge.router)

# Domain 7: Skill Intelligence, Career Trajectories & Placement Readiness Engine
api_router.include_router(career.router)

# Domain 8: Project Intelligence, Portfolio Engine & Skill Evidence Graph
api_router.include_router(projects.router)
api_router.include_router(portfolio.router)
api_router.include_router(skill_graph.router)

# Domain 9: Institutional Analytics, Faculty Grading Workflows & Departmental Intelligence
api_router.include_router(institutional_analytics.router)

# Domain 10: Autonomous Adaptive Remediation & Institutional Intelligence Closing
api_router.include_router(remediation.router)

# Domain 11: System-wide AI Orchestration & Natural Language Explanation Layer
api_router.include_router(ai.router)

# Domain 12: Production Readiness, Operations, Notifications & Observability
api_router.include_router(notifications.router)
api_router.include_router(admin_operations.router)


