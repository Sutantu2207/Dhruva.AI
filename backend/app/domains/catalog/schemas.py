"""Pydantic schemas for National Academic Taxonomy & India-Wide Academic Catalog."""

from datetime import datetime, date
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# =========================================================================
# Sources & Versions
# =========================================================================

class AcademicCatalogSourceCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    organization: str = Field(min_length=2, max_length=255)
    website_url: Optional[str] = None
    is_authoritative: bool = True


class AcademicCatalogSourceResponse(AcademicCatalogSourceCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AcademicCatalogVersionCreate(BaseModel):
    version_tag: str = Field(min_length=2, max_length=64)
    source_id: Optional[str] = None
    status: str = "active"
    effective_date: date
    notes: Optional[str] = None


class AcademicCatalogVersionResponse(AcademicCatalogVersionCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Disciplines & Degree Types
# =========================================================================

class AcademicDisciplineCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    display_name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    status: str = "active"
    version_id: Optional[str] = None
    source_id: Optional[str] = None


class AcademicDisciplineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    display_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    status: Optional[str] = None


class AcademicDisciplineResponse(AcademicDisciplineCreate):
    id: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DegreeTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    short_name: str = Field(min_length=1, max_length=64)
    level: int = Field(default=3, ge=1, le=10)
    typical_duration_years: float = Field(default=4.0, ge=0.5, le=10.0)
    status: str = "active"


class DegreeTypeResponse(DegreeTypeCreate):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Programs & Specializations
# =========================================================================

class ProgramCatalogCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    short_name: str = Field(min_length=1, max_length=64)
    discipline_id: str
    degree_type_id: str
    duration_years: float = Field(default=4.0, ge=0.5, le=10.0)
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    status: str = "active"
    version_id: Optional[str] = None
    source_id: Optional[str] = None


class ProgramCatalogUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    short_name: Optional[str] = Field(None, min_length=1, max_length=64)
    duration_years: Optional[float] = Field(None, ge=0.5, le=10.0)
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    status: Optional[str] = None


class ProgramCatalogResponse(ProgramCatalogCreate):
    id: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProgramSpecializationCreate(BaseModel):
    program_catalog_id: str
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    status: str = "active"


class ProgramSpecializationResponse(ProgramSpecializationCreate):
    id: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Courses
# =========================================================================

class CourseCatalogCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=2, max_length=255)
    discipline_id: str
    default_credits: float = Field(default=3.0, ge=0.5, le=30.0)
    academic_level: str = "intermediate"
    description: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    status: str = "active"
    version_id: Optional[str] = None
    source_id: Optional[str] = None


class CourseCatalogUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    default_credits: Optional[float] = Field(None, ge=0.5, le=30.0)
    academic_level: Optional[str] = None
    description: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    status: Optional[str] = None


class CourseCatalogResponse(CourseCatalogCreate):
    id: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Skills & Careers
# =========================================================================

class SkillCatalogCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    category: str = "technical"
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    status: str = "active"


class SkillCatalogResponse(SkillCatalogCreate):
    id: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CareerCatalogCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=2, max_length=255)
    industry: str = "Technology"
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    status: str = "active"


class CareerCatalogResponse(CareerCatalogCreate):
    id: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Curriculum Mappings
# =========================================================================

class ProgramSkillMappingCreate(BaseModel):
    program_catalog_id: str
    skill_id: str
    relevance_weight: float = Field(default=1.0, ge=0.0, le=1.0)
    is_core: bool = True


class ProgramSkillMappingResponse(ProgramSkillMappingCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class CourseSkillMappingCreate(BaseModel):
    course_catalog_id: str
    skill_id: str
    depth_level: str = "applied"
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class CourseSkillMappingResponse(CourseSkillMappingCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class CareerSkillMappingCreate(BaseModel):
    career_id: str
    skill_id: str
    importance: str = "required"
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class CareerSkillMappingResponse(CareerSkillMappingCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class ProgramCareerMappingCreate(BaseModel):
    program_catalog_id: str
    career_id: str
    match_strength: float = Field(default=0.8, ge=0.0, le=1.0)


class ProgramCareerMappingResponse(ProgramCareerMappingCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Institutional Mappings
# =========================================================================

class InstitutionProgramMappingCreate(BaseModel):
    institution_id: str
    institution_program_id: str
    national_program_id: str
    specialization_id: Optional[str] = None
    local_code: str = Field(min_length=1, max_length=64)
    local_name: str = Field(min_length=2, max_length=255)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class InstitutionProgramMappingResponse(InstitutionProgramMappingCreate):
    id: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InstitutionCourseMappingCreate(BaseModel):
    institution_id: str
    institution_course_id: str
    national_course_id: str
    local_code: str = Field(min_length=1, max_length=64)
    local_title: str = Field(min_length=2, max_length=255)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class InstitutionCourseMappingResponse(InstitutionCourseMappingCreate):
    id: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# Import & Search
# =========================================================================

class CatalogImportRequest(BaseModel):
    entity_type: str = Field(description="discipline, degree_type, program, specialization, course, skill, career")
    source_id: Optional[str] = None
    version_id: Optional[str] = None
    is_dry_run: bool = False
    records: List[Dict[str, Any]]


class CatalogImportJobResponse(BaseModel):
    id: str
    entity_type: str
    source_id: Optional[str] = None
    version_id: Optional[str] = None
    is_dry_run: bool
    status: str
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    duplicate_records: int
    errors: Optional[List[Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CatalogSearchResult(BaseModel):
    programs: List[ProgramCatalogResponse]
    courses: List[CourseCatalogResponse]
    skills: List[SkillCatalogResponse]
    careers: List[CareerCatalogResponse]
