/**
 * Type definitions for Domain 8: Project Intelligence, Evidence Graph & Portfolio Engine.
 */

export interface ProjectSkillItem {
  id: string;
  project_id: string;
  skill_catalog_id: string;
  skill_name?: string;
  skill_category?: string;
  claimed_level: string; // beginner, intermediate, advanced, expert
  observed_level?: string;
  evidence_strength: number;
  verification_status: 'unverified' | 'submitted' | 'under_review' | 'verified' | 'rejected';
  verified_by_user_id?: string;
  verified_at?: string;
  source: string;
  notes?: string;
}

export interface ProjectConceptItem {
  id: string;
  project_id: string;
  concept_id: string;
  concept_name?: string;
  demonstrated_level: string;
  verification_status: string;
  verified_by_user_id?: string;
  verified_at?: string;
  notes?: string;
}

export interface ProjectEvidenceItem {
  id: string;
  project_id: string;
  student_profile_id: string;
  evidence_type:
    | 'repository'
    | 'commit'
    | 'pull_request'
    | 'deployment'
    | 'documentation'
    | 'demo'
    | 'screenshot'
    | 'video'
    | 'test_report'
    | 'architecture_diagram'
    | 'faculty_review'
    | 'mentor_review'
    | 'assessment'
    | 'project_submission';
  source: string;
  source_reference: string;
  title: string;
  description?: string;
  submitted_at: string;
  verification_status: 'submitted' | 'under_review' | 'verified' | 'rejected' | 'expired';
  verified_by_user_id?: string;
  verified_at?: string;
  evidence_strength: number;
  metadata_json?: Record<string, unknown>;
  algorithm_version?: string;
}

export interface ProjectReviewItem {
  id: string;
  project_id: string;
  reviewer_user_id: string;
  reviewer_name?: string;
  review_type: string;
  technical_depth: number;
  problem_solving: number;
  code_quality: number;
  architecture_quality: number;
  documentation_quality: number;
  testing_quality: number;
  practical_application: number;
  originality: number;
  student_contribution_score: number;
  professional_presentation: number;
  overall_score: number;
  rubric_breakdown: Record<string, number>;
  feedback?: string;
  decision: 'approved' | 'rejected' | 'revisions_requested';
  is_finalized: boolean;
  reviewed_at: string;
}

export interface ProjectQualityScore {
  overall_score: number;
  technical_depth: number;
  implementation_quality: number;
  documentation_quality: number;
  testing_quality: number;
  architecture_quality: number;
  verification_strength: number;
  dimension_breakdown: Record<string, unknown>;
  missing_elements: string[];
  algorithm_version: string;
}

export interface CareerRelevanceItem {
  project_id: string;
  career_id: string;
  career_title: string;
  relevance_score: number;
  relevance_tier: 'high' | 'medium' | 'low' | 'none';
  matched_skills_count: number;
  critical_skills_matched: string[];
  missing_critical_skills: string[];
  explanation: string;
  algorithm_version: string;
}

export interface StudentProjectSummary {
  id: string;
  student_profile_id: string;
  title: string;
  slug?: string;
  short_description?: string;
  description?: string;
  problem_statement?: string;
  solution?: string;
  project_type:
    | 'academic'
    | 'personal'
    | 'hackathon'
    | 'internship'
    | 'capstone'
    | 'research'
    | 'open_source'
    | 'freelance'
    | 'startup'
    | 'competition'
    | 'other';
  status: 'draft' | 'in_progress' | 'completed' | 'archived';
  start_date?: string;
  end_date?: string;
  repository_url?: string;
  live_url?: string;
  demo_url?: string;
  documentation_url?: string;
  technologies: string[];
  visibility: 'private' | 'institution' | 'public';
  team_or_individual: 'individual' | 'team';
  role?: string;
  team_size: number;
  contribution_description?: string;
  contribution_percentage?: number;
  modules_contributed?: string[];
  verification_status: 'unverified' | 'submitted' | 'under_review' | 'verified' | 'rejected';
  is_verified: boolean;
  verified_by_user_id?: string;
  quality_score?: number;
  career_relevance_score?: number;
  career_relevance_category?: 'high' | 'medium' | 'low' | 'none';
  created_at: string;
  updated_at: string;
}

export interface StudentProjectDetail extends StudentProjectSummary {
  skills: ProjectSkillItem[];
  concepts: ProjectConceptItem[];
  evidence: ProjectEvidenceItem[];
  reviews: ProjectReviewItem[];
  quality_breakdown?: Record<string, unknown>;
}

export interface CreateProjectPayload {
  title: string;
  description?: string;
  short_description?: string;
  problem_statement?: string;
  solution?: string;
  project_type?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  repository_url?: string;
  live_url?: string;
  demo_url?: string;
  documentation_url?: string;
  technologies?: string[];
  team_or_individual?: string;
  role?: string;
  team_size?: number;
  contribution_description?: string;
  contribution_percentage?: number;
  modules_contributed?: string[];
  visibility?: 'private' | 'institution' | 'public';
  skill_ids?: string[];
  concept_ids?: string[];
}

