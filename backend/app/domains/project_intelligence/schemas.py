"""Pydantic schemas for Domain 8: Project Intelligence, Evidence Graph & Portfolio Engine."""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


# =========================================================================
# 1. Project Schemas
# =========================================================================

class ProjectSkillItem(BaseModel):
    skill_catalog_id: str
    skill_name: Optional[str] = None
    skill_code: Optional[str] = None
    claimed_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    observed_level: Optional[str] = None
    evidence_strength: float = 0.50
    verification_status: str = "unverified"
    source: str = "student_claim"
    notes: Optional[str] = None


class ProjectSkillResponse(BaseModel):
    id: str
    project_id: str
    skill_catalog_id: str
    skill_name: Optional[str] = None
    skill_category: Optional[str] = None
    claimed_level: str = "intermediate"
    observed_level: Optional[str] = None
    evidence_strength: float = 0.50
    verification_status: str = "unverified"
    verified_by_user_id: Optional[str] = None
    verified_at: Optional[datetime] = None
    source: str = "student_claim"
    notes: Optional[str] = None


class ProjectConceptItem(BaseModel):
    concept_id: str
    concept_name: Optional[str] = None
    demonstrated_level: str = "proficient"
    verification_status: str = "unverified"
    notes: Optional[str] = None


class ProjectConceptResponse(BaseModel):
    id: str
    project_id: str
    concept_id: str
    concept_name: Optional[str] = None
    demonstrated_level: str = "proficient"
    verification_status: str = "unverified"
    verified_by_user_id: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    problem_statement: Optional[str] = None
    solution: Optional[str] = None
    project_type: str = "academic"  # academic, personal, hackathon, internship, capstone, research, open_source, freelance, startup, competition, other
    status: str = "in_progress"  # planned, in_progress, completed, archived
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    repository_url: Optional[str] = None
    live_url: Optional[str] = None
    demo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    technologies: Optional[List[str]] = None
    team_or_individual: str = "individual"
    role: Optional[str] = None
    team_size: int = 1
    contribution_description: Optional[str] = None
    contribution_percentage: Optional[float] = None
    modules_contributed: Optional[List[str]] = None
    visibility: str = "private"  # private, institution, public
    skill_ids: Optional[List[str]] = None
    concept_ids: Optional[List[str]] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    problem_statement: Optional[str] = None
    solution: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    repository_url: Optional[str] = None
    live_url: Optional[str] = None
    demo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    technologies: Optional[List[str]] = None
    team_or_individual: Optional[str] = None
    role: Optional[str] = None
    team_size: Optional[int] = None
    contribution_description: Optional[str] = None
    contribution_percentage: Optional[float] = None
    modules_contributed: Optional[List[str]] = None
    visibility: Optional[str] = None
    skill_ids: Optional[List[str]] = None
    concept_ids: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    id: str
    student_profile_id: str
    title: str
    slug: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    solution: Optional[str] = None
    project_type: str
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    repository_url: Optional[str] = None
    live_url: Optional[str] = None
    demo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    technologies: Optional[List[str]] = None
    visibility: str
    team_or_individual: str
    role: Optional[str] = None
    team_size: int = 1
    contribution_description: Optional[str] = None
    contribution_percentage: Optional[float] = None
    modules_contributed: Optional[List[str]] = None
    verification_status: str
    is_verified: bool
    verified_by_user_id: Optional[str] = None
    quality_score: Optional[float] = None
    career_relevance_score: Optional[float] = None
    career_relevance_category: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# =========================================================================
# 2. Evidence Schemas
# =========================================================================

class ProjectEvidenceCreate(BaseModel):
    evidence_type: str  # repository, commit, pull_request, deployment, documentation, demo, screenshot, video, test_report, architecture_diagram, faculty_review, mentor_review, assessment, project_submission
    source: str = "github"  # github, gitlab, url, file_upload, internal
    source_reference: str
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    evidence_strength: float = Field(0.80, ge=0.0, le=1.0)
    metadata_json: Optional[Dict[str, Any]] = None


class ProjectEvidenceVerify(BaseModel):
    decision: str  # verified, rejected
    verification_notes: Optional[str] = None


ProjectEvidenceVerifyRequest = ProjectEvidenceVerify


class ProjectEvidenceResponse(BaseModel):
    id: str
    project_id: str
    student_profile_id: str
    evidence_type: str
    source: str
    source_reference: str
    title: str
    description: Optional[str] = None
    submitted_at: datetime
    verification_status: str
    verified_by_user_id: Optional[str] = None
    verified_at: Optional[datetime] = None
    evidence_strength: float
    metadata_json: Optional[Dict[str, Any]] = None
    algorithm_version: str = "v1.0.0-deterministic"


# =========================================================================
# 3. Faculty Review Schemas
# =========================================================================

class ProjectReviewCreate(BaseModel):
    review_type: str = "faculty"  # faculty, mentor, peer
    technical_depth: float = Field(70.0, ge=0.0, le=100.0)
    problem_solving: float = Field(70.0, ge=0.0, le=100.0)
    code_quality: float = Field(70.0, ge=0.0, le=100.0)
    architecture_quality: float = Field(70.0, ge=0.0, le=100.0)
    documentation_quality: float = Field(70.0, ge=0.0, le=100.0)
    testing_quality: float = Field(70.0, ge=0.0, le=100.0)
    practical_application: float = Field(70.0, ge=0.0, le=100.0)
    originality: float = Field(70.0, ge=0.0, le=100.0)
    student_contribution_score: float = Field(70.0, ge=0.0, le=100.0)
    professional_presentation: float = Field(70.0, ge=0.0, le=100.0)
    feedback: Optional[str] = None
    decision: str = "approved"  # approved, rejected, revisions_requested


