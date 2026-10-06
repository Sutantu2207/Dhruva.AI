"""Database models for National Academic Taxonomy & India-Wide Academic Catalog (Domain 2.5).

Provides a decoupled national curriculum taxonomy covering:
- Disciplines (Engineering, Sciences, Commerce, Arts, Design, Law, Medicine, etc.)
- Degree Types (Certificate, Diploma, Undergraduate, Postgraduate, Doctoral, etc.)
- National Programs & Specializations
- National Course Catalog
- Skill Catalog & Career Catalog
- Multi-dimensional Mappings (Program/Course/Career -> Skills, Program -> Career)
- Institution-specific Mapping layer (Mapping local college programs/courses to national standards)
- Versioning, Source Provenance, and Ingestion Audit Tracking.
"""

import uuid
from datetime import datetime, timezone, date
from typing import List, Optional
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Date,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# =========================================================================
# 1. Source Provenance & Catalog Versioning
# =========================================================================

class AcademicCatalogSource(Base):
    """Authoritative source or governing regulatory body (e.g. UGC, AICTE, NMC, BCI, NBA)."""
    __tablename__ = "academic_catalog_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_authoritative: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    versions: Mapped[List["AcademicCatalogVersion"]] = relationship("AcademicCatalogVersion", back_populates="source", cascade="all, delete-orphan")


class AcademicCatalogVersion(Base):
    """Immutable version release tag for the national catalog taxonomy."""
    __tablename__ = "academic_catalog_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version_tag: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., "2026.1"
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)  # draft, active, superseded, archived
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    source: Mapped[Optional["AcademicCatalogSource"]] = relationship("AcademicCatalogSource", back_populates="versions")


# =========================================================================
# 2. National Academic Taxonomy & Degree Types
# =========================================================================

class AcademicDiscipline(Base):
    """Broad discipline of higher learning (Engineering, Sciences, Management, Humanities, Design, etc.)."""
    __tablename__ = "academic_disciplines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g. "ENGG_TECH", "COMMERCE_MGMT"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_versions.id", ondelete="SET NULL"), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    programs: Mapped[List["ProgramCatalog"]] = relationship("ProgramCatalog", back_populates="discipline", cascade="all, delete-orphan")
    courses: Mapped[List["CourseCatalog"]] = relationship("CourseCatalog", back_populates="discipline")


class DegreeType(Base):
    """Academic level classification (Certificate, Diploma, Undergraduate, Postgraduate, Doctoral)."""
    __tablename__ = "degree_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # UG, PG, DIPLOMA, DOCTORAL
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # "Undergraduate"
    short_name: Mapped[str] = mapped_column(String(64), nullable=False)  # "UG"
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # 1=Cert, 2=Diploma, 3=UG, 4=PG, 5=Doctoral
    typical_duration_years: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    programs: Mapped[List["ProgramCatalog"]] = relationship("ProgramCatalog", back_populates="degree_type")


# =========================================================================
# 3. National Program & Specialization Catalog
# =========================================================================

class ProgramCatalog(Base):
    """Authoritative national program entity (e.g. B.Tech, B.Sc, BCA, BBA, B.Com, B.Des, MBBS, LL.B)."""
    __tablename__ = "program_catalogs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., "BTECH", "BCA", "MBBS"
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # "Bachelor of Technology"
    short_name: Mapped[str] = mapped_column(String(64), nullable=False)  # "B.Tech"
    discipline_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_disciplines.id", ondelete="RESTRICT"), index=True, nullable=False)
    degree_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("degree_types.id", ondelete="RESTRICT"), index=True, nullable=False)
    duration_years: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_versions.id", ondelete="SET NULL"), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    discipline: Mapped["AcademicDiscipline"] = relationship("AcademicDiscipline", back_populates="programs")
    degree_type: Mapped["DegreeType"] = relationship("DegreeType", back_populates="programs")
    specializations: Mapped[List["ProgramSpecialization"]] = relationship("ProgramSpecialization", back_populates="program_catalog", cascade="all, delete-orphan")
    skill_mappings: Mapped[List["ProgramSkillMapping"]] = relationship("ProgramSkillMapping", back_populates="program", cascade="all, delete-orphan")
    career_mappings: Mapped[List["ProgramCareerMapping"]] = relationship("ProgramCareerMapping", back_populates="program", cascade="all, delete-orphan")


