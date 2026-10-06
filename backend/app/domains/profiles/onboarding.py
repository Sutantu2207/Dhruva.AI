"""Bulk Onboarding and Importer Engine for Students and Faculty.

Includes:
- Protection against CSV Formula Injection (=, +, -, @, tab, cr)
- Duplicate detection
- Idempotency
- Validation against institutional scope (institution, department, program, batch, section)
- Dry-run validation support
- Audit logging via OnboardingImportJob
"""

import csv
import io
import re
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import UserRole, get_password_hash
from app.domains.identity.models import User
from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    Batch,
    Section,
    StudentAcademicProfile,
    TeacherAcademicProfile,
)
from app.domains.profiles.models import (
    OnboardingImportJob,
    StudentProfileDetail,
    TeacherProfileDetail,
    StudentAcademicStatusHistory,
)
from app.domains.profiles.audit import record_audit_log


DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_cell(value: Any) -> str:
    """Sanitizes text value against CSV formula injection attacks."""
    if value is None:
        return ""
    text = str(value).strip()
    if text.startswith(DANGEROUS_FORMULA_PREFIXES):
        # Escape leading trigger characters
        text = "'" + text
    return text


def parse_csv_content(content_str: str) -> List[Dict[str, str]]:
    """Safely parses CSV text into normalized list of dictionaries."""
    f = io.StringIO(content_str.strip())
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        return []
    
    rows: List[Dict[str, str]] = []
    for row in reader:
        cleaned_row = {}
        for k, v in row.items():
            if k is not None:
                clean_k = k.strip().lower()
                clean_v = sanitize_csv_cell(v)
                cleaned_row[clean_k] = clean_v
        rows.append(cleaned_row)
    return rows


