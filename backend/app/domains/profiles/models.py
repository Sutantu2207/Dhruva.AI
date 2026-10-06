"""Domain 3: Student & Faculty Management, Onboarding, Mentorship & Profiles Models.

Built on top of Domain 1 (Identity & Users) and Domain 2 (Academic Institutional Hierarchy).
Reuses Domain 2.5 (SkillCatalog, CareerCatalog, AcademicDiscipline).
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# =========================================================================
# 1. Student Extended Profile & Academic Status History
# =========================================================================

class StudentProfileDetail(Base):
    """Optional biographical and professional presentation metadata for a student."""
    __tablename__ = "student_profile_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    learning_preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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

    academic_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )


class StudentAcademicStatusHistory(Base):
    """Auditable log of academic status transitions (active, on_leave, suspended, graduated, withdrawn)."""
    __tablename__ = "student_academic_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    old_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )
    changed_by: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User",
        foreign_keys=[changed_by_user_id],
    )


# =========================================================================
# 2. Student Skills & Interests
# =========================================================================

class StudentSkill(Base):
    """Skill claimed or verified for a student, referencing canonical SkillCatalog."""
    __tablename__ = "student_skills"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "skill_catalog_id", name="uq_student_skill_catalog"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill_catalog_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skill_catalogs.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    proficiency: Mapped[str] = mapped_column(String(32), default="beginner", nullable=False)  # beginner, developing, intermediate, advanced, expert
    source: Mapped[str] = mapped_column(String(32), default="self_declared", nullable=False)  # self_declared, assessment_verified, course_verified, project_verified, faculty_verified
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
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

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )
    skill_catalog: Mapped["SkillCatalog"] = relationship(  # noqa: F821
        "SkillCatalog",
        foreign_keys=[skill_catalog_id],
    )


class StudentInterest(Base):
    """Structured interest expressing a student's exploration orientation."""
    __tablename__ = "student_interests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    discipline_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("academic_disciplines.id", ondelete="SET NULL"), nullable=True
    )
    career_catalog_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("career_catalogs.id", ondelete="SET NULL"), nullable=True
    )
    interest_title: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )


class StudentCareerGoal(Base):
    """Target career pathway for a student referencing canonical CareerCatalog."""
    __tablename__ = "student_career_goals"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "career_catalog_id", name="uq_student_career_catalog"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    career_catalog_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("career_catalogs.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    short_term_goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    long_term_goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_industry: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    preferred_locations: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    target_organizations: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
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

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )
    career_catalog: Mapped["CareerCatalog"] = relationship(  # noqa: F821
        "CareerCatalog",
        foreign_keys=[career_catalog_id],
    )


# =========================================================================
# 3. Student Projects, Certifications & Achievements
# =========================================================================

