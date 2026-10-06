"""National Academic Taxonomy & India-Wide Academic Catalog REST API Endpoints (Domain 2.5).

Enforces centralized RBAC and institutional scoping:
- Super Admin: Authoritative catalog curation, versioning, source provenance, and dataset imports.
- Institution Admin: Browses national catalog, maps institutional programs/courses to national catalog.
- Teacher / Student: Read-only search and catalog exploration.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
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
    InstitutionProgramMapping,
    InstitutionCourseMapping,
    CatalogImportJob,
)
from app.domains.catalog.schemas import (
    AcademicCatalogSourceCreate,
    AcademicCatalogSourceResponse,
    AcademicCatalogVersionCreate,
    AcademicCatalogVersionResponse,
    AcademicDisciplineCreate,
    AcademicDisciplineUpdate,
    AcademicDisciplineResponse,
    DegreeTypeCreate,
    DegreeTypeResponse,
    ProgramCatalogCreate,
    ProgramCatalogUpdate,
    ProgramCatalogResponse,
    ProgramSpecializationCreate,
    ProgramSpecializationResponse,
    CourseCatalogCreate,
    CourseCatalogUpdate,
    CourseCatalogResponse,
    SkillCatalogCreate,
    SkillCatalogResponse,
    CareerCatalogCreate,
    CareerCatalogResponse,
    ProgramSkillMappingCreate,
    ProgramSkillMappingResponse,
    CourseSkillMappingCreate,
    CourseSkillMappingResponse,
    CareerSkillMappingCreate,
    CareerSkillMappingResponse,
    ProgramCareerMappingCreate,
    ProgramCareerMappingResponse,
    InstitutionProgramMappingCreate,
    InstitutionProgramMappingResponse,
    InstitutionCourseMappingCreate,
    InstitutionCourseMappingResponse,
    CatalogImportRequest,
    CatalogImportJobResponse,
    CatalogSearchResult,
)
from app.domains.catalog.service import academic_catalog_service
from app.domains.catalog.importer import catalog_importer

router = APIRouter(prefix="/catalog", tags=["National Academic Catalog"])


def _check_institution_mapping_access(current_user: User, target_institution_id: str) -> None:
    """Ensures user can only create/manage mappings within their authorized institution."""
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    if current_user.role == UserRole.INSTITUTION_ADMIN:
        if current_user.institution_id and current_user.institution_id == target_institution_id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot map resources for an institution other than your assigned institution.",
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Requires Institution Admin or Super Admin privileges.",
    )


# =========================================================================
# 1. Sources & Catalog Versions
# =========================================================================

@router.get("/sources", response_model=List[AcademicCatalogSourceResponse], summary="List catalog sources")
async def list_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_sources(db, skip=skip, limit=limit)


@router.post(
    "/sources",
    response_model=AcademicCatalogSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register catalog source (Super Admin only)",
)
async def create_source(
    payload: AcademicCatalogSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_source(db, payload)


@router.get("/catalog-versions", response_model=List[AcademicCatalogVersionResponse], summary="List catalog versions")
async def list_catalog_versions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_versions(db, skip=skip, limit=limit)


@router.post(
    "/catalog-versions",
    response_model=AcademicCatalogVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish catalog version (Super Admin only)",
)
async def create_catalog_version(
    payload: AcademicCatalogVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_version(db, payload)


# =========================================================================
# 2. Disciplines & Degree Types
# =========================================================================

@router.get("/disciplines", response_model=List[AcademicDisciplineResponse], summary="List academic disciplines")
async def list_disciplines(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_disciplines(db, skip=skip, limit=limit)


@router.get("/disciplines/{id_or_code}", response_model=AcademicDisciplineResponse, summary="Get discipline details")
async def get_discipline(
    id_or_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.get_discipline(db, id_or_code)


@router.post(
    "/disciplines",
    response_model=AcademicDisciplineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create academic discipline (Super Admin only)",
)
async def create_discipline(
    payload: AcademicDisciplineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_discipline(db, payload)


@router.get("/degree-types", response_model=List[DegreeTypeResponse], summary="List academic degree types")
async def list_degree_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_degree_types(db, skip=skip, limit=limit)


@router.post(
    "/degree-types",
    response_model=DegreeTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create academic degree type (Super Admin only)",
)
async def create_degree_type(
    payload: DegreeTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_degree_type(db, payload)


# =========================================================================
# 3. Programs & Specializations
# =========================================================================

@router.get("/programs", response_model=List[ProgramCatalogResponse], summary="List national programs")
async def list_programs(
    discipline_id: Optional[str] = Query(None),
    degree_type_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_programs(
        db, discipline_id=discipline_id, degree_type_id=degree_type_id, search=search, skip=skip, limit=limit
    )


@router.get("/programs/{id}", response_model=ProgramCatalogResponse, summary="Get national program details")
async def get_program(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.get_program(db, id)


@router.post(
    "/programs",
    response_model=ProgramCatalogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create national program (Super Admin only)",
)
async def create_program(
    payload: ProgramCatalogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_program(db, payload)


@router.patch(
    "/programs/{id}",
    response_model=ProgramCatalogResponse,
    summary="Update national program (Super Admin only)",
)
async def update_program(
    id: str,
    payload: ProgramCatalogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.update_program(db, id, payload)


@router.get("/specializations", response_model=List[ProgramSpecializationResponse], summary="List program specializations")
async def list_specializations(
    program_catalog_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_specializations(db, program_catalog_id=program_catalog_id, skip=skip, limit=limit)


@router.post(
    "/specializations",
    response_model=ProgramSpecializationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create program specialization (Super Admin only)",
)
async def create_specialization(
    payload: ProgramSpecializationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_specialization(db, payload)


# =========================================================================
# 4. Courses
# =========================================================================

@router.get("/courses", response_model=List[CourseCatalogResponse], summary="List national courses")
async def list_courses(
    discipline_id: Optional[str] = Query(None),
    academic_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_courses(
        db, discipline_id=discipline_id, academic_level=academic_level, search=search, skip=skip, limit=limit
    )


@router.get("/courses/{id}", response_model=CourseCatalogResponse, summary="Get national course details")
async def get_course(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.get_course(db, id)


@router.post(
    "/courses",
    response_model=CourseCatalogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create national course (Super Admin only)",
)
async def create_course(
    payload: CourseCatalogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_course(db, payload)


@router.patch(
    "/courses/{id}",
    response_model=CourseCatalogResponse,
    summary="Update national course (Super Admin only)",
)
async def update_course(
    id: str,
    payload: CourseCatalogUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.update_course(db, id, payload)


# =========================================================================
# 5. Skills & Careers
# =========================================================================

@router.get("/skills", response_model=List[SkillCatalogResponse], summary="List skills in catalog")
async def list_skills(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_skills(db, category=category, search=search, skip=skip, limit=limit)


@router.post(
    "/skills",
    response_model=SkillCatalogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create skill in catalog (Super Admin only)",
)
async def create_skill(
    payload: SkillCatalogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_skill(db, payload)


@router.get("/careers", response_model=List[CareerCatalogResponse], summary="List careers in catalog")
async def list_careers(
    industry: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.list_careers(db, industry=industry, search=search, skip=skip, limit=limit)


@router.post(
    "/careers",
    response_model=CareerCatalogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create career in catalog (Super Admin only)",
)
async def create_career(
    payload: CareerCatalogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_career(db, payload)


# =========================================================================
# 6. Curriculum Mappings
# =========================================================================

@router.post(
    "/program-skill-mappings",
    response_model=ProgramSkillMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map skill to program (Super Admin only)",
)
async def create_program_skill_mapping(
    payload: ProgramSkillMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_program_skill_mapping(db, payload)


@router.post(
    "/course-skill-mappings",
    response_model=CourseSkillMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map skill to course (Super Admin only)",
)
async def create_course_skill_mapping(
    payload: CourseSkillMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_course_skill_mapping(db, payload)


@router.post(
    "/career-skill-mappings",
    response_model=CareerSkillMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map skill to career (Super Admin only)",
)
async def create_career_skill_mapping(
    payload: CareerSkillMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_career_skill_mapping(db, payload)


@router.post(
    "/program-career-mappings",
    response_model=ProgramCareerMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map career to program (Super Admin only)",
)
async def create_program_career_mapping(
    payload: ProgramCareerMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await academic_catalog_service.create_program_career_mapping(db, payload)


# =========================================================================
# 7. Institutional Mappings (Local College -> National Catalog)
# =========================================================================

@router.post(
    "/institution-program-mappings",
    response_model=InstitutionProgramMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map local institution program to national program",
)
async def map_institution_program(
    payload: InstitutionProgramMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_institution_mapping_access(current_user, payload.institution_id)
    return await academic_catalog_service.create_institution_program_mapping(db, payload)


@router.get(
    "/institution-program-mappings",
    response_model=List[InstitutionProgramMappingResponse],
    summary="List program mappings for institution",
)
async def list_institution_program_mappings(
    institution_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_inst = institution_id or current_user.institution_id
    if not target_inst:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="institution_id parameter required.")
    _check_institution_mapping_access(current_user, target_inst)
    return await academic_catalog_service.list_institution_program_mappings(db, institution_id=target_inst, skip=skip, limit=limit)


@router.post(
    "/institution-course-mappings",
    response_model=InstitutionCourseMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map local institution course to national course",
)
async def map_institution_course(
    payload: InstitutionCourseMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_institution_mapping_access(current_user, payload.institution_id)
    return await academic_catalog_service.create_institution_course_mapping(db, payload)


@router.get(
    "/institution-course-mappings",
    response_model=List[InstitutionCourseMappingResponse],
    summary="List course mappings for institution",
)
async def list_institution_course_mappings(
    institution_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_inst = institution_id or current_user.institution_id
    if not target_inst:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="institution_id parameter required.")
    _check_institution_mapping_access(current_user, target_inst)
    return await academic_catalog_service.list_institution_course_mappings(db, institution_id=target_inst, skip=skip, limit=limit)


# =========================================================================
# 8. Unified Search & Batch Import
# =========================================================================

@router.get("/search", response_model=CatalogSearchResult, summary="Unified search across national catalog")
async def search_catalog(
    q: str = Query(..., min_length=2, description="Search query string"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await academic_catalog_service.search_catalog(db, query_str=q, limit=limit)


@router.post(
    "/imports",
    response_model=CatalogImportJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute bulk dataset import (Super Admin only)",
)
async def execute_catalog_import(
    payload: CatalogImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    return await catalog_importer.execute_import(db, payload, user_id=current_user.id)


@router.get(
    "/imports/{job_id}",
    response_model=CatalogImportJobResponse,
    summary="Get import job status & report (Super Admin only)",
)
async def get_import_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    stmt = select(CatalogImportJob).where(CatalogImportJob.id == job_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found.")
    return job
