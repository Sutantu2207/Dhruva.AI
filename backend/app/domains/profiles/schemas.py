"""Pydantic schemas for Domain 3: Student & Faculty Management, Mentorship, Profiles & Onboarding."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# =========================================================================
# 1. Student Extended Profile & Academic Status
# =========================================================================

class StudentProfileDetailUpdate(BaseModel):
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    learning_preferences: Optional[Dict[str, Any]] = None
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    github_url: Optional[str] = Field(None, max_length=255)
    website_url: Optional[str] = Field(None, max_length=255)


class StudentProfileDetailResponse(BaseModel):
    id: str
    student_profile_id: str
    headline: Optional[str] = None
    bio: Optional[str] = None
    learning_preferences: Optional[Dict[str, Any]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentAcademicStatusChangeRequest(BaseModel):
    new_status: str = Field(description="active, on_leave, suspended, graduated, withdrawn, transferred, completed, inactive")
    effective_from: date
    effective_to: Optional[date] = None
    reason: Optional[str] = None


class StudentAcademicStatusHistoryResponse(BaseModel):
    id: str
    student_profile_id: str
    old_status: str
    new_status: str
    effective_from: date
    effective_to: Optional[date] = None
    reason: Optional[str] = None
    changed_by_user_id: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 2. Student Skills, Interests & Career Goals
# =========================================================================

class StudentSkillCreate(BaseModel):
    skill_catalog_id: str
    proficiency: str = Field(default="beginner", description="beginner, developing, intermediate, advanced, expert")
    source: str = Field(default="self_declared", description="self_declared, assessment_verified, course_verified, project_verified, faculty_verified")


class StudentSkillUpdate(BaseModel):
    proficiency: Optional[str] = Field(None, description="beginner, developing, intermediate, advanced, expert")
    source: Optional[str] = None


class StudentSkillResponse(BaseModel):
    id: str
    student_profile_id: str
    skill_catalog_id: str
    proficiency: str
    source: str
    is_verified: bool
    verified_by_user_id: Optional[str] = None
    last_assessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    skill_name: Optional[str] = None
    skill_code: Optional[str] = None
    skill_category: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class StudentInterestCreate(BaseModel):
    interest_title: str = Field(min_length=2, max_length=128)
    discipline_id: Optional[str] = None
    career_catalog_id: Optional[str] = None
    notes: Optional[str] = None


class StudentInterestResponse(BaseModel):
    id: str
    student_profile_id: str
    interest_title: str
    discipline_id: Optional[str] = None
    career_catalog_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentCareerGoalCreate(BaseModel):
    career_catalog_id: str
    priority: int = Field(default=1, ge=1, le=10)
    short_term_goals: Optional[str] = None
    long_term_goals: Optional[str] = None
    target_industry: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    target_organizations: Optional[List[str]] = None


class StudentCareerGoalUpdate(BaseModel):
    priority: Optional[int] = Field(None, ge=1, le=10)
    short_term_goals: Optional[str] = None
    long_term_goals: Optional[str] = None
    target_industry: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    target_organizations: Optional[List[str]] = None


class StudentCareerGoalResponse(BaseModel):
    id: str
    student_profile_id: str
    career_catalog_id: str
    priority: int
    short_term_goals: Optional[str] = None
    long_term_goals: Optional[str] = None
    target_industry: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    target_organizations: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    career_title: Optional[str] = None
    career_code: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 3. Student Projects, Certifications & Achievements
# =========================================================================

class StudentProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    project_type: str = Field(default="academic", description="academic, capstone, internship, hackathon, personal, research")
    status: str = Field(default="in_progress", description="planned, in_progress, completed, archived")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    repository_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    documentation_url: Optional[str] = Field(None, max_length=500)
    technologies: Optional[List[str]] = None
    team_or_individual: str = Field(default="individual", description="individual, team")
    role: Optional[str] = Field(None, max_length=128)
    outcomes: Optional[str] = None
    skill_catalog_ids: Optional[List[str]] = None


class StudentProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    repository_url: Optional[str] = None
    demo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    technologies: Optional[List[str]] = None
    team_or_individual: Optional[str] = None
    role: Optional[str] = None
    outcomes: Optional[str] = None
    skill_catalog_ids: Optional[List[str]] = None


class StudentProjectResponse(BaseModel):
    id: str
    student_profile_id: str
    title: str
    description: Optional[str] = None
    project_type: str
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    repository_url: Optional[str] = None
    demo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    technologies: Optional[List[str]] = None
    team_or_individual: str
    role: Optional[str] = None
    outcomes: Optional[str] = None
    is_verified: bool
    verified_by_user_id: Optional[str] = None
    skill_ids: List[str] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentCertificationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    issuer: str = Field(min_length=2, max_length=255)
    credential_id: Optional[str] = Field(None, max_length=128)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_url: Optional[str] = Field(None, max_length=500)
    document_reference: Optional[str] = Field(None, max_length=500)


class StudentCertificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    issuer: Optional[str] = None
    credential_id: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_url: Optional[str] = None
    document_reference: Optional[str] = None


class StudentCertificationVerifyRequest(BaseModel):
    status: str = Field(description="verified, rejected, pending")
    verification_notes: Optional[str] = None


class StudentCertificationResponse(BaseModel):
    id: str
    student_profile_id: str
    title: str
    issuer: str
    credential_id: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_url: Optional[str] = None
    document_reference: Optional[str] = None
    status: str
    verified_by_user_id: Optional[str] = None
    verification_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentAchievementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    category: str = Field(default="competition", description="hackathon, competition, award, academic, publication, leadership, extracurricular")
    achievement_date: Optional[date] = None
    issuer_event: Optional[str] = Field(None, max_length=255)
    evidence_url: Optional[str] = Field(None, max_length=500)


class StudentAchievementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    achievement_date: Optional[date] = None
    issuer_event: Optional[str] = None
    evidence_url: Optional[str] = None


class StudentAchievementResponse(BaseModel):
    id: str
    student_profile_id: str
    title: str
    description: Optional[str] = None
    category: str
    achievement_date: Optional[date] = None
    issuer_event: Optional[str] = None
    evidence_url: Optional[str] = None
    is_verified: bool
    verified_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 4. Student Portfolio & Resume
# =========================================================================

class StudentPortfolioUpdate(BaseModel):
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    featured_project_ids: Optional[List[str]] = None
    featured_skill_ids: Optional[List[str]] = None
    public_visibility: Optional[bool] = None
    custom_links: Optional[List[Dict[str, str]]] = None


class StudentPortfolioResponse(BaseModel):
    id: str
    student_profile_id: str
    headline: Optional[str] = None
    bio: Optional[str] = None
    featured_project_ids: Optional[List[str]] = None
    featured_skill_ids: Optional[List[str]] = None
    public_visibility: bool = False
    custom_links: Optional[List[Dict[str, str]]] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StudentResumeUpdate(BaseModel):
    summary: Optional[str] = None
    selected_project_ids: Optional[List[str]] = None
    selected_skill_ids: Optional[List[str]] = None
    selected_certification_ids: Optional[List[str]] = None
    selected_achievement_ids: Optional[List[str]] = None
    experience_entries: Optional[List[Dict[str, Any]]] = None
    custom_sections: Optional[Dict[str, Any]] = None


class StudentResumeResponse(BaseModel):
    id: str
    student_profile_id: str
    summary: Optional[str] = None
    selected_project_ids: Optional[List[str]] = None
    selected_skill_ids: Optional[List[str]] = None
    selected_certification_ids: Optional[List[str]] = None
    selected_achievement_ids: Optional[List[str]] = None
    experience_entries: Optional[List[Dict[str, Any]]] = None
    custom_sections: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 5. Faculty Profile Detail
# =========================================================================

class TeacherProfileDetailUpdate(BaseModel):
    biography: Optional[str] = None
    experience_years: Optional[float] = Field(None, ge=0.0, le=70.0)
    qualifications: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    office_location: Optional[str] = Field(None, max_length=128)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)


class TeacherProfileDetailResponse(BaseModel):
    id: str
    teacher_profile_id: str
    biography: Optional[str] = None
    experience_years: Optional[float] = None
    qualifications: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    office_location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 6. Mentorship Schemas
# =========================================================================

class MentorshipRelationCreate(BaseModel):
    student_profile_id: str
    mentor_user_id: str
    start_date: date = Field(default_factory=date.today)
    assignment_source: str = Field(default="admin_assigned", description="admin_assigned, hod_assigned, system_assigned")


class MentorshipRelationResponse(BaseModel):
    id: str
    institution_id: str
    mentor_user_id: str
    student_profile_id: str
    start_date: date
    end_date: Optional[date] = None
    status: str
    assignment_source: str
    created_at: datetime
    updated_at: datetime
    student_name: Optional[str] = None
    student_enrollment_number: Optional[str] = None
    mentor_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class MentorGroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    description: Optional[str] = None
    department_id: Optional[str] = None
    mentor_user_id: str


class MentorGroupAddStudentRequest(BaseModel):
    student_profile_id: str


class MentorGroupResponse(BaseModel):
    id: str
    institution_id: str
    department_id: Optional[str] = None
    mentor_user_id: str
    name: str
    description: Optional[str] = None
    status: str
    member_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MentorNoteCreate(BaseModel):
    student_profile_id: str
    content: str = Field(min_length=1)
    visibility: str = Field(default="private_mentor", description="private_mentor, shared_faculty, institutional_admin")
    follow_up_date: Optional[date] = None


class MentorNoteUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    visibility: Optional[str] = None
    follow_up_date: Optional[date] = None
    status: Optional[str] = Field(None, description="open, resolved, archived")


class MentorNoteResponse(BaseModel):
    id: str
    institution_id: str
    mentor_user_id: str
    student_profile_id: str
    content: str
    visibility: str
    follow_up_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 7. Follow-Up / Intervention Schemas
# =========================================================================

class StudentInterventionCreate(BaseModel):
    student_profile_id: str
    category: str = Field(default="academic_support", description="academic_support, attendance_support, course_support, career_support, project_support, administrative_support")
    priority: str = Field(default="medium", description="low, medium, high, urgent")
    reason: str = Field(min_length=2)
    action_plan: Optional[str] = None
    follow_up_date: Optional[date] = None


class StudentInterventionUpdate(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = Field(None, description="open, in_progress, resolved, closed")
    reason: Optional[str] = None
    action_plan: Optional[str] = None
    follow_up_date: Optional[date] = None


class StudentInterventionResolveRequest(BaseModel):
    resolution_notes: str = Field(min_length=2)


class StudentInterventionResponse(BaseModel):
    id: str
    institution_id: str
    student_profile_id: str
    created_by_user_id: str
    category: str
    priority: str
    status: str
    reason: str
    action_plan: Optional[str] = None
    follow_up_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    resolved_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# 8. Dashboard Data Contracts
# =========================================================================

class StudentDashboardOverview(BaseModel):
    user_id: str
    student_profile_id: str
    enrollment_number: str
    academic_status: str
    institution_name: str
    program_name: str
    batch_name: str
    section_name: Optional[str] = None
    completion_percentage: float
    completed_sections: List[str]
    missing_sections: List[str]
    active_courses_count: int
    total_skills_count: int
    verified_skills_count: int
    projects_count: int
    certifications_count: int
    achievements_count: int
    mentor_name: Optional[str] = None
    active_interventions_count: int


class FacultyDashboardOverview(BaseModel):
    user_id: str
    teacher_profile_id: str
    employee_id: str
    designation: str
    department_name: str
    institution_name: str
    assigned_offerings_count: int
    total_enrolled_students: int
    assigned_mentees_count: int
    pending_follow_ups_count: int
    profile_status: str


class AdminInstitutionOverview(BaseModel):
    institution_id: str
    institution_name: str
    total_students: int
    total_faculty: int
    active_programs: int
    active_batches: int
    total_sections: int
    total_courses: int
    status_distribution: Dict[str, int]
    pending_onboarding_jobs: int


# =========================================================================
# 9. Bulk Onboarding & Import Schemas
# =========================================================================

class OnboardingImportRequest(BaseModel):
    import_type: str = Field(description="students or faculty")
    file_name: str
    is_dry_run: bool = False
    records: List[Dict[str, Any]]


class OnboardingImportJobResponse(BaseModel):
    id: str
    institution_id: str
    import_type: str
    file_name: str
    is_dry_run: bool
    status: str
    total_records: int
    successful_records: int
    duplicate_records: int
    failed_records: int
    errors: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
