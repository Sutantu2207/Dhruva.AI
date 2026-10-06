/**
 * Domain 7 — Skill Intelligence, Career Trajectory & Placement Readiness Types
 * All fields are deterministic, backend-derived, and versioned.
 */

export type ProficiencyTier =
  | "exposure"
  | "beginner"
  | "developing"
  | "proficient"
  | "advanced";

export type VerificationStatus =
  | "unverified"
  | "developing"
  | "demonstrated"
  | "verified";

export type GapSeverity = "critical" | "high" | "medium" | "low" | "none";

export type TrajectoryStepStatus =
  | "not_started"
  | "in_progress"
  | "completed"
  | "blocked"
  | "not_available";

export type PlacementStatus =
  | "not_yet_assessed"
  | "needs_portfolio"
  | "assessing"
  | "ready_for_review"
  | "placement_ready";

export interface StudentSkillEvidenceRecord {
  id: string;
  skill_id: string;
  source_type: string;
  source_id?: string | null;
  raw_score?: number | null;
  normalized_score: number;
  evidence_strength: number;
  weight: number;
  verified: boolean;
  recorded_at: string;
  metadata?: Record<string, unknown> | null;
}

export interface StudentSkillIntelligence {
  id: string;
  student_profile_id: string;
  skill_id: string;
  skill_name: string;
  skill_code: string;
  skill_slug: string;
  observed_proficiency: number;
  self_reported_proficiency?: number | null;
  verified_proficiency: number;
  confidence: number;
  proficiency_tier: ProficiencyTier;
  verification_status: VerificationStatus;
  evidence_count: number;
  verified_evidence_count: number;
  assessment_evidence_count: number;
  project_evidence_count: number;
  course_evidence_count: number;
  certification_evidence_count: number;
  concept_mastery_contribution: number;
  last_evaluated_at: string;
  algorithm_version: string;
  evidence_records?: StudentSkillEvidenceRecord[];
}

export interface SkillGap {
  skill_id: string;
  skill_name: string;
  skill_code: string;
  current_proficiency: number;
  required_proficiency: number;
  gap_size: number;
  severity: GapSeverity;
  priority: number;
  reason: string;
  confidence: number;
}

export interface StudentCareerReadiness {
  id: string;
  student_profile_id: string;
  career_id: string;
  career_title: string;
  career_slug: string;
  readiness_score: number;
  confidence: number;
  required_skill_coverage: number;
  preferred_skill_coverage: number;
  critical_skill_coverage: number;
  critical_gaps_count: number;
  evaluated_at: string;
  algorithm_version: string;
  gaps: SkillGap[];
  strengths: StudentSkillIntelligence[];
  developing: StudentSkillIntelligence[];
}

export interface CareerTrajectoryStep {
  id: string;
  step_order: number;
  title: string;
  description?: string | null;
  step_type: string;
  skill_id?: string | null;
  skill_name?: string | null;
  concept_id?: string | null;
  concept_title?: string | null;
  lesson_id?: string | null;
  lesson_title?: string | null;
  course_id?: string | null;
  course_title?: string | null;
  assessment_id?: string | null;
  status: TrajectoryStepStatus;
  priority: number;
  reason?: string | null;
}

export interface CareerTrajectory {
  id: string;
  student_profile_id: string;
  career_id: string;
  career_title: string;
  status: string;
  created_at: string;
  updated_at: string;
  algorithm_version: string;
  steps: CareerTrajectoryStep[];
}

export interface CareerFit {
  career_id: string;
  career_title: string;
  fit_score?: number | null;
  basis: string;
  assessed: boolean;
}

export interface PlacementReadiness {
  id: string;
  student_profile_id: string;
  overall_status: PlacementStatus;
  technical_readiness?: number | null;
  assessment_readiness?: number | null;
  project_evidence?: number | null;
  communication_readiness?: number | null;
  resume_readiness?: number | null;
  interview_readiness?: number | null;
  assessed_components_count: number;
  total_components_count: number;
  evaluated_at: string;
  algorithm_version: string;
}

export interface CareerIntelligenceOverview {
  career?: {
    id: string;
    title: string;
    slug: string;
    description?: string | null;
  } | null;
  fit?: CareerFit | null;
  readiness?: StudentCareerReadiness | null;
  placement?: PlacementReadiness | null;
  strengths: StudentSkillIntelligence[];
  developing: StudentSkillIntelligence[];
  gaps: SkillGap[];
  trajectory: CareerTrajectoryStep[];
  has_career_goal: boolean;
  message: string;
}

export interface CareerComparisonItem {
  career_id: string;
  career_title: string;
  career_slug: string;
  readiness_score: number;
  confidence: number;
  required_skill_coverage: number;
  preferred_skill_coverage: number;
  critical_skill_coverage: number;
  critical_gaps_count: number;
  total_skills_count: number;
  strengths_count: number;
  gaps_count: number;
}