class ProgramSpecialization(Base):
    """Academic program specialization (e.g. Computer Science & Engg, AI & ML, Data Science, Finance)."""
    __tablename__ = "program_specializations"
    __table_args__ = (
        UniqueConstraint("program_catalog_id", "code", name="uq_prog_spec_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    program_catalog_id: Mapped[str] = mapped_column(String(36), ForeignKey("program_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # e.g., "CSE", "AIML", "FINANCE"
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # "Artificial Intelligence and Machine Learning"
    slug: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    program_catalog: Mapped["ProgramCatalog"] = relationship("ProgramCatalog", back_populates="specializations")


# =========================================================================
# 4. National Course Catalog
# =========================================================================

class CourseCatalog(Base):
    """Standardized national curriculum course definition decoupled from specific institutions."""
    __tablename__ = "course_catalogs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., "NAT-CS-DSA"
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # "Data Structures and Algorithms"
    discipline_id: Mapped[str] = mapped_column(String(36), ForeignKey("academic_disciplines.id", ondelete="RESTRICT"), index=True, nullable=False)
    default_credits: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)
    academic_level: Mapped[str] = mapped_column(String(32), default="intermediate", nullable=False)  # introductory, intermediate, advanced, research
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_versions.id", ondelete="SET NULL"), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    discipline: Mapped["AcademicDiscipline"] = relationship("AcademicDiscipline", back_populates="courses")
    skill_mappings: Mapped[List["CourseSkillMapping"]] = relationship("CourseSkillMapping", back_populates="course", cascade="all, delete-orphan")


# =========================================================================
# 5. Skills & Careers Taxonomy
# =========================================================================

class SkillCatalog(Base):
    """Reusable skill taxonomy entity (technical, analytical, domain, soft_skill)."""
    __tablename__ = "skill_catalogs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., "SKL-PYTHON", "SKL-SQL"
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # "Python Programming"
    category: Mapped[str] = mapped_column(String(64), default="technical", nullable=False)  # technical, domain, soft_skill, analytical
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CareerCatalog(Base):
    """Career trajectory and target profile definition (e.g., Software Engineer, Data Scientist, UX Designer)."""
    __tablename__ = "career_catalogs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., "CAR-SWE", "CAR-DATA-SCIENTIST"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(128), default="Technology", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    skill_mappings: Mapped[List["CareerSkillMapping"]] = relationship("CareerSkillMapping", back_populates="career", cascade="all, delete-orphan")


# =========================================================================
# 6. Multi-Dimensional Curriculum Mappings
# =========================================================================

class ProgramSkillMapping(Base):
    """Associates academic programs with foundational skills."""
    __tablename__ = "program_skill_mappings"
    __table_args__ = (
        UniqueConstraint("program_catalog_id", "skill_id", name="uq_prog_skill_map"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    program_catalog_id: Mapped[str] = mapped_column(String(36), ForeignKey("program_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    relevance_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_core: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    program: Mapped["ProgramCatalog"] = relationship("ProgramCatalog", back_populates="skill_mappings")
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")


class CourseSkillMapping(Base):
    """Associates courses with imparted skills."""
    __tablename__ = "course_skill_mappings"
    __table_args__ = (
        UniqueConstraint("course_catalog_id", "skill_id", name="uq_course_skill_map"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    course_catalog_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    depth_level: Mapped[str] = mapped_column(String(32), default="applied", nullable=False)  # foundational, applied, expert
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    course: Mapped["CourseCatalog"] = relationship("CourseCatalog", back_populates="skill_mappings")
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")


class CareerSkillMapping(Base):
    """Connects careers to required/preferred competency skills."""
    __tablename__ = "career_skill_mappings"
    __table_args__ = (
        UniqueConstraint("career_id", "skill_id", name="uq_career_skill_map"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    career_id: Mapped[str] = mapped_column(String(36), ForeignKey("career_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    importance: Mapped[str] = mapped_column(String(32), default="required", nullable=False)  # required, preferred, bonus
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    career: Mapped["CareerCatalog"] = relationship("CareerCatalog", back_populates="skill_mappings")
    skill: Mapped["SkillCatalog"] = relationship("SkillCatalog")


class ProgramCareerMapping(Base):
    """High-level pathways connecting degree programs to primary career destinations."""
    __tablename__ = "program_career_mappings"
    __table_args__ = (
        UniqueConstraint("program_catalog_id", "career_id", name="uq_prog_career_map"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    program_catalog_id: Mapped[str] = mapped_column(String(36), ForeignKey("program_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    career_id: Mapped[str] = mapped_column(String(36), ForeignKey("career_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    match_strength: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)

    program: Mapped["ProgramCatalog"] = relationship("ProgramCatalog", back_populates="career_mappings")
    career: Mapped["CareerCatalog"] = relationship("CareerCatalog")


# =========================================================================
# 7. Institutional Mappings (Local College -> National Standard)
# =========================================================================

class InstitutionProgramMapping(Base):
    """Binds an institution's internal program offering to the national catalog."""
    __tablename__ = "institution_program_mappings"
    __table_args__ = (
        UniqueConstraint("institution_id", "institution_program_id", "national_program_id", name="uq_inst_prog_national_map"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    institution_program_id: Mapped[str] = mapped_column(String(36), ForeignKey("programs.id", ondelete="CASCADE"), index=True, nullable=False)
    national_program_id: Mapped[str] = mapped_column(String(36), ForeignKey("program_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    specialization_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("program_specializations.id", ondelete="SET NULL"), nullable=True, index=True)
    local_code: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., "BE-CSE"
    local_name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "B.Tech Computer Science & Engg"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class InstitutionCourseMapping(Base):
    """Binds an institution's specific course offering to a standardized national course."""
    __tablename__ = "institution_course_mappings"
    __table_args__ = (
        UniqueConstraint("institution_id", "institution_course_id", "national_course_id", name="uq_inst_course_national_map"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False)
    institution_course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False)
    national_course_id: Mapped[str] = mapped_column(String(36), ForeignKey("course_catalogs.id", ondelete="CASCADE"), index=True, nullable=False)
    local_code: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., "CSE302"
    local_title: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Data Structures and Applications"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# =========================================================================
# 8. Import Execution & Audit Tracking
# =========================================================================

class CatalogImportJob(Base):
    """Audit log tracking administrative dataset imports (CSV/JSON)."""
    __tablename__ = "catalog_import_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)  # discipline, degree_type, program, course, skill, career
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_sources.id", ondelete="SET NULL"), nullable=True)
    version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("academic_catalog_versions.id", ondelete="SET NULL"), nullable=True)
    is_dry_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, completed, failed
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    initiated_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