class OnboardingEngine:
    """Production onboarding engine validating and executing student and faculty bulk ingestion."""

    @staticmethod
    async def import_students(
        db: AsyncSession,
        admin_user: User,
        records: List[Dict[str, Any]],
        file_name: str,
        is_dry_run: bool = False,
    ) -> OnboardingImportJob:
        """Processes and optionally commits student batch ingestion."""
        institution_id = admin_user.institution_id
        if not institution_id and admin_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator must belong to an institution to onboard students.",
            )

        job = OnboardingImportJob(
            institution_id=institution_id or "global",
            import_type="students",
            initiated_by_user_id=admin_user.id,
            file_name=file_name,
            is_dry_run=is_dry_run,
            status="pending",
            total_records=len(records),
            successful_records=0,
            duplicate_records=0,
            failed_records=0,
            errors=[],
        )
        db.add(job)
        await db.flush()

        errors: List[Dict[str, Any]] = []
        successful_count = 0
        duplicate_count = 0
        failed_count = 0

        # Pre-load institution programs and batches for quick validation
        inst_target_id = institution_id

        for idx, rec in enumerate(records):
            row_num = idx + 1
            email = str(rec.get("email", "")).strip().lower()
            first_name = str(rec.get("first_name", "")).strip()
            last_name = str(rec.get("last_name", "")).strip()
            enrollment_number = str(rec.get("enrollment_number", "")).strip()
            program_code = str(rec.get("program_code", "")).strip().upper()
            batch_name = str(rec.get("batch_name", "")).strip()
            section_name = str(rec.get("section_name", "")).strip().upper() if rec.get("section_name") else None
            admission_year = rec.get("admission_year")
            graduation_year = rec.get("graduation_year")

            # Check cross-institution security violation
            row_inst = rec.get("institution_id")
            if row_inst and inst_target_id and row_inst != inst_target_id:
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "enrollment_number": enrollment_number,
                    "error": f"Cross-institution record rejected: row specifies institution '{row_inst}'."
                })
                continue

            # Validation
            if not email or not first_name or not last_name or not enrollment_number:
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "enrollment_number": enrollment_number,
                    "error": "Missing required fields (email, first_name, last_name, enrollment_number)."
                })
                continue

            # Check email regex
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "email": email,
                    "error": "Invalid email address format."
                })
                continue

            # Resolve program via department
            stmt_prog = (
                select(Program)
                .join(Department, Department.id == Program.department_id)
                .where(
                    Department.institution_id == inst_target_id,
                    Program.code == program_code,
                )
            )
            prog_res = await db.execute(stmt_prog)
            program = prog_res.scalar_one_or_none()
            if not program:
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "program_code": program_code,
                    "error": f"Program code '{program_code}' not found for institution."
                })
                continue

            # Resolve batch
            stmt_batch = select(Batch).where(
                Batch.program_id == program.id,
                Batch.label == batch_name,
            )
            batch_res = await db.execute(stmt_batch)
            batch = batch_res.scalar_one_or_none()
            if not batch:
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "batch_name": batch_name,
                    "error": f"Batch '{batch_name}' not found for program."
                })
                continue

            # Resolve section if given
            section_id = None
            if section_name:
                stmt_sec = select(Section).where(
                    Section.batch_id == batch.id,
                    Section.name == section_name,
                )
                sec_res = await db.execute(stmt_sec)
                sec = sec_res.scalar_one_or_none()
                if sec:
                    section_id = sec.id
                else:
                    failed_count += 1
                    errors.append({
                        "row": row_num,
                        "section_name": section_name,
                        "error": f"Section '{section_name}' not found for batch '{batch_name}'."
                    })
                    continue

            # Check existing user / duplicate
            stmt_user = select(User).where(User.normalized_email == email)
            user_exists = (await db.execute(stmt_user)).scalar_one_or_none()

            stmt_enr = select(StudentAcademicProfile).where(
                StudentAcademicProfile.institution_id == inst_target_id,
                StudentAcademicProfile.enrollment_number == enrollment_number,
            )
            enr_exists = (await db.execute(stmt_enr)).scalar_one_or_none()

            if user_exists or enr_exists:
                duplicate_count += 1
                # Idempotent skip or error reporting
                errors.append({
                    "row": row_num,
                    "email": email,
                    "enrollment_number": enrollment_number,
                    "warning": "Duplicate student record or enrollment number already exists."
                })
                continue

            # Parse years with fallback
            cur_year = datetime.now().year
            adm_yr = int(admission_year) if admission_year else cur_year
            grad_yr = int(graduation_year) if graduation_year else (adm_yr + 4)

            if not is_dry_run:
                # Create User
                new_user = User(
                    email=email,
                    normalized_email=email,
                    hashed_password=get_password_hash("Dhruva@123"),  # Safe initial default to reset
                    role=UserRole.STUDENT,
                    first_name=first_name,
                    last_name=last_name,
                    display_name=f"{first_name} {last_name}",
                    institution_id=inst_target_id,
                    is_active=True,
                    is_verified=True,
                )
                db.add(new_user)
                await db.flush()

                # Create StudentAcademicProfile
                academic_profile = StudentAcademicProfile(
                    user_id=new_user.id,
                    institution_id=inst_target_id,
                    program_id=program.id,
                    batch_id=batch.id,
                    current_section_id=section_id,
                    enrollment_number=enrollment_number,
                    admission_year=adm_yr,
                    graduation_year=grad_yr,
                    academic_status="active",
                )
                db.add(academic_profile)
                await db.flush()

                # Create initial detail & status history
                profile_detail = StudentProfileDetail(student_profile_id=academic_profile.id)
                db.add(profile_detail)

                status_hist = StudentAcademicStatusHistory(
                    student_profile_id=academic_profile.id,
                    old_status="none",
                    new_status="active",
                    effective_from=date.today(),
                    reason="Initial bulk onboarding import",
                    changed_by_user_id=admin_user.id,
                )
                db.add(status_hist)

            successful_count += 1

        job.successful_records = successful_count
        job.duplicate_records = duplicate_count
        job.failed_records = failed_count
        job.errors = errors
        job.status = "completed" if failed_count == 0 else ("partial_failure" if successful_count > 0 else "failed")
        job.completed_at = datetime.now(timezone.utc)

        await record_audit_log(
            db=db,
            actor_user_id=admin_user.id,
            action="bulk_onboard_students",
            resource_type="onboarding_import_jobs",
            resource_id=job.id,
            institution_id=institution_id,
            metadata_payload={
                "file_name": file_name,
                "is_dry_run": is_dry_run,
                "total": len(records),
                "successful": successful_count,
                "duplicates": duplicate_count,
                "failed": failed_count,
            }
        )

        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def import_faculty(
        db: AsyncSession,
        admin_user: User,
        records: List[Dict[str, Any]],
        file_name: str,
        is_dry_run: bool = False,
    ) -> OnboardingImportJob:
        """Processes and optionally commits faculty batch ingestion."""
        institution_id = admin_user.institution_id
        if not institution_id and admin_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator must belong to an institution to onboard faculty.",
            )

        job = OnboardingImportJob(
            institution_id=institution_id or "global",
            import_type="faculty",
            initiated_by_user_id=admin_user.id,
            file_name=file_name,
            is_dry_run=is_dry_run,
            status="pending",
            total_records=len(records),
            successful_records=0,
            duplicate_records=0,
            failed_records=0,
            errors=[],
        )
        db.add(job)
        await db.flush()

        errors: List[Dict[str, Any]] = []
        successful_count = 0
        duplicate_count = 0
        failed_count = 0

        inst_target_id = institution_id

        for idx, rec in enumerate(records):
            row_num = idx + 1
            email = str(rec.get("email", "")).strip().lower()
            first_name = str(rec.get("first_name", "")).strip()
            last_name = str(rec.get("last_name", "")).strip()
            employee_id = str(rec.get("employee_id", "")).strip()
            department_code = str(rec.get("department_code", "")).strip().upper()
            designation = str(rec.get("designation", "Assistant Professor")).strip()

            # Cross-institution check
            row_inst = rec.get("institution_id")
            if row_inst and inst_target_id and row_inst != inst_target_id:
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "employee_id": employee_id,
                    "error": f"Cross-institution record rejected: row specifies institution '{row_inst}'."
                })
                continue

            # Validation
            if not email or not first_name or not last_name or not employee_id or not department_code:
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "employee_id": employee_id,
                    "error": "Missing required fields (email, first_name, last_name, employee_id, department_code)."
                })
                continue

            # Check email regex
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "email": email,
                    "error": "Invalid email address format."
                })
                continue

            # Resolve department
            stmt_dept = select(Department).where(
                Department.institution_id == inst_target_id,
                Department.code == department_code,
            )
            dept_res = await db.execute(stmt_dept)
            dept = dept_res.scalar_one_or_none()
            if not dept:
                failed_count += 1
                errors.append({
                    "row": row_num,
                    "department_code": department_code,
                    "error": f"Department code '{department_code}' not found for institution."
                })
                continue

            # Duplicate check
            stmt_user = select(User).where(User.normalized_email == email)
            user_exists = (await db.execute(stmt_user)).scalar_one_or_none()

            stmt_fac = select(TeacherAcademicProfile).where(
                TeacherAcademicProfile.institution_id == inst_target_id,
                TeacherAcademicProfile.employee_id == employee_id,
            )
            fac_exists = (await db.execute(stmt_fac)).scalar_one_or_none()

            if user_exists or fac_exists:
                duplicate_count += 1
                errors.append({
                    "row": row_num,
                    "email": email,
                    "employee_id": employee_id,
                    "warning": "Duplicate faculty email or employee ID already exists."
                })
                continue

            if not is_dry_run:
                # Create User
                new_user = User(
                    email=email,
                    normalized_email=email,
                    hashed_password=get_password_hash("Dhruva@123"),
                    role=UserRole.TEACHER,
                    first_name=first_name,
                    last_name=last_name,
                    display_name=f"{first_name} {last_name}",
                    institution_id=inst_target_id,
                    is_active=True,
                    is_verified=True,
                )
                db.add(new_user)
                await db.flush()

                # Create TeacherAcademicProfile
                teacher_profile = TeacherAcademicProfile(
                    user_id=new_user.id,
                    institution_id=inst_target_id,
                    department_id=dept.id,
                    designation=designation or "Assistant Professor",
                    employee_id=employee_id,
                    status="active",
                )
                db.add(teacher_profile)
                await db.flush()

                # Create TeacherProfileDetail
                teacher_detail = TeacherProfileDetail(
                    teacher_profile_id=teacher_profile.id,
                )
                db.add(teacher_detail)

            successful_count += 1

        job.successful_records = successful_count
        job.duplicate_records = duplicate_count
        job.failed_records = failed_count
        job.errors = errors
        job.status = "completed" if failed_count == 0 else ("partial_failure" if successful_count > 0 else "failed")
        job.completed_at = datetime.now(timezone.utc)

        await record_audit_log(
            db=db,
            actor_user_id=admin_user.id,
            action="bulk_onboard_faculty",
            resource_type="onboarding_import_jobs",
            resource_id=job.id,
            institution_id=institution_id,
            metadata_payload={
                "file_name": file_name,
                "is_dry_run": is_dry_run,
                "total": len(records),
                "successful": successful_count,
                "duplicates": duplicate_count,
                "failed": failed_count,
            }
        )

        await db.commit()
        await db.refresh(job)
        return job
