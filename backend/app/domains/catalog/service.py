"""Service layer for National Academic Taxonomy & India-Wide Academic Catalog (Domain 2.5)."""

import re
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalog.models import (
    AcademicCatalogSource,
    AcademicCatalogVersion,
    AcademicDiscipline,
    DegreeType,
    ProgramCatalog,
    ProgramSpecialization,
    CourseCatalog,
    SkillCatalog,
    CareerCatalog,
    ProgramSkillMapping,
    CourseSkillMapping,
    CareerSkillMapping,
    ProgramCareerMapping,
    InstitutionProgramMapping,
    InstitutionCourseMapping,
    CatalogImportJob,
)
from app.domains.catalog.schemas import (
    AcademicCatalogSourceCreate,
    AcademicCatalogVersionCreate,
    AcademicDisciplineCreate,
    AcademicDisciplineUpdate,
    DegreeTypeCreate,
    ProgramCatalogCreate,
    ProgramCatalogUpdate,
    ProgramSpecializationCreate,
    CourseCatalogCreate,
    CourseCatalogUpdate,
    SkillCatalogCreate,
    CareerCatalogCreate,
    ProgramSkillMappingCreate,
    CourseSkillMappingCreate,
    CareerSkillMappingCreate,
    ProgramCareerMappingCreate,
    InstitutionProgramMappingCreate,
    InstitutionCourseMappingCreate,
)
from app.domains.academic.models import Institution, Department, Program as LocalProgram, Course as LocalCourse


