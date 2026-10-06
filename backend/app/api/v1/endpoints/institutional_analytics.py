"""REST API endpoints for Institutional Analytics, Faculty Grading, and Departmental Intelligence."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.institutional_intelligence.schemas import (
    FacultyDashboardAnalytics,
    CourseOfferingAnalyticsResponse,
    GradingQueueItem,
    ManualGradingSubmission,
    RegradeSubmission,
    DepartmentAnalyticsResponse,
    DepartmentComparisonResponse,
    PlacementOfficerAnalyticsResponse,
    InterventionSignalResponse,
    AcknowledgeSignalPayload,
    DismissSignalPayload,
    ConvertSignalToInterventionPayload,
)
from app.domains.institutional_intelligence.service import InstitutionalIntelligenceService
from app.domains.institutional_intelligence.grading_workflow_service import GradingWorkflowService

router = APIRouter(tags=["Institutional Intelligence & Analytics"])


# -------------------------------------------------------------------------
# 1. Faculty Dashboard & Course Offering Analytics
# -------------------------------------------------------------------------

@router.get("/faculty/dashboard-analytics", response_model=FacultyDashboardAnalytics)
async def get_faculty_dashboard_analytics(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve holistic dashboard analytics strictly for faculty assigned scope."""
    return await InstitutionalIntelligenceService.get_faculty_dashboard(db, current_user)


@router.get("/faculty/courses/{offering_id}/analytics", response_model=CourseOfferingAnalyticsResponse)
async def get_course_offering_analytics(
    offering_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Drill-down analytics for a specific Course Offering."""
    return await InstitutionalIntelligenceService.get_course_offering_analytics(db, offering_id, current_user)


@router.get("/faculty/courses/{offering_id}/export")
async def export_course_offering_csv(
    offering_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Export authentic course performance metrics as CSV."""
    csv_data = await InstitutionalIntelligenceService.export_course_performance_csv(db, offering_id, current_user)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=course_{offering_id}_analytics.csv"},
    )


# -------------------------------------------------------------------------
# 2. Faculty Grading Queue & Rubric Workflows
# -------------------------------------------------------------------------

@router.get("/faculty/grading", response_model=List[GradingQueueItem])
async def get_grading_queue(
    offering_id: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve pending manual evaluations, project reviews, and evidence verifications."""
    return await GradingWorkflowService.get_faculty_grading_queue(
        db, current_user, offering_id=offering_id, item_type=item_type
    )


@router.post("/faculty/grading/questions/{evaluation_id}")
async def grade_manual_question(
    evaluation_id: str,
    payload: ManualGradingSubmission,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Grades a manual question evaluation and recalculates attempt total deterministically."""
    ev = await GradingWorkflowService.grade_manual_question(
        db,
        evaluation_id=evaluation_id,
        user=current_user,
        awarded_marks=payload.awarded_marks,
        feedback=payload.feedback,
        rubric_scores=payload.rubric_scores,
    )
    return {
        "status": "graded",
        "evaluation_id": ev.id,
        "awarded_marks": float(ev.awarded_marks),
        "is_correct": ev.is_correct,
        "evaluated_at": ev.evaluated_at,
    }


@router.post("/faculty/grading/questions/{evaluation_id}/regrade")
async def regrade_manual_question(
    evaluation_id: str,
    payload: RegradeSubmission,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Applies immutable regrade with audit log recording reason and original marks."""
    audit = await GradingWorkflowService.regrade_evaluation(
        db,
        evaluation_id=evaluation_id,
        user=current_user,
        new_marks=payload.new_marks,
        reason=payload.reason,
    )
    return {
        "status": "regraded",
        "audit_id": audit.id,
        "previous_marks": float(audit.previous_marks),
        "new_marks": float(audit.new_marks),
        "reason": audit.reason,
        "regraded_at": audit.regraded_at,
    }


# -------------------------------------------------------------------------
# 3. Department Analytics (HOD) & Institutional Comparisons
# -------------------------------------------------------------------------

@router.get("/hod/departments/{department_id}/analytics", response_model=DepartmentAnalyticsResponse)
async def get_department_analytics(
    department_id: str,
    current_user: User = Depends(require_roles(UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve department-scoped intelligence. HOD is strictly restricted to own department."""
    return await InstitutionalIntelligenceService.get_department_analytics(db, department_id, current_user)


@router.get("/admin/departments/compare", response_model=DepartmentComparisonResponse)
async def compare_departments(
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Compare academic performance across departments with privacy suppression for small cohorts (< 3)."""
    inst_id = current_user.institution_id
    if not inst_id and current_user.role == UserRole.SUPER_ADMIN:
        # Fallback to first active institution if super admin without explicit inst
        inst = (await db.execute(select(Institution).limit(1))).scalar_one_or_none()
        inst_id = inst.id if inst else "default"

    return await InstitutionalIntelligenceService.get_department_comparisons(db, inst_id, current_user)


# -------------------------------------------------------------------------
# 4. Placement Officer Intelligence
# -------------------------------------------------------------------------

@router.get("/placement/analytics", response_model=PlacementOfficerAnalyticsResponse)
async def get_placement_analytics(
    current_user: User = Depends(require_roles(UserRole.PLACEMENT_OFFICER, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve institution-scoped employability, career readiness, and systemic skill gap intelligence."""
    inst_id = current_user.institution_id
    if not inst_id and current_user.role == UserRole.SUPER_ADMIN:
        inst = (await db.execute(select(Institution).limit(1))).scalar_one_or_none()
        inst_id = inst.id if inst else "default"

    return await InstitutionalIntelligenceService.get_placement_analytics(db, inst_id, current_user)


# -------------------------------------------------------------------------
# 5. Early Intervention Signals Lifecycle
# -------------------------------------------------------------------------

@router.post("/interventions/signals/scan", response_model=List[InterventionSignalResponse])
async def scan_intervention_signals(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Run deterministic InterventionSignalEngine scan across student populations."""
    inst_id = current_user.institution_id
    if not inst_id and current_user.role == UserRole.SUPER_ADMIN:
        inst = (await db.execute(select(Institution).limit(1))).scalar_one_or_none()
        inst_id = inst.id if inst else "default"

    signals = await InstitutionalIntelligenceService.scan_and_generate_signals(db, inst_id, current_user)
    return signals


@router.post("/interventions/signals/{signal_id}/acknowledge", response_model=InterventionSignalResponse)
async def acknowledge_signal(
    signal_id: str,
    payload: AcknowledgeSignalPayload,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an academic support signal."""
    return await InstitutionalIntelligenceService.acknowledge_signal(db, signal_id, current_user)


@router.post("/interventions/signals/{signal_id}/dismiss", response_model=InterventionSignalResponse)
async def dismiss_signal(
    signal_id: str,
    payload: DismissSignalPayload,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an academic support signal with an auditable reason."""
    return await InstitutionalIntelligenceService.dismiss_signal(db, signal_id, payload.reason, current_user)


@router.post("/interventions/signals/{signal_id}/convert", response_model=InterventionSignalResponse)
async def convert_signal_to_intervention(
    signal_id: str,
    payload: ConvertSignalToInterventionPayload,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Elevate an academic signal into a formal StudentIntervention record."""
    return await InstitutionalIntelligenceService.convert_signal_to_intervention(
        db,
        signal_id=signal_id,
        category=payload.category,
        priority=payload.priority,
        user=current_user,
        action_plan=payload.action_plan,
        follow_up_date=payload.follow_up_date,
    )