export type UpdateProjectPayload = Partial<CreateProjectPayload>;

export interface SubmitEvidencePayload {
  evidence_type: string;
  source: string;
  source_reference: string;
  title: string;
  description?: string;
  evidence_strength?: number;
  metadata_json?: Record<string, unknown>;
}

export interface SubmitReviewPayload {
  review_type?: string;
  technical_depth?: number;
  problem_solving?: number;
  code_quality?: number;
  architecture_quality?: number;
  documentation_quality?: number;
  testing_quality?: number;
  practical_application?: number;
  originality?: number;
  student_contribution_score?: number;
  professional_presentation?: number;
  feedback?: string;
  decision?: 'approved' | 'rejected' | 'revisions_requested';
}

export interface PortfolioHealthData {
  overall_health_score: number | null;
  status: 'assessed' | 'insufficient_evidence';
  technical_depth: number | null;
  project_diversity: number | null;
  evidence_quality: number | null;
  documentation_quality: number | null;
  career_alignment: number | null;
  professional_presence: number | null;
  verification_coverage: number | null;
  completeness_score: number;
  missing_sections: string[];
  dimension_explanations: Record<string, unknown>;
  recommendations: string[];
  algorithm_version: string;
}

export interface StudentPortfolioConfig {
  id: string;
  student_profile_id: string;
  headline?: string;
  bio?: string;
  slug?: string;
  theme: string;
  featured_project_ids: string[];
  featured_skill_ids: string[];
  featured_certification_ids: string[];
  featured_achievement_ids: string[];
  public_visibility: boolean;
  contact_email?: string;
  social_links: Record<string, string>;
  custom_links: Array<{ title: string; url: string }>;
  custom_domain?: string;
  created_at: string;
  updated_at: string;
}

export interface PublicPortfolioData {
  student_name: string;
  headline?: string;
  bio?: string;
  theme: string;
  contact_email?: string;
  social_links?: Record<string, string>;
  custom_links?: Array<{ title: string; url: string }>;
  projects: Array<{
    id: string;
    title: string;
    short_description?: string;
    project_type: string;
    technologies: string[];
    repository_url?: string;
    live_url?: string;
    quality_score?: number;
    is_verified: boolean;
  }>;
  skills: Array<{ name: string; proficiency: string; category?: string }>;
  certifications: Array<{ title: string; issuer: string; credential_url?: string; issue_date?: string }>;
  achievements: Array<{ title: string; category: string; issuer_event?: string }>;
}

export interface SkillEvidenceGraphData {
  skill_id: string;
  skill_name: string;
  skill_code?: string;
  category?: string;
  state: {
    observed_proficiency: number;
    verified_proficiency: number;
    confidence: number;
    verification_status: string;
    proficiency_tier: string;
  };
  provenance_summary: {
    assessments_count: number;
    mastered_concepts_count: number;
    courses_count: number;
    projects_count: number;
    verified_projects_count: number;
    project_evidence_items_count: number;
  };
  concepts: Array<{
    concept_id: string;
    concept_name: string;
    weight: number;
    is_core: boolean;
    mastery: number;
    classification: string;
  }>;
  courses: Array<{
    course_id: string;
    course_code: string;
    course_title: string;
    weight: number;
  }>;
  assessments: Array<{
    evidence_id: string;
    assessment_title?: string;
    score: number;
    verified_at?: string;
  }>;
  projects: Array<{
    project_id: string;
    project_title: string;
    project_type: string;
    is_verified: boolean;
    claimed_level: string;
    evidence_strength: number;
    quality_score?: number;
  }>;
  project_evidence: Array<{
    evidence_id: string;
    project_id: string;
    evidence_type: string;
    title: string;
    source: string;
    source_reference: string;
    verification_status: string;
    evidence_strength: number;
  }>;
  target_careers: Array<{
    career_id: string;
    career_title: string;
    importance: string;
    weight: number;
  }>;
}

export interface StudentSkillGraphData {
  student_profile_id: string;
  primary_career?: {
    id: string;
    title: string;
    code: string;
  };
  career_requirements: Record<string, unknown>;
  total_evaluated_skills: number;
  verified_skills_count: number;
  unverified_skills_count: number;
  skills_by_category: Record<string, unknown[]>;
  skills: Array<{
    skill_id: string;
    name: string;
    code: string;
    category: string;
    tier: string;
    observed_proficiency: number;
    verified_proficiency: number;
    confidence: number;
    verification_status: string;
    is_career_required: boolean;
    importance?: string;
    has_project_evidence: boolean;
    projects_count: number;
  }>;
}

export interface ProjectGapStrengtheningItem {
  project_id: string;
  title: string;
  project_type: string;
  matching_gap_skills: string[];
  relevance_score: number;
}

export interface ProjectInsufficientEvidenceItem {
  project_id: string;
  title: string;
  project_type: string;
  total_skills: number;
  verified_evidence_count: number;
  missing_elements: string[];
}
