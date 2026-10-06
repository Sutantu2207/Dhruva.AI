"""Faculty Grading Workflow Service managing grading queue, manual evaluations, and regrades."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.assessment.models import (
    AssessmentEvaluation,
    AssessmentAttempt,
    ManualEvaluation,
    RubricCriterion,
)
from app.domains.profiles.models import (
    StudentProject,
)
from app.domains.project_intelligence.models import (
    ProjectEvidence,
    ProjectReview,
)
from app.domains.institutional_intelligence.models import EvaluationRegradeAudit
from app.domains.academic.models import (
    TeacherAcademicProfile,
    TeachingAssignment,
    CourseOffering,
    StudentEnrollment,
    StudentAcademicProfile,
)


class GradingWorkflowService:
    """Manages faculty manual grading queue, rubric scoring, and immutable evaluation adjustments."""

    @classmethod
    async def get_faculty_grading_queue(
        cls,
        db: AsyncSession,
        user: User,
        *,
        offering_id: Optional[str] = None,
        item_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves pending grading items strictly scoped to faculty authorization."""
        if user.role not in (UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors and academic administrators can access the grading queue.",
            )

        queue_items: List[Dict[str, Any]] = []

        # Find authorized offerings if TEACHER
        authorized_offering_ids: Optional[List[str]] = None
        if user.role == UserRole.TEACHER:
            teacher_prof_res = await db.execute(
                select(TeacherAcademicProfile).where(TeacherAcademicProfile.user_id == user.id)
            )
            teacher_prof = teacher_prof_res.scalar_one_or_none()
            if not teacher_prof:
                return []

            assignments_res = await db.execute(
                select(TeachingAssignment.course_offering_id).where(
                    TeachingAssignment.teacher_profile_id == teacher_prof.id,
                    TeachingAssignment.status == "active",
                )
            )
            authorized_offering_ids = [row[0] for row in assignments_res.all()]
            if offering_id and offering_id not in authorized_offering_ids:
                return []
            if offering_id:
                authorized_offering_ids = [offering_id]
        elif offering_id:
            authorized_offering_ids = [offering_id]

        # 1. Pending Assessment Manual Evaluations
        if not item_type or item_type == "manual_question":
            stmt = (
                select(AssessmentEvaluation, AssessmentAttempt, StudentAcademicProfile, User)
                .join(AssessmentAttempt, AssessmentEvaluation.attempt_id == AssessmentAttempt.id)
                .join(StudentAcademicProfile, AssessmentAttempt.student_profile_id == StudentAcademicProfile.id)
                .join(User, StudentAcademicProfile.user_id == User.id)
                .where(
                    AssessmentEvaluation.evaluation_type.in_(["manual", "ai_proposed"]),
                    AssessmentAttempt.status.in_(["submitted", "under_evaluation"]),
                )
            )
            evals = (await db.execute(stmt)).all()
            for eval_row, attempt, student_prof, student_user in evals:
                queue_items.append({
                    "item_id": eval_row.id,
                    "item_type": "manual_question",
                    "priority": "high",
                    "title": f"Manual Evaluation for Attempt #{attempt.attempt_number}",
                    "student_profile_id": student_prof.id,
                    "student_name": f"{student_user.first_name} {student_user.last_name}",
                    "enrollment_number": student_prof.enrollment_number,
                    "course_offering_id": None,
                    "course_code": None,
                    "course_title": None,
                    "submitted_at": attempt.submitted_at or attempt.updated_at,
                    "status": "pending",
                    "metadata_json": {
                        "attempt_id": attempt.id,
                        "question_version_id": eval_row.question_version_id,
                        "max_marks": float(eval_row.max_marks),
                    },
                })

        # 2. Pending Project Evidence Items
        if not item_type or item_type == "evidence_verification":
            evidence_stmt = (
                select(ProjectEvidence, StudentProject, StudentAcademicProfile, User)
                .join(StudentProject, ProjectEvidence.project_id == StudentProject.id)
                .join(StudentAcademicProfile, ProjectEvidence.student_profile_id == StudentAcademicProfile.id)
                .join(User, StudentAcademicProfile.user_id == User.id)
                .where(
                    ProjectEvidence.verification_status.in_(["submitted", "under_review"]),
                )
            )
            evidence_rows = (await db.execute(evidence_stmt)).all()
            for ev, proj, student_prof, student_user in evidence_rows:
                queue_items.append({
                    "item_id": ev.id,
                    "item_type": "evidence_verification",
                    "priority": "medium",
                    "title": f"Verify Artifact: {ev.title} ({ev.evidence_type})",
                    "student_profile_id": student_prof.id,
                    "student_name": f"{student_user.first_name} {student_user.last_name}",
                    "enrollment_number": student_prof.enrollment_number,
                    "course_offering_id": None,
                    "course_code": None,
                    "course_title": None,
                    "submitted_at": ev.submitted_at,
                    "status": ev.verification_status,
                    "metadata_json": {
                        "project_id": proj.id,
                        "project_title": proj.title,
                        "source": ev.source,
                        "source_reference": ev.source_reference,
                    },
                })

        # 3. Pending Project Reviews
        if not item_type or item_type == "project_review":
            proj_stmt = (
                select(StudentProject, StudentAcademicProfile, User)
                .join(StudentAcademicProfile, StudentProject.student_profile_id == StudentAcademicProfile.id)
                .join(User, StudentAcademicProfile.user_id == User.id)
                .where(
                    StudentProject.verification_status.in_(["submitted", "under_review"]),
                )
            )
            proj_rows = (await db.execute(proj_stmt)).all()
            for proj, student_prof, student_user in proj_rows:
                queue_items.append({
                    "item_id": proj.id,
                    "item_type": "project_review",
                    "priority": "high",
                    "title": f"Review Capstone/Project: {proj.title}",
                    "student_profile_id": student_prof.id,
                    "student_name": f"{student_user.first_name} {student_user.last_name}",
                    "enrollment_number": student_prof.enrollment_number,
                    "course_offering_id": None,
                    "course_code": None,
                    "course_title": None,
                    "submitted_at": proj.updated_at,
                    "status": proj.verification_status,
                    "metadata_json": {
                        "project_type": proj.project_type,
                        "visibility": proj.visibility,
                    },
                })

        # Sort by submitted_at ascending (FIFO)
        queue_items.sort(key=lambda x: x["submitted_at"])
        return queue_items

    @classmethod
    async def grade_manual_question(
        cls,
        db: AsyncSession,
        evaluation_id: str,
        user: User,
        awarded_marks: Decimal,
        feedback: Optional[str] = None,
        rubric_scores: Optional[Dict[str, Decimal]] = None,
    ) -> AssessmentEvaluation:
        """Grades a manual question evaluation and recalculates attempt total."""
        if user.role not in (UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized to grade manual questions.",
            )

        res = await db.execute(
            select(AssessmentEvaluation).where(AssessmentEvaluation.id == evaluation_id)
        )
        evaluation = res.scalar_one_or_none()
        if not evaluation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation record not found.")

        if awarded_marks > evaluation.max_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Awarded marks ({awarded_marks}) cannot exceed max marks ({evaluation.max_marks}).",
            )
        if awarded_marks < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Awarded marks cannot be negative.",
            )

        evaluation.awarded_marks = awarded_marks
        evaluation.is_correct = awarded_marks > Decimal("0.00")
        evaluation.feedback = feedback
        evaluation.evaluator_id = user.id
        evaluation.evaluated_at = datetime.now(timezone.utc)

        # Store rubric breakdown if provided
        if rubric_scores:
            for criterion_id, score in rubric_scores.items():
                manual_eval = ManualEvaluation(
                    evaluation_id=evaluation.id,
                    rubric_criterion_id=criterion_id,
                    awarded_marks=score,
                    notes=feedback,
                )
                db.add(manual_eval)

        # Recalculate Attempt score
        attempt_res = await db.execute(
            select(AssessmentAttempt).where(AssessmentAttempt.id == evaluation.attempt_id)
        )
        attempt = attempt_res.scalar_one_or_none()
        if attempt:
            all_evals = (
                await db.execute(
                    select(AssessmentEvaluation).where(AssessmentEvaluation.attempt_id == attempt.id)
                )
            ).scalars().all()

            total_awarded = sum((e.awarded_marks for e in all_evals), Decimal("0.00"))
            total_max = sum((e.max_marks for e in all_evals), Decimal("0.00"))

            attempt.score = total_awarded
            if total_max > Decimal("0.00"):
                attempt.percentage = round((total_awarded / total_max) * Decimal("100.0"), 2)
            attempt.status = "evaluated"
            attempt.evaluated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(evaluation)
        return evaluation

    @classmethod
    async def regrade_evaluation(
        cls,
        db: AsyncSession,
        evaluation_id: str,
        user: User,
        new_marks: Decimal,
        reason: str,
    ) -> EvaluationRegradeAudit:
        """Applies immutable regrade with audit log recording reason and original marks."""
        if user.role not in (UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized to adjust or regrade evaluation.",
            )

        res = await db.execute(
            select(AssessmentEvaluation).where(AssessmentEvaluation.id == evaluation_id)
        )
        evaluation = res.scalar_one_or_none()
        if not evaluation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation record not found.")

        if new_marks > evaluation.max_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New marks ({new_marks}) cannot exceed max marks ({evaluation.max_marks}).",
            )
        if new_marks < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New marks cannot be negative.",
            )

        previous_marks = evaluation.awarded_marks
        evaluation.awarded_marks = new_marks
        evaluation.is_correct = new_marks > Decimal("0.00")
        evaluation.evaluator_id = user.id
        evaluation.evaluated_at = datetime.now(timezone.utc)

        audit = EvaluationRegradeAudit(
            evaluation_id=evaluation.id,
            evaluator_id=user.id,
            previous_marks=previous_marks,
            new_marks=new_marks,
            reason=reason,
        )
        db.add(audit)

        # Recalculate Attempt score
        attempt_res = await db.execute(
            select(AssessmentAttempt).where(AssessmentAttempt.id == evaluation.attempt_id)
        )
        attempt = attempt_res.scalar_one_or_none()
        if attempt:
            all_evals = (
                await db.execute(
                    select(AssessmentEvaluation).where(AssessmentEvaluation.attempt_id == attempt.id)
                )
            ).scalars().all()
            total_awarded = sum((e.awarded_marks for e in all_evals), Decimal("0.00"))
            total_max = sum((e.max_marks for e in all_evals), Decimal("0.00"))
            attempt.score = total_awarded
            if total_max > Decimal("0.00"):
                attempt.percentage = round((total_awarded / total_max) * Decimal("100.0"), 2)

        await db.commit()
        await db.refresh(audit)
        return audit