class StudentProject(Base):
    """Verified student technical or research artifact demonstrating practical capability."""
    __tablename__ = "student_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_type: Mapped[str] = mapped_column(String(64), default="academic", nullable=False)  # academic, capstone, internship, hackathon, personal, research
    status: Mapped[str] = mapped_column(String(32), default="in_progress", nullable=False)  # planned, in_progress, completed, archived
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    repository_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    demo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    documentation_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    technologies: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    team_or_individual: Mapped[str] = mapped_column(String(32), default="individual", nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    outcomes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Domain 8 Extensions
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    problem_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    live_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), default="private", nullable=False)  # private, institution, public
    verification_status: Mapped[str] = mapped_column(String(32), default="unverified", nullable=False, index=True)  # unverified, submitted, under_review, verified, rejected
    team_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    contribution_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contribution_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    modules_contributed: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_breakdown: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    career_relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    career_relevance_category: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

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

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )
    project_skills: Mapped[List["StudentProjectSkill"]] = relationship(
        "StudentProjectSkill",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    project_concepts: Mapped[List["ProjectConcept"]] = relationship(  # noqa: F821
        "ProjectConcept",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    evidence_items: Mapped[List["ProjectEvidence"]] = relationship(  # noqa: F821
        "ProjectEvidence",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[List["ProjectReview"]] = relationship(  # noqa: F821
        "ProjectReview",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class StudentProjectSkill(Base):
    """Bridge connecting a student project to demonstrated skills in SkillCatalog."""
    __tablename__ = "student_project_skills"
    __table_args__ = (
        UniqueConstraint("project_id", "skill_catalog_id", name="uq_project_skill_pair"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill_catalog_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skill_catalogs.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    claimed_level: Mapped[str] = mapped_column(String(32), default="intermediate", nullable=False)
    observed_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    evidence_strength: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="unverified", nullable=False)
    verified_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="student_claim", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project: Mapped["StudentProject"] = relationship("StudentProject", back_populates="project_skills")
    skill_catalog: Mapped["SkillCatalog"] = relationship("SkillCatalog")  # noqa: F821


class StudentCertification(Base):
    """Third-party or institutional credential claimed by a student."""
    __tablename__ = "student_certifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    credential_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    document_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="unverified", nullable=False)  # unverified, pending, verified, rejected
    verified_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )


class StudentAchievement(Base):
    """External or internal competitive, leadership, or academic recognition."""
    __tablename__ = "student_achievements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), default="competition", nullable=False)  # hackathon, competition, award, academic, publication, leadership, extracurricular
    achievement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    issuer_event: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
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

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )


# =========================================================================
# 4. Student Portfolio & Resume
# =========================================================================

class StudentPortfolio(Base):
    """Curated presentation portfolio referencing real verified student projects and skills."""
    __tablename__ = "student_portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)
    theme: Mapped[str] = mapped_column(String(64), default="modern", nullable=False)
    featured_project_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    featured_skill_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    featured_certification_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    featured_achievement_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    public_visibility: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    social_links: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    custom_links: Mapped[Optional[List[Dict[str, str]]]] = mapped_column(JSON, nullable=True)
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

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )


class StudentResume(Base):
    """Structured resume data aggregating verified education, skills, and projects."""
    __tablename__ = "student_resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_academic_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected_project_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    selected_skill_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    selected_certification_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    selected_achievement_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    experience_entries: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    custom_sections: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
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

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile",
        foreign_keys=[student_profile_id],
    )


# =========================================================================
# 5. Faculty Profile Detail
# =========================================================================

class TeacherProfileDetail(Base):
    """Extended professional, research, and institutional contact details for faculty."""
    __tablename__ = "teacher_profile_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teacher_academic_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    biography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    qualifications: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    expertise_areas: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    office_location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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

    academic_profile: Mapped["TeacherAcademicProfile"] = relationship(  # noqa: F821
        "TeacherAcademicProfile",
        foreign_keys=[teacher_profile_id],
    )


# =========================================================================
# 6. Mentorship System (Relationships, Groups & Notes)
# =========================================================================

class MentorshipRelation(Base):
    """1:1 mentorship assignment between a mentor user and a student."""
    __tablename__ = "mentorship_relations"
    __table_args__ = (
        UniqueConstraint("mentor_user_id", "student_profile_id", name="uq_mentor_student_pair"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    mentor_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)  # active, paused, completed, ended
    assignment_source: Mapped[str] = mapped_column(String(32), default="admin_assigned", nullable=False)  # admin_assigned, hod_assigned, system_assigned
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

    mentor_user: Mapped["User"] = relationship("User", foreign_keys=[mentor_user_id])  # noqa: F821
    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile", foreign_keys=[student_profile_id]
    )


class MentorGroup(Base):
    """Mentoring cohort grouping multiple students under an assigned mentor."""
    __tablename__ = "mentor_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    department_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    mentor_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)  # active, completed, archived
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

    mentor_user: Mapped["User"] = relationship("User", foreign_keys=[mentor_user_id])  # noqa: F821
    members: Mapped[List["MentorGroupMember"]] = relationship(
        "MentorGroupMember", back_populates="group", cascade="all, delete-orphan"
    )


class MentorGroupMember(Base):
    """Membership of a student within a MentorGroup."""
    __tablename__ = "mentor_group_members"
    __table_args__ = (
        UniqueConstraint("mentor_group_id", "student_profile_id", name="uq_group_student_pair"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mentor_group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("mentor_groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    group: Mapped["MentorGroup"] = relationship("MentorGroup", back_populates="members")
    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile", foreign_keys=[student_profile_id]
    )


class MentorNote(Base):
    """Private or shared mentor observation notes. Strictly protected from unauthorized student visibility."""
    __tablename__ = "mentor_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    mentor_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), default="private_mentor", nullable=False)  # private_mentor, shared_faculty, institutional_admin
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)  # open, resolved, archived
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

    mentor_user: Mapped["User"] = relationship("User", foreign_keys=[mentor_user_id])  # noqa: F821
    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile", foreign_keys=[student_profile_id]
    )


# =========================================================================
# 7. Follow-Up / Intervention Foundation
# =========================================================================

class StudentIntervention(Base):
    """Structured follow-up record for academic, attendance, or course guidance."""
    __tablename__ = "student_interventions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_academic_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # academic_support, attendance_support, course_support, career_support, project_support, administrative_support
    priority: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)  # low, medium, high, urgent
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)  # open, in_progress, resolved, closed
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    action_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
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

    student_profile: Mapped["StudentAcademicProfile"] = relationship(  # noqa: F821
        "StudentAcademicProfile", foreign_keys=[student_profile_id]
    )
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])  # noqa: F821


# =========================================================================
# 8. Onboarding Import Jobs
# =========================================================================

class OnboardingImportJob(Base):
    """Audit log tracking bulk student and faculty CSV/JSON onboarding operations."""
    __tablename__ = "onboarding_import_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    import_type: Mapped[str] = mapped_column(String(32), nullable=False)  # students, faculty
    initiated_by_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_dry_run: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, completed, failed
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped["Institution"] = relationship("Institution")  # noqa: F821
    initiated_by: Mapped["User"] = relationship("User", foreign_keys=[initiated_by_user_id])  # noqa: F821