def slugify(text: str) -> str:
    """Generate a clean URL/lookup slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")


class AcademicCatalogService:
    """Core domain service for National Academic Catalog operations."""

    # ---------------- Sources & Versions ----------------
    async def create_source(self, db: AsyncSession, data: AcademicCatalogSourceCreate) -> AcademicCatalogSource:
        stmt = select(AcademicCatalogSource).where(AcademicCatalogSource.code == data.code.strip().upper())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Source code already exists.")

        source = AcademicCatalogSource(
            code=data.code.strip().upper(),
            name=data.name.strip(),
            organization=data.organization.strip(),
            website_url=data.website_url,
            is_authoritative=data.is_authoritative,
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        return source

    async def list_sources(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> List[AcademicCatalogSource]:
        stmt = select(AcademicCatalogSource).order_by(AcademicCatalogSource.code).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def create_version(self, db: AsyncSession, data: AcademicCatalogVersionCreate) -> AcademicCatalogVersion:
        stmt = select(AcademicCatalogVersion).where(AcademicCatalogVersion.version_tag == data.version_tag.strip())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Catalog version tag already exists.")

        version = AcademicCatalogVersion(
            version_tag=data.version_tag.strip(),
            source_id=data.source_id,
            status=data.status,
            effective_date=data.effective_date,
            notes=data.notes,
        )
        db.add(version)
        await db.commit()
        await db.refresh(version)
        return version

    async def list_versions(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> List[AcademicCatalogVersion]:
        stmt = select(AcademicCatalogVersion).order_by(AcademicCatalogVersion.effective_date.desc()).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    # ---------------- Disciplines ----------------
    async def create_discipline(self, db: AsyncSession, data: AcademicDisciplineCreate) -> AcademicDiscipline:
        stmt = select(AcademicDiscipline).where(AcademicDiscipline.code == data.code.strip().upper())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Discipline code already exists.")

        slug = slugify(data.name)
        # Ensure unique slug
        slug_stmt = select(AcademicDiscipline).where(AcademicDiscipline.slug == slug)
        if (await db.execute(slug_stmt)).scalar_one_or_none():
            slug = f"{slug}-{data.code.strip().lower()}"

        discipline = AcademicDiscipline(
            code=data.code.strip().upper(),
            name=data.name.strip(),
            display_name=data.display_name.strip(),
            slug=slug,
            description=data.description,
            aliases=data.aliases or [],
            status=data.status,
            version_id=data.version_id,
            source_id=data.source_id,
        )
        db.add(discipline)
        await db.commit()
        await db.refresh(discipline)
        return discipline

    async def list_disciplines(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> List[AcademicDiscipline]:
        stmt = select(AcademicDiscipline).order_by(AcademicDiscipline.name).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_discipline(self, db: AsyncSession, id_or_code: str) -> AcademicDiscipline:
        stmt = select(AcademicDiscipline).where(
            (AcademicDiscipline.id == id_or_code) | (AcademicDiscipline.code == id_or_code.upper())
        )
        discipline = (await db.execute(stmt)).scalar_one_or_none()
        if not discipline:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic discipline not found.")
        return discipline

    # ---------------- Degree Types ----------------
    async def create_degree_type(self, db: AsyncSession, data: DegreeTypeCreate) -> DegreeType:
        stmt = select(DegreeType).where(DegreeType.code == data.code.strip().upper())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Degree type code already exists.")

        deg = DegreeType(
            code=data.code.strip().upper(),
            name=data.name.strip(),
            short_name=data.short_name.strip(),
            level=data.level,
            typical_duration_years=data.typical_duration_years,
            status=data.status,
        )
        db.add(deg)
        await db.commit()
        await db.refresh(deg)
        return deg

    async def list_degree_types(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> List[DegreeType]:
        stmt = select(DegreeType).order_by(DegreeType.level).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    # ---------------- Programs & Specializations ----------------
    async def create_program(self, db: AsyncSession, data: ProgramCatalogCreate) -> ProgramCatalog:
        stmt = select(ProgramCatalog).where(ProgramCatalog.code == data.code.strip().upper())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="National program code already exists.")

        # Validate discipline and degree type
        disc_stmt = select(AcademicDiscipline).where(AcademicDiscipline.id == data.discipline_id)
        if not (await db.execute(disc_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic discipline not found.")

        deg_stmt = select(DegreeType).where(DegreeType.id == data.degree_type_id)
        if not (await db.execute(deg_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Degree type not found.")

        slug = slugify(f"{data.short_name}-{data.name}")
        prog = ProgramCatalog(
            code=data.code.strip().upper(),
            name=data.name.strip(),
            short_name=data.short_name.strip(),
            discipline_id=data.discipline_id,
            degree_type_id=data.degree_type_id,
            duration_years=data.duration_years,
            description=data.description,
            slug=slug,
            aliases=data.aliases or [],
            status=data.status,
            version_id=data.version_id,
            source_id=data.source_id,
        )
        db.add(prog)
        await db.commit()
        await db.refresh(prog)
        return prog

    async def list_programs(
        self,
        db: AsyncSession,
        discipline_id: Optional[str] = None,
        degree_type_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProgramCatalog]:
        stmt = select(ProgramCatalog)
        if discipline_id:
            stmt = stmt.where(ProgramCatalog.discipline_id == discipline_id)
        if degree_type_id:
            stmt = stmt.where(ProgramCatalog.degree_type_id == degree_type_id)
        if search:
            query = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(ProgramCatalog.name).like(query),
                    func.lower(ProgramCatalog.short_name).like(query),
                    func.lower(ProgramCatalog.code).like(query),
                )
            )
        stmt = stmt.order_by(ProgramCatalog.name).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_program(self, db: AsyncSession, id: str) -> ProgramCatalog:
        stmt = select(ProgramCatalog).where(ProgramCatalog.id == id)
        prog = (await db.execute(stmt)).scalar_one_or_none()
        if not prog:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program catalog record not found.")
        return prog

    async def update_program(self, db: AsyncSession, id: str, data: ProgramCatalogUpdate) -> ProgramCatalog:
        prog = await self.get_program(db, id)
        if data.name is not None:
            prog.name = data.name.strip()
        if data.short_name is not None:
            prog.short_name = data.short_name.strip()
        if data.duration_years is not None:
            prog.duration_years = data.duration_years
        if data.description is not None:
            prog.description = data.description
        if data.aliases is not None:
            prog.aliases = data.aliases
        if data.status is not None:
            prog.status = data.status
        await db.commit()
        await db.refresh(prog)
        return prog

    async def create_specialization(self, db: AsyncSession, data: ProgramSpecializationCreate) -> ProgramSpecialization:
        await self.get_program(db, data.program_catalog_id)

        stmt = select(ProgramSpecialization).where(
            ProgramSpecialization.program_catalog_id == data.program_catalog_id,
            ProgramSpecialization.code == data.code.strip().upper(),
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Specialization code already exists for this program.")

        slug = slugify(data.name)
        spec = ProgramSpecialization(
            program_catalog_id=data.program_catalog_id,
            code=data.code.strip().upper(),
            name=data.name.strip(),
            slug=slug,
            description=data.description,
            aliases=data.aliases or [],
            status=data.status,
        )
        db.add(spec)
        await db.commit()
        await db.refresh(spec)
        return spec

    async def list_specializations(
        self, db: AsyncSession, program_catalog_id: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[ProgramSpecialization]:
        stmt = select(ProgramSpecialization)
        if program_catalog_id:
            stmt = stmt.where(ProgramSpecialization.program_catalog_id == program_catalog_id)
        stmt = stmt.order_by(ProgramSpecialization.name).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    # ---------------- Courses ----------------
    async def create_course(self, db: AsyncSession, data: CourseCatalogCreate) -> CourseCatalog:
        stmt = select(CourseCatalog).where(CourseCatalog.code == data.code.strip().upper())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="National course code already exists.")

        disc_stmt = select(AcademicDiscipline).where(AcademicDiscipline.id == data.discipline_id)
        if not (await db.execute(disc_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic discipline not found.")

        slug = slugify(f"{data.code}-{data.title}")
        course = CourseCatalog(
            code=data.code.strip().upper(),
            title=data.title.strip(),
            discipline_id=data.discipline_id,
            default_credits=data.default_credits,
            academic_level=data.academic_level,
            description=data.description,
            prerequisites=data.prerequisites or [],
            aliases=data.aliases or [],
            slug=slug,
            status=data.status,
            version_id=data.version_id,
            source_id=data.source_id,
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    async def list_courses(
        self,
        db: AsyncSession,
        discipline_id: Optional[str] = None,
        academic_level: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CourseCatalog]:
        stmt = select(CourseCatalog)
        if discipline_id:
            stmt = stmt.where(CourseCatalog.discipline_id == discipline_id)
        if academic_level:
            stmt = stmt.where(CourseCatalog.academic_level == academic_level)
        if search:
            query = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(CourseCatalog.title).like(query),
                    func.lower(CourseCatalog.code).like(query),
                )
            )
        stmt = stmt.order_by(CourseCatalog.title).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def get_course(self, db: AsyncSession, id: str) -> CourseCatalog:
        stmt = select(CourseCatalog).where(CourseCatalog.id == id)
        course = (await db.execute(stmt)).scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="National course catalog record not found.")
        return course

    async def update_course(self, db: AsyncSession, id: str, data: CourseCatalogUpdate) -> CourseCatalog:
        course = await self.get_course(db, id)
        if data.title is not None:
            course.title = data.title.strip()
        if data.default_credits is not None:
            course.default_credits = data.default_credits
        if data.academic_level is not None:
            course.academic_level = data.academic_level
        if data.description is not None:
            course.description = data.description
        if data.prerequisites is not None:
            course.prerequisites = data.prerequisites
        if data.aliases is not None:
            course.aliases = data.aliases
        if data.status is not None:
            course.status = data.status
        await db.commit()
        await db.refresh(course)
        return course

    # ---------------- Skills & Careers ----------------
    async def create_skill(self, db: AsyncSession, data: SkillCatalogCreate) -> SkillCatalog:
        stmt = select(SkillCatalog).where(SkillCatalog.code == data.code.strip().upper())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Skill code already exists.")

        slug = slugify(data.name)
        skill = SkillCatalog(
            code=data.code.strip().upper(),
            name=data.name.strip(),
            category=data.category,
            description=data.description,
            slug=slug,
            aliases=data.aliases or [],
            status=data.status,
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)
        return skill

    async def list_skills(
        self, db: AsyncSession, category: Optional[str] = None, search: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[SkillCatalog]:
        stmt = select(SkillCatalog)
        if category:
            stmt = stmt.where(SkillCatalog.category == category)
        if search:
            query = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(SkillCatalog.name).like(query),
                    func.lower(SkillCatalog.code).like(query),
                )
            )
        stmt = stmt.order_by(SkillCatalog.name).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def create_career(self, db: AsyncSession, data: CareerCatalogCreate) -> CareerCatalog:
        stmt = select(CareerCatalog).where(CareerCatalog.code == data.code.strip().upper())
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Career code already exists.")

        slug = slugify(data.title)
        career = CareerCatalog(
            code=data.code.strip().upper(),
            title=data.title.strip(),
            industry=data.industry,
            description=data.description,
            slug=slug,
            aliases=data.aliases or [],
            status=data.status,
        )
        db.add(career)
        await db.commit()
        await db.refresh(career)
        return career

    async def list_careers(
        self, db: AsyncSession, industry: Optional[str] = None, search: Optional[str] = None, skip: int = 0, limit: int = 50
    ) -> List[CareerCatalog]:
        stmt = select(CareerCatalog)
        if industry:
            stmt = stmt.where(CareerCatalog.industry == industry)
        if search:
            query = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(CareerCatalog.title).like(query),
                    func.lower(CareerCatalog.code).like(query),
                )
            )
        stmt = stmt.order_by(CareerCatalog.title).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    # ---------------- Curriculum Mappings ----------------
    async def create_program_skill_mapping(self, db: AsyncSession, data: ProgramSkillMappingCreate) -> ProgramSkillMapping:
        stmt = select(ProgramSkillMapping).where(
            ProgramSkillMapping.program_catalog_id == data.program_catalog_id,
            ProgramSkillMapping.skill_id == data.skill_id,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Program skill mapping already exists.")

        mapping = ProgramSkillMapping(
            program_catalog_id=data.program_catalog_id,
            skill_id=data.skill_id,
            relevance_weight=data.relevance_weight,
            is_core=data.is_core,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    async def create_course_skill_mapping(self, db: AsyncSession, data: CourseSkillMappingCreate) -> CourseSkillMapping:
        stmt = select(CourseSkillMapping).where(
            CourseSkillMapping.course_catalog_id == data.course_catalog_id,
            CourseSkillMapping.skill_id == data.skill_id,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Course skill mapping already exists.")

        mapping = CourseSkillMapping(
            course_catalog_id=data.course_catalog_id,
            skill_id=data.skill_id,
            depth_level=data.depth_level,
            weight=data.weight,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    async def create_career_skill_mapping(self, db: AsyncSession, data: CareerSkillMappingCreate) -> CareerSkillMapping:
        stmt = select(CareerSkillMapping).where(
            CareerSkillMapping.career_id == data.career_id,
            CareerSkillMapping.skill_id == data.skill_id,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Career skill mapping already exists.")

        mapping = CareerSkillMapping(
            career_id=data.career_id,
            skill_id=data.skill_id,
            importance=data.importance,
            weight=data.weight,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    async def create_program_career_mapping(self, db: AsyncSession, data: ProgramCareerMappingCreate) -> ProgramCareerMapping:
        stmt = select(ProgramCareerMapping).where(
            ProgramCareerMapping.program_catalog_id == data.program_catalog_id,
            ProgramCareerMapping.career_id == data.career_id,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Program career mapping already exists.")

        mapping = ProgramCareerMapping(
            program_catalog_id=data.program_catalog_id,
            career_id=data.career_id,
            match_strength=data.match_strength,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    # ---------------- Institutional Mappings ----------------
    async def create_institution_program_mapping(
        self, db: AsyncSession, data: InstitutionProgramMappingCreate
    ) -> InstitutionProgramMapping:
        # Validate target institution
        inst_stmt = select(Institution).where(Institution.id == data.institution_id)
        if not (await db.execute(inst_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target institution not found.")

        # Validate local program belongs to target institution via department
        prog_stmt = (
            select(LocalProgram)
            .join(Department, LocalProgram.department_id == Department.id)
            .where(
                LocalProgram.id == data.institution_program_id,
                Department.institution_id == data.institution_id,
            )
        )
        local_prog = (await db.execute(prog_stmt)).scalar_one_or_none()
        if not local_prog:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local institutional program not found in your institution.")

        # Validate national program exists
        await self.get_program(db, data.national_program_id)

        stmt = select(InstitutionProgramMapping).where(
            InstitutionProgramMapping.institution_id == data.institution_id,
            InstitutionProgramMapping.institution_program_id == data.institution_program_id,
            InstitutionProgramMapping.national_program_id == data.national_program_id,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Institution program mapping already exists.")

        mapping = InstitutionProgramMapping(
            institution_id=data.institution_id,
            institution_program_id=data.institution_program_id,
            national_program_id=data.national_program_id,
            specialization_id=data.specialization_id,
            local_code=data.local_code.strip(),
            local_name=data.local_name.strip(),
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            confidence_score=data.confidence_score,
            notes=data.notes,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    async def list_institution_program_mappings(
        self, db: AsyncSession, institution_id: str, skip: int = 0, limit: int = 50
    ) -> List[InstitutionProgramMapping]:
        stmt = select(InstitutionProgramMapping).where(
            InstitutionProgramMapping.institution_id == institution_id
        ).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    async def create_institution_course_mapping(
        self, db: AsyncSession, data: InstitutionCourseMappingCreate
    ) -> InstitutionCourseMapping:
        inst_stmt = select(Institution).where(Institution.id == data.institution_id)
        if not (await db.execute(inst_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target institution not found.")

        course_stmt = select(LocalCourse).where(
            LocalCourse.id == data.institution_course_id,
            LocalCourse.institution_id == data.institution_id,
        )
        if not (await db.execute(course_stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local institutional course not found in your institution.")

        await self.get_course(db, data.national_course_id)

        stmt = select(InstitutionCourseMapping).where(
            InstitutionCourseMapping.institution_id == data.institution_id,
            InstitutionCourseMapping.institution_course_id == data.institution_course_id,
            InstitutionCourseMapping.national_course_id == data.national_course_id,
        )
        if (await db.execute(stmt)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Institution course mapping already exists.")

        mapping = InstitutionCourseMapping(
            institution_id=data.institution_id,
            institution_course_id=data.institution_course_id,
            national_course_id=data.national_course_id,
            local_code=data.local_code.strip(),
            local_title=data.local_title.strip(),
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            confidence_score=data.confidence_score,
            notes=data.notes,
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    async def list_institution_course_mappings(
        self, db: AsyncSession, institution_id: str, skip: int = 0, limit: int = 50
    ) -> List[InstitutionCourseMapping]:
        stmt = select(InstitutionCourseMapping).where(
            InstitutionCourseMapping.institution_id == institution_id
        ).offset(skip).limit(limit)
        return list((await db.execute(stmt)).scalars().all())

    # ---------------- Search ----------------
    async def search_catalog(
        self, db: AsyncSession, query_str: str, limit: int = 20
    ) -> Dict[str, Any]:
        term = f"%{query_str.strip().lower()}%"

        # Search programs
        prog_stmt = select(ProgramCatalog).where(
            or_(
                func.lower(ProgramCatalog.name).like(term),
                func.lower(ProgramCatalog.short_name).like(term),
                func.lower(ProgramCatalog.code).like(term),
            )
        ).limit(limit)
        programs = list((await db.execute(prog_stmt)).scalars().all())

        # Search courses
        course_stmt = select(CourseCatalog).where(
            or_(
                func.lower(CourseCatalog.title).like(term),
                func.lower(CourseCatalog.code).like(term),
            )
        ).limit(limit)
        courses = list((await db.execute(course_stmt)).scalars().all())

        # Search skills
        skill_stmt = select(SkillCatalog).where(
            or_(
                func.lower(SkillCatalog.name).like(term),
                func.lower(SkillCatalog.code).like(term),
            )
        ).limit(limit)
        skills = list((await db.execute(skill_stmt)).scalars().all())

        # Search careers
        career_stmt = select(CareerCatalog).where(
            or_(
                func.lower(CareerCatalog.title).like(term),
                func.lower(CareerCatalog.code).like(term),
            )
        ).limit(limit)
        careers = list((await db.execute(career_stmt)).scalars().all())

        return {
            "programs": programs,
            "courses": courses,
            "skills": skills,
            "careers": careers,
        }


academic_catalog_service = AcademicCatalogService()
