"""Deterministic Profile Completion Calculation Engine.

Pure deterministic logic calculating student profile completion from stored records.
Guarantees identical outputs for identical domain states.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ProfileSectionStatus(BaseModel):
    name: str
    weight: float
    is_completed: bool
    summary: str


class ProfileCompletionReport(BaseModel):
    completion_percentage: float = Field(ge=0.0, le=100.0)
    completed_sections: List[str]
    missing_sections: List[str]
    section_breakdown: List[ProfileSectionStatus]
    last_updated: datetime


def calculate_profile_completion(
    academic_profile: Any,
    profile_detail: Optional[Any] = None,
    skills_count: int = 0,
    career_goals_count: int = 0,
    interests_count: int = 0,
    projects_count: int = 0,
    certifications_count: int = 0,
    portfolio: Optional[Any] = None,
    resume: Optional[Any] = None,
) -> ProfileCompletionReport:
    """Calculates deterministic profile completion score across 8 standard sections."""

    sections: List[ProfileSectionStatus] = []

    # 1. Academic Affiliation (Weight: 20%) - Core institutional foundation
    has_academic = bool(
        academic_profile
        and getattr(academic_profile, "institution_id", None)
        and getattr(academic_profile, "program_id", None)
        and getattr(academic_profile, "batch_id", None)
        and getattr(academic_profile, "enrollment_number", None)
    )
    sections.append(
        ProfileSectionStatus(
            name="Academic Profile",
            weight=20.0,
            is_completed=has_academic,
            summary="Program, batch cohort, and enrollment identifier confirmed." if has_academic else "Missing institutional enrollment setup.",
        )
    )

    # 2. Basic Biographical Profile (Weight: 10%)
    has_bio = bool(
        profile_detail
        and (
            getattr(profile_detail, "headline", None)
            or getattr(profile_detail, "bio", None)
            or getattr(profile_detail, "contact_email", None)
        )
    )
    sections.append(
        ProfileSectionStatus(
            name="Basic Profile",
            weight=10.0,
            is_completed=has_bio,
            summary="Headline and bio details added." if has_bio else "Add your professional headline and bio.",
        )
    )

    # 3. Skills Taxonomy (Weight: 15%)
    has_skills = skills_count > 0
    sections.append(
        ProfileSectionStatus(
            name="Skills",
            weight=15.0,
            is_completed=has_skills,
            summary=f"{skills_count} skill(s) recorded." if has_skills else "Map at least one technical or professional skill.",
        )
    )

    # 4. Career Interests & Target Goals (Weight: 15%)
    has_career = (career_goals_count > 0) or (interests_count > 0)
    sections.append(
        ProfileSectionStatus(
            name="Career Goals",
            weight=15.0,
            is_completed=has_career,
            summary="Target career goals or exploratory interests configured." if has_career else "Specify target industry careers and learning interests.",
        )
    )

    # 5. Technical & Capstone Projects (Weight: 15%)
    has_projects = projects_count > 0
    sections.append(
        ProfileSectionStatus(
            name="Projects",
            weight=15.0,
            is_completed=has_projects,
            summary=f"{projects_count} project(s) documented." if has_projects else "Document at least one academic, internship, or personal project.",
        )
    )

    # 6. Certifications (Weight: 10%)
    has_certs = certifications_count > 0
    sections.append(
        ProfileSectionStatus(
            name="Certifications",
            weight=10.0,
            is_completed=has_certs,
            summary=f"{certifications_count} credential(s) added." if has_certs else "Add relevant certificates, credentials, or courses.",
        )
    )

    # 7. Portfolio (Weight: 7.5%)
    has_portfolio = bool(
        portfolio
        and (
            getattr(portfolio, "headline", None)
            or getattr(portfolio, "bio", None)
            or getattr(portfolio, "public_visibility", False)
            or (getattr(portfolio, "featured_project_ids", None) and len(portfolio.featured_project_ids) > 0)
        )
    )
    sections.append(
        ProfileSectionStatus(
            name="Portfolio",
            weight=7.5,
            is_completed=has_portfolio,
            summary="Portfolio customized." if has_portfolio else "Curate featured projects and public visibility.",
        )
    )

    # 8. Resume Profile (Weight: 7.5%)
    has_resume = bool(
        resume
        and (
            getattr(resume, "summary", None)
            or (getattr(resume, "selected_project_ids", None) and len(resume.selected_project_ids) > 0)
            or (getattr(resume, "selected_skill_ids", None) and len(resume.selected_skill_ids) > 0)
        )
    )
    sections.append(
        ProfileSectionStatus(
            name="Resume",
            weight=7.5,
            is_completed=has_resume,
            summary="Structured resume curated." if has_resume else "Configure structured resume highlights and summary.",
        )
    )

    # Calculate score
    total_score = sum(s.weight for s in sections if s.is_completed)
    completed_names = [s.name for s in sections if s.is_completed]
    missing_names = [s.name for s in sections if not s.is_completed]

    return ProfileCompletionReport(
        completion_percentage=round(total_score, 1),
        completed_sections=completed_names,
        missing_sections=missing_names,
        section_breakdown=sections,
        last_updated=datetime.now(timezone.utc),
    )