class ProjectReviewResponse(BaseModel):
    id: str
    project_id: str
    reviewer_user_id: str
    reviewer_name: Optional[str] = None
    review_type: str
    technical_depth: float
    problem_solving: float
    code_quality: float
    architecture_quality: float
    documentation_quality: float
    testing_quality: float
    practical_application: float
    originality: float
    student_contribution_score: float
    professional_presentation: float
    overall_score: float
    rubric_breakdown: Dict[str, float] = {}
    feedback: Optional[str] = None
    decision: str
    is_finalized: bool
    reviewed_at: datetime


# =========================================================================
# 4. Intelligence & Evaluation Schemas
# =========================================================================

class ProjectQualityResultSchema(BaseModel):
    overall_score: float
    technical_depth: float = 0.0
    implementation_quality: float = 0.0
    documentation_quality: float = 0.0
    testing_quality: float = 0.0
    architecture_quality: float = 0.0
    verification_strength: float = 0.0
    dimension_breakdown: Dict[str, Any] = {}
    missing_elements: List[str] = []
    algorithm_version: str = "v1.0.0-deterministic"


ProjectQualityResponse = ProjectQualityResultSchema


class CareerRelevanceResultSchema(BaseModel):
    project_id: str
    career_id: str
    career_title: str
    relevance_score: float
    relevance_tier: str
    matched_skills_count: int
    critical_skills_matched: List[str] = []
    missing_critical_skills: List[str] = []
    explanation: str
    algorithm_version: str = "v1.0.0-deterministic"


CareerRelevanceResponse = CareerRelevanceResultSchema


class ProjectDetailResponse(ProjectResponse):
    skills: List[ProjectSkillResponse] = []
    concepts: List[ProjectConceptResponse] = []
    evidence: List[ProjectEvidenceResponse] = []
    reviews: List[ProjectReviewResponse] = []
    quality_breakdown: Optional[Dict[str, Any]] = None


# =========================================================================
# 5. Portfolio Schemas
# =========================================================================

class PortfolioHealthResultSchema(BaseModel):
    overall_health_score: Optional[float] = None
    status: str
    technical_depth: Optional[float] = None
    project_diversity: Optional[float] = None
    evidence_quality: Optional[float] = None
    documentation_quality: Optional[float] = None
    career_alignment: Optional[float] = None
    professional_presence: Optional[float] = None
    verification_coverage: Optional[float] = None
    completeness_score: float
    missing_sections: List[str] = []
    dimension_explanations: Dict[str, Any] = {}
    recommendations: List[str] = []
    algorithm_version: str = "v1.0.0-deterministic"


PortfolioHealthResponse = PortfolioHealthResultSchema


class PortfolioUpdate(BaseModel):
    headline: Optional[str] = None
    bio: Optional[str] = None
    slug: Optional[str] = None
    theme: Optional[str] = None
    featured_project_ids: Optional[List[str]] = None
    featured_skill_ids: Optional[List[str]] = None
    featured_certification_ids: Optional[List[str]] = None
    featured_achievement_ids: Optional[List[str]] = None
    public_visibility: Optional[bool] = None
    contact_email: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    custom_links: Optional[List[Dict[str, str]]] = None


class PortfolioResponse(BaseModel):
    id: str
    student_profile_id: str
    headline: Optional[str] = None
    bio: Optional[str] = None
    slug: Optional[str] = None
    theme: str
    featured_project_ids: Optional[List[str]] = None
    featured_skill_ids: Optional[List[str]] = None
    featured_certification_ids: Optional[List[str]] = None
    featured_achievement_ids: Optional[List[str]] = None
    public_visibility: bool
    contact_email: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    custom_links: Optional[List[Dict[str, str]]] = None
    custom_domain: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PublicPortfolioResponse(BaseModel):
    student_name: str
    headline: Optional[str] = None
    bio: Optional[str] = None
    theme: str
    contact_email: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    custom_links: Optional[List[Dict[str, str]]] = None
    projects: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    certifications: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]


# =========================================================================
# 6. Skill Graph Schemas
# =========================================================================

class SkillEvidenceGraphResponse(BaseModel):
    skill_id: str
    skill_name: str
    skill_code: Optional[str] = None
    category: Optional[str] = None
    state: Dict[str, Any]
    provenance_summary: Dict[str, Any]
    concepts: List[Dict[str, Any]] = []
    courses: List[Dict[str, Any]] = []
    assessments: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []
    project_evidence: List[Dict[str, Any]] = []
    target_careers: List[Dict[str, Any]] = []


class StudentSkillGraphResponse(BaseModel):
    student_profile_id: str
    primary_career: Optional[Dict[str, Any]] = None
    career_requirements: Dict[str, Any] = {}
    total_evaluated_skills: int
    verified_skills_count: int
    unverified_skills_count: int
    skills_by_category: Dict[str, List[Dict[str, Any]]] = {}
    skills: List[Dict[str, Any]] = []
