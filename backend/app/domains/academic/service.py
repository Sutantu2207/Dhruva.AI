"""Business logic and validation service for Academic Management & Institutional Hierarchy."""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.identity.models import User
from app.core.security import UserRole
from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    AcademicYear,
    Semester,
    Batch,
    Section,
    Course,
    CourseOffering,
    StudentAcademicProfile,
    TeacherAcademicProfile,
    StudentEnrollment,
    TeachingAssignment,
)
from app.domains.academic.schemas import (
    InstitutionCreate,
    InstitutionUpdate,
    DepartmentCreate,
    ProgramCreate,
    AcademicYearCreate,
    SemesterCreate,
    BatchCreate,
    SectionCreate,
    CourseCreate,
    CourseOfferingCreate,
    StudentAcademicProfileCreate,
    StudentAcademicProfileUpdate,
    TeacherAcademicProfileCreate,
    TeacherAcademicProfileUpdate,
    StudentEnrollmentCreate,
    StudentEnrollmentUpdate,
    TeachingAssignmentCreate,
)


class AcademicService:
    """Service handling institutional hierarchy and relationship integrity."""

    # ---------------- Institutions ----------------
    async def create_institution(self, db: AsyncSession, data: InstitutionCreate) -> Institution:
        stmt = select(Institution).where(Institution.code == data.code.strip().upper())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Institution code already exists.")

        inst = Institution(
            name=data.name.strip(),
            code=data.code.strip().upper(),
            email_domains=data.email_domains,
        )
        db.add(inst)
        await db.commit()
        await db.refresh(inst)
        return inst

    async def list_institutions(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> List[Institution]:
        stmt = select(Institution).order_by(Institution.name).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_institution(self, db: AsyncSession, id: str) -> Institution:
        stmt = select(Institution).where(Institution.id == id)
        inst = (await db.execute(stmt)).scalar_one_or_none()
        if not inst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")
        return inst

    async def update_institution(self, db: AsyncSession, id: str, data: InstitutionUpdate) -> Institution:
        inst = await self.get_institution(db, id)
        if data.name is not None:
            inst.name = data.name.strip()
        if data.email_domains is not None:
            inst.email_domains = data.email_domains
        if data.status is not None:
            inst.status = data.status
        await db.commit()
        await db.refresh(inst)
        return inst

    # ---------------- Departments ----------------
    async def create_department(self, db: AsyncSession, data: DepartmentCreate) -> Department:
        await self.get_institution(db, data.institution_id)
        stmt = select(Department).where(
            Department.institution_id == data.institution_id,
            Department.code == data.code.strip().upper(),
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department code already exists in this institution.")

        dept = Department(
            institution_id=data.institution_id,
            name=data.name.strip(),
            code=data.code.strip().upper(),
        )
        db.add(dept)
        await db.commit()
        await db.refresh(dept)
        return dept

    async def list_departments(self, db: AsyncSession, institution_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Department]:
        stmt = select(Department)
        if institution_id:
            stmt = stmt.where(Department.institution_id == institution_id)
        stmt = stmt.order_by(Department.name).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_department(self, db: AsyncSession, id: str) -> Department:
        stmt = select(Department).where(Department.id == id)
        dept = (await db.execute(stmt)).scalar_one_or_none()
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
        return dept

    # ---------------- Programs ----------------
    async def create_program(self, db: AsyncSession, data: ProgramCreate) -> Program:
        dept = await self.get_department(db, data.department_id)

        stmt = select(Program).where(
            Program.department_id == data.department_id,
            Program.code == data.code.strip().upper(),
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Program code already exists in this department.")

        prog = Program(
            department_id=data.department_id,
            name=data.name.strip(),
            code=data.code.strip().upper(),
            degree_type=data.degree_type.strip(),
            duration_years=data.duration_years,
        )
        db.add(prog)
        await db.commit()
        await db.refresh(prog)
        return prog

    async def list_programs(self, db: AsyncSession, department_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Program]:
        stmt = select(Program)
        if department_id:
            stmt = stmt.where(Program.department_id == department_id)
        stmt = stmt.order_by(Program.name).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_program(self, db: AsyncSession, id: str) -> Program:
        stmt = select(Program).where(Program.id == id)
        prog = (await db.execute(stmt)).scalar_one_or_none()
        if not prog:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found.")
        return prog

    # ---------------- Academic Years ----------------
    async def create_academic_year(self, db: AsyncSession, data: AcademicYearCreate) -> AcademicYear:
        await self.get_institution(db, data.institution_id)
        if data.start_date >= data.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Academic year start_date must precede end_date.")

        stmt = select(AcademicYear).where(
            AcademicYear.institution_id == data.institution_id,
            AcademicYear.name == data.name.strip(),
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Academic year with this name already exists in this institution.")

        ay = AcademicYear(
            institution_id=data.institution_id,
            name=data.name.strip(),
            start_date=data.start_date,
            end_date=data.end_date,
        )
        db.add(ay)
        await db.commit()
        await db.refresh(ay)
        return ay

    async def list_academic_years(self, db: AsyncSession, institution_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[AcademicYear]:
        stmt = select(AcademicYear)
        if institution_id:
            stmt = stmt.where(AcademicYear.institution_id == institution_id)
        stmt = stmt.order_by(AcademicYear.start_date.desc()).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_academic_year(self, db: AsyncSession, id: str) -> AcademicYear:
        stmt = select(AcademicYear).where(AcademicYear.id == id)
        ay = (await db.execute(stmt)).scalar_one_or_none()
        if not ay:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found.")
        return ay

    # ---------------- Semesters ----------------
    async def create_semester(self, db: AsyncSession, data: SemesterCreate) -> Semester:
        await self.get_academic_year(db, data.academic_year_id)

        if data.start_date >= data.end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Semester start_date must precede end_date.")

        stmt = select(Semester).where(
            Semester.academic_year_id == data.academic_year_id,
            Semester.semester_number == data.semester_number,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Semester number already exists for this academic year.")

        sem = Semester(
            academic_year_id=data.academic_year_id,
            semester_number=data.semester_number,
            label=data.label.strip(),
            start_date=data.start_date,
            end_date=data.end_date,
        )
        db.add(sem)
        await db.commit()
        await db.refresh(sem)
        return sem

    async def list_semesters(self, db: AsyncSession, academic_year_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Semester]:
        stmt = select(Semester)
        if academic_year_id:
            stmt = stmt.where(Semester.academic_year_id == academic_year_id)
        stmt = stmt.order_by(Semester.semester_number).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_semester(self, db: AsyncSession, id: str) -> Semester:
        stmt = select(Semester).where(Semester.id == id)
        sem = (await db.execute(stmt)).scalar_one_or_none()
        if not sem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found.")
        return sem

    # ---------------- Batches ----------------
    async def create_batch(self, db: AsyncSession, data: BatchCreate) -> Batch:
        await self.get_institution(db, data.institution_id)
        await self.get_program(db, data.program_id)

        if data.admission_year >= data.graduation_year:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch admission_year must precede graduation_year.")

        stmt = select(Batch).where(
            Batch.program_id == data.program_id,
            Batch.label == data.label.strip(),
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Batch with this label already exists for this program.")

        batch = Batch(
            institution_id=data.institution_id,
            program_id=data.program_id,
            admission_year=data.admission_year,
            graduation_year=data.graduation_year,
            label=data.label.strip(),
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        return batch

    async def list_batches(
        self, db: AsyncSession, institution_id: Optional[str] = None, program_id: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[Batch]:
        stmt = select(Batch)
        if institution_id:
            stmt = stmt.where(Batch.institution_id == institution_id)
        if program_id:
            stmt = stmt.where(Batch.program_id == program_id)
        stmt = stmt.order_by(Batch.admission_year.desc()).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_batch(self, db: AsyncSession, id: str) -> Batch:
        stmt = select(Batch).where(Batch.id == id)
        batch = (await db.execute(stmt)).scalar_one_or_none()
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")
        return batch

    # ---------------- Sections ----------------
    async def create_section(self, db: AsyncSession, data: SectionCreate) -> Section:
        await self.get_batch(db, data.batch_id)

        stmt = select(Section).where(
            Section.batch_id == data.batch_id,
            Section.name == data.name.strip().upper(),
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Section with this name already exists in this batch.")

        sec = Section(
            batch_id=data.batch_id,
            name=data.name.strip().upper(),
            capacity=data.capacity,
        )
        db.add(sec)
        await db.commit()
        await db.refresh(sec)
        return sec

    async def list_sections(self, db: AsyncSession, batch_id: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Section]:
        stmt = select(Section)
        if batch_id:
            stmt = stmt.where(Section.batch_id == batch_id)
        stmt = stmt.order_by(Section.name).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_section(self, db: AsyncSession, id: str) -> Section:
        stmt = select(Section).where(Section.id == id)
        sec = (await db.execute(stmt)).scalar_one_or_none()
        if not sec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        return sec

    # ---------------- Courses ----------------
    async def create_course(self, db: AsyncSession, data: CourseCreate) -> Course:
        await self.get_institution(db, data.institution_id)
        await self.get_department(db, data.department_id)

        stmt = select(Course).where(
            Course.institution_id == data.institution_id,
            Course.code == data.code.strip().upper(),
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Course code already exists in this institution.")

        course = Course(
            institution_id=data.institution_id,
            department_id=data.department_id,
            code=data.code.strip().upper(),
            title=data.title.strip(),
            description=data.description,
            credits=data.credits,
            course_type=data.course_type,
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    async def list_courses(
        self, db: AsyncSession, institution_id: Optional[str] = None, department_id: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[Course]:
        stmt = select(Course)
        if institution_id:
            stmt = stmt.where(Course.institution_id == institution_id)
        if department_id:
            stmt = stmt.where(Course.department_id == department_id)
        stmt = stmt.order_by(Course.code).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_course(self, db: AsyncSession, id: str) -> Course:
        stmt = select(Course).where(Course.id == id)
        course = (await db.execute(stmt)).scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
        return course

    # ---------------- Course Offerings ----------------
    async def create_course_offering(self, db: AsyncSession, data: CourseOfferingCreate) -> CourseOffering:
        await self.get_course(db, data.course_id)
        await self.get_academic_year(db, data.academic_year_id)
        await self.get_semester(db, data.semester_id)
        await self.get_section(db, data.section_id)

        stmt = select(CourseOffering).where(
            CourseOffering.course_id == data.course_id,
            CourseOffering.academic_year_id == data.academic_year_id,
            CourseOffering.semester_id == data.semester_id,
            CourseOffering.section_id == data.section_id,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Course is already offered to this section for the specified semester.")

        offering = CourseOffering(
            course_id=data.course_id,
            academic_year_id=data.academic_year_id,
            semester_id=data.semester_id,
            section_id=data.section_id,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        db.add(offering)
        await db.commit()
        await db.refresh(offering)
        return offering

    async def list_course_offerings(
        self,
        db: AsyncSession,
        course_id: Optional[str] = None,
        academic_year_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        section_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CourseOffering]:
        stmt = select(CourseOffering)
        if course_id:
            stmt = stmt.where(CourseOffering.course_id == course_id)
        if academic_year_id:
            stmt = stmt.where(CourseOffering.academic_year_id == academic_year_id)
        if semester_id:
            stmt = stmt.where(CourseOffering.semester_id == semester_id)
        if section_id:
            stmt = stmt.where(CourseOffering.section_id == section_id)
        stmt = stmt.offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_course_offering(self, db: AsyncSession, id: str) -> CourseOffering:
        stmt = select(CourseOffering).where(CourseOffering.id == id)
        offering = (await db.execute(stmt)).scalar_one_or_none()
        if not offering:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course offering not found.")
        return offering

    # ---------------- Student Academic Profiles ----------------
    async def create_student_profile(self, db: AsyncSession, data: StudentAcademicProfileCreate) -> StudentAcademicProfile:
        stmt_user = select(User).where(User.id == data.user_id)
        user = (await db.execute(stmt_user)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")
        if user.role != UserRole.STUDENT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must possess student role to have a student academic profile.")

        stmt_exist = select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == data.user_id)
        if (await db.execute(stmt_exist)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student academic profile already exists for this user.")

        await self.get_institution(db, data.institution_id)
        await self.get_program(db, data.program_id)
        await self.get_batch(db, data.batch_id)
        if data.current_section_id:
            await self.get_section(db, data.current_section_id)

        stmt_enroll = select(StudentAcademicProfile).where(
            StudentAcademicProfile.institution_id == data.institution_id,
            StudentAcademicProfile.enrollment_number == data.enrollment_number.strip().upper(),
        )
        if (await db.execute(stmt_enroll)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Enrollment number already exists in this institution.")

        profile = StudentAcademicProfile(
            user_id=data.user_id,
            institution_id=data.institution_id,
            program_id=data.program_id,
            batch_id=data.batch_id,
            current_section_id=data.current_section_id,
            enrollment_number=data.enrollment_number.strip().upper(),
            admission_year=data.admission_year,
            graduation_year=data.graduation_year,
        )
        db.add(profile)
        if not user.institution_id:
            user.institution_id = data.institution_id

        await db.commit()
        await db.refresh(profile)
        return profile

    async def get_student_profile(self, db: AsyncSession, profile_id_or_user_id: str) -> Optional[StudentAcademicProfile]:
        stmt = select(StudentAcademicProfile).where(
            (StudentAcademicProfile.id == profile_id_or_user_id) | (StudentAcademicProfile.user_id == profile_id_or_user_id)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def update_student_profile(
        self, db: AsyncSession, user_id: str, data: StudentAcademicProfileUpdate
    ) -> StudentAcademicProfile:
        profile = await self.get_student_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student academic profile not found.")

        if data.current_section_id is not None:
            if data.current_section_id:
                await self.get_section(db, data.current_section_id)
            profile.current_section_id = data.current_section_id
        if data.academic_status is not None:
            profile.academic_status = data.academic_status
        if data.graduation_year is not None:
            profile.graduation_year = data.graduation_year

        await db.commit()
        await db.refresh(profile)
        return profile

    # ---------------- Teacher Academic Profiles ----------------
    async def create_teacher_profile(self, db: AsyncSession, data: TeacherAcademicProfileCreate) -> TeacherAcademicProfile:
        stmt_user = select(User).where(User.id == data.user_id)
        user = (await db.execute(stmt_user)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

        stmt_exist = select(TeacherAcademicProfile).where(TeacherAcademicProfile.user_id == data.user_id)
        if (await db.execute(stmt_exist)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Teacher academic profile already exists for this user.")

        await self.get_institution(db, data.institution_id)
        await self.get_department(db, data.department_id)

        stmt_emp = select(TeacherAcademicProfile).where(
            TeacherAcademicProfile.institution_id == data.institution_id,
            TeacherAcademicProfile.employee_id == data.employee_id.strip().upper(),
        )
        if (await db.execute(stmt_emp)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID already exists in this institution.")

        profile = TeacherAcademicProfile(
            user_id=data.user_id,
            institution_id=data.institution_id,
            department_id=data.department_id,
            designation=data.designation.strip(),
            employee_id=data.employee_id.strip().upper(),
        )
        db.add(profile)
        if not user.institution_id:
            user.institution_id = data.institution_id

        await db.commit()
        await db.refresh(profile)
        return profile

    async def get_teacher_profile(self, db: AsyncSession, profile_id_or_user_id: str) -> Optional[TeacherAcademicProfile]:
        stmt = select(TeacherAcademicProfile).where(
            (TeacherAcademicProfile.id == profile_id_or_user_id) | (TeacherAcademicProfile.user_id == profile_id_or_user_id)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    async def update_teacher_profile(
        self, db: AsyncSession, user_id: str, data: TeacherAcademicProfileUpdate
    ) -> TeacherAcademicProfile:
        profile = await self.get_teacher_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher academic profile not found.")

        if data.designation is not None:
            profile.designation = data.designation.strip()
        if data.status is not None:
            profile.status = data.status

        await db.commit()
        await db.refresh(profile)
        return profile

    # ---------------- Student Enrollments ----------------
    async def enroll_student(self, db: AsyncSession, data: StudentEnrollmentCreate) -> StudentEnrollment:
        stmt_sp = select(StudentAcademicProfile).where(StudentAcademicProfile.id == data.student_profile_id)
        if not (await db.execute(stmt_sp)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

        await self.get_course_offering(db, data.course_offering_id)

        stmt_dupe = select(StudentEnrollment).where(
            StudentEnrollment.student_profile_id == data.student_profile_id,
            StudentEnrollment.course_offering_id == data.course_offering_id,
        )
        if (await db.execute(stmt_dupe)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already enrolled in this course offering.")

        enrollment = StudentEnrollment(
            student_profile_id=data.student_profile_id,
            course_offering_id=data.course_offering_id,
            enrollment_status=data.enrollment_status,
        )
        db.add(enrollment)
        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    async def list_enrollments(
        self,
        db: AsyncSession,
        student_profile_id: Optional[str] = None,
        course_offering_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[StudentEnrollment]:
        stmt = select(StudentEnrollment)
        if student_profile_id:
            stmt = stmt.where(StudentEnrollment.student_profile_id == student_profile_id)
        if course_offering_id:
            stmt = stmt.where(StudentEnrollment.course_offering_id == course_offering_id)
        stmt = stmt.offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_enrollment(self, db: AsyncSession, id: str) -> StudentEnrollment:
        stmt = select(StudentEnrollment).where(StudentEnrollment.id == id)
        enrollment = (await db.execute(stmt)).scalar_one_or_none()
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found.")
        return enrollment

    async def update_enrollment(self, db: AsyncSession, id: str, data: StudentEnrollmentUpdate) -> StudentEnrollment:
        enrollment = await self.get_enrollment(db, id)
        enrollment.enrollment_status = data.enrollment_status
        await db.commit()
        await db.refresh(enrollment)
        return enrollment

    # ---------------- Teaching Assignments ----------------
    async def assign_teacher(self, db: AsyncSession, data: TeachingAssignmentCreate) -> TeachingAssignment:
        stmt_tp = select(TeacherAcademicProfile).where(TeacherAcademicProfile.id == data.teacher_profile_id)
        if not (await db.execute(stmt_tp)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher profile not found.")

        await self.get_course_offering(db, data.course_offering_id)

        stmt_dupe = select(TeachingAssignment).where(
            TeachingAssignment.teacher_profile_id == data.teacher_profile_id,
            TeachingAssignment.course_offering_id == data.course_offering_id,
            TeachingAssignment.assignment_role == data.assignment_role,
        )
        if (await db.execute(stmt_dupe)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Teacher is already assigned to this course offering with this role.")

        assignment = TeachingAssignment(
            teacher_profile_id=data.teacher_profile_id,
            course_offering_id=data.course_offering_id,
            assignment_role=data.assignment_role,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    async def list_teaching_assignments(
        self,
        db: AsyncSession,
        teacher_profile_id: Optional[str] = None,
        course_offering_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[TeachingAssignment]:
        stmt = select(TeachingAssignment)
        if teacher_profile_id:
            stmt = stmt.where(TeachingAssignment.teacher_profile_id == teacher_profile_id)
        if course_offering_id:
            stmt = stmt.where(TeachingAssignment.course_offering_id == course_offering_id)
        stmt = stmt.offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_teaching_assignment(self, db: AsyncSession, id: str) -> TeachingAssignment:
        stmt = select(TeachingAssignment).where(TeachingAssignment.id == id)
        assignment = (await db.execute(stmt)).scalar_one_or_none()
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teaching assignment not found.")
        return assignment


academic_service = AcademicService()
