/**
 * Domain 5: Assessment Engine, Question Banks, Evaluation & Deterministic Evidence
 * TypeScript Definitions
 */

export type QuestionType =
  | "single_choice"
  | "multiple_choice"
  | "true_false"
  | "fill_blank"
  | "short_answer"
  | "long_answer"
  | "coding"
  | "numeric"
  | "ordering"
  | "matching"
  | "case_study";

export type QuestionStatus = "draft" | "in_review" | "approved" | "archived";
export type QuestionDifficulty = "easy" | "medium" | "hard" | "expert";

export type AssessmentType =
  | "practice"
  | "quiz"
  | "assignment"
  | "diagnostic"
  | "internal"
  | "midterm"
  | "end_semester"
  | "mock_exam"
  | "placement_test"
  | "skill_assessment"
  | "custom";

export type AssessmentStatus =
  | "draft"
  | "scheduled"
  | "open"
  | "closed"
  | "graded"
  | "archived";

export type AttemptStatus =
  | "not_started"
  | "in_progress"
  | "submitted"
  | "under_evaluation"
  | "evaluated"
  | "cancelled"
  | "expired";

export type ResultReleaseStatus = "draft_result" | "internal" | "released" | "recalled";

export interface QuestionBank {
  id: string;
  institution_id: string;
  owner_id: string;
  department_id?: string | null;
  course_id?: string | null;
  title: string;
  description?: string | null;
  status: string;
  visibility: string;
  created_at: string;
  updated_at: string;
}

export interface QuestionOption {
  id: string;
  question_version_id: string;
  option_text: string;
  option_order: number;
  is_correct?: boolean;
  explanation?: string | null;
  metadata_json?: Record<string, unknown> | null;
}

export interface QuestionConcept {
  id: string;
  question_version_id: string;
  concept_id: string;
  importance: string;
  weight: number;
  is_primary: boolean;
  concept_name?: string;
}

export interface QuestionSkill {
  id: string;
  question_version_id: string;
  skill_id: string;
  weight: number;
  evidence_type: string;
  skill_title?: string;
}

export interface QuestionVersion {
  id: string;
  question_id: string;
  version_number: number;
  prompt: string;
  instructions?: string | null;
  difficulty: QuestionDifficulty;
  points: number;
  negative_marks: number;
  estimated_time_minutes?: number | null;
  explanation?: string | null;
  options: QuestionOption[];
  concepts: QuestionConcept[];
  skills: QuestionSkill[];
  evaluation_config?: Record<string, unknown> | null;
  is_current: boolean;
  author_id?: string | null;
  reviewer_id?: string | null;
  created_at: string;
}

export interface Question {
  id: string;
  question_bank_id: string;
  question_type: QuestionType;
  title: string;
  status: QuestionStatus;
  current_version_id?: string | null;
  current_version?: QuestionVersion | null;
  created_at: string;
  updated_at: string;
}

export interface AssessmentQuestionItem {
  id: string;
  question_version_id: string;
  section_name?: string | null;
  order_index: number;
  points: number;
  negative_marks: number;
  is_mandatory: boolean;
  question_version?: QuestionVersion | null;
}

export interface AssessmentVersion {
  id: string;
  assessment_id: string;
  version_number: number;
  title: string;
  duration_minutes: number;
  total_marks: number;
  passing_marks: number;
  blueprint_id?: string | null;
  is_active: boolean;
  questions: AssessmentQuestionItem[];
  created_at: string;
}

export interface Assessment {
  id: string;
  institution_id: string;
  course_offering_id: string;
  title: string;
  description?: string | null;
  instructions?: string | null;
  assessment_type: AssessmentType;
  status: AssessmentStatus;
  duration_minutes: number;
  total_marks: number;
  passing_marks: number;
  attempts_allowed: number;
  randomization_settings?: Record<string, unknown> | null;
  feedback_policy: string;
  start_at?: string | null;
  end_at?: string | null;
  late_submission_policy?: Record<string, unknown> | null;
  active_version_id?: string | null;
  active_version?: AssessmentVersion | null;
  created_by_id?: string | null;
  reviewed_by_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttemptDeliveryOption {
  id: string;
  option_text: string;
  option_order: number;
}

export interface AttemptDeliveryQuestion {
  question_version_id: string;
  section_name?: string | null;
  order_index: number;
  question_type: QuestionType;
  title: string;
  prompt: string;
  instructions?: string | null;
  points: number;
  negative_marks: number;
  options: AttemptDeliveryOption[];
  allowed_interaction?: Record<string, unknown> | null;
}

export interface AttemptDelivery {
  attempt_id: string;
  assessment_title: string;
  assessment_type: string;
  started_at: string;
  expires_at: string;
  duration_minutes: number;
  questions: AttemptDeliveryQuestion[];
}

export interface AssessmentAttempt {
  id: string;
  assessment_version_id: string;
  student_id: string;
  attempt_number: number;
  started_at: string;
  submitted_at?: string | null;
  expires_at: string;
  status: AttemptStatus;
  total_score?: number | null;
  percentage?: number | null;
  result_status: string;
}

export interface AssessmentResponse {
  id: string;
  attempt_id: string;
  question_version_id: string;
  response_payload: Record<string, unknown>;
  answered_at: string;
  is_final: boolean;
}

export interface QuestionResultBreakdown {
  question_version_id: string;
  question_title?: string;
  question_type?: string;
  earned_marks: number;
  maximum_marks: number;
  evaluator_type: string;
  evaluation_details?: Record<string, unknown> | null;
  explanation?: string | null;
}

export interface ConceptEvidence {
  id: string;
  student_id: string;
  question_version_id: string;
  assessment_id: string;
  concept_id: string;
  score: number;
  evidence_type: string;
  recorded_at: string;
}

export interface SkillEvidence {
  id: string;
  student_id: string;
  question_version_id: string;
  assessment_id: string;
  skill_id: string;
  score: number;
  evidence_type: string;
  recorded_at: string;
}

export interface AssessmentResult {
  id: string;
  attempt_id: string;
  student_id: string;
  assessment_id: string;
  raw_marks: number;
  maximum_marks: number;
  percentage: number;
  grade?: string | null;
  passed: boolean;
  release_status: ResultReleaseStatus;
  released_at?: string | null;
  evaluated_at: string;
  question_breakdown: QuestionResultBreakdown[];
  concept_evidence: ConceptEvidence[];
  skill_evidence: SkillEvidence[];
}
