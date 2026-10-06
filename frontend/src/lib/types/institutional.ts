/**
 * Domain 9: Institutional Analytics, Faculty Grading Workflows & Departmental Intelligence Types.
 */

export type SignalSeverity = "low" | "medium" | "high" | "urgent";
export type SignalStatus = "detected" | "acknowledged" | "dismissed" | "converted";
export type GradingQueueType = "manual_question" | "project_review" | "evidence_verification";
export type GradingQueuePriority = "low" | "medium" | "high";

export interface AcademicInterventionSignal {
  id: string;
  institution_id: string;
  student_profile_id: string;
  student_name?: string | null;
  enrollment_number?: string | null;
  course_offering_id?: string | null;
  course_code?: string | null;
  course_title?: string | null;
  signal_type: string;
  severity: SignalSeverity;
  title: string;
  evidence_data: Record<string, unknown>;
  recommended_action: string;
  status: SignalStatus;
  detected_at: string;
  acknowledged_at?: string | null;
  acknowledged_by_user_id?: string | null;
  dismiss_reason?: string | null;
  intervention_id?: string | null;
  algorithm_version: string;
}

export interface AcknowledgeSignalPayload {
  notes?: string;
}

export interface DismissSignalPayload {
  reason: string;
}

export interface ConvertSignalToInterventionPayload {
  category?: string;
  priority?: string;
  action_plan?: string;
  follow_up_date?: string;
}

export interface GradingQueueItem {
  item_id: string;
  item_type: GradingQueueType;
  priority: GradingQueuePriority;
  title: string;
  student_profile_id: string;
  student_name: string;
  enrollment_number: string;
  course_offering_id?: string | null;
  course_code?: string | null;
  course_title?: string | null;
  submitted_at: string;
  status: string;
  metadata_json?: Record<string, unknown> | null;
}

export interface RubricCriterionScorePayload {
  criterion_id: string;
  points_awarded: number;
  comments?: string;
}

export interface GradeManualQuestionPayload {
  marks_awarded: number;
  feedback?: string;
  rubric_breakdown?: RubricCriterionScorePayload[];
}

export interface RegradeEvaluationPayload {
  new_marks: number;
  reason: string;
}

export interface QuestionAnalytics {
  question_id: string;
  question_title: string;
  question_type: string;
  attempts_count: number;
  average_score?: number | null;
  accuracy_rate?: number | null;
  skip_rate?: number | null;
  review_recommended: boolean;
  review_reason?: string | null;
}

export interface AssessmentOfferingSummary {
  assessment_id: string;
  title: string;
  total_assigned: number;
  total_started: number;
  total_completed: number;
  completion_rate: number;
  average_score?: number | null;
  median_score?: number | null;
  pass_rate?: number | null;
  score_distribution: {
    "0_to_49": number;
    "50_to_69": number;
    "70_to_84": number;
    "85_to_100": number;
  };
  pending_manual_evaluations: number;
  questions: QuestionAnalytics[];
}

export interface ConceptOfferingAnalytics {
  concept_id: string;
  concept_name: string;
  average_mastery: number;
  mastery_distribution: {
    beginner: number;
    developing: number;
    proficient: number;
    advanced: number;
  };
  high_retention_risk_count: number;
  overdue_reviews_count: number;
  prerequisite_readiness_rate: number;
  is_difficult: boolean;
}

export interface CourseOfferingAnalytics {
  offering_id: string;
  course_id: string;
  course_code: string;
  course_title: string;
  section_name: string;
  enrolled_count: number;
  active_learners_count: number;
  average_lesson_progress: number;
  completion_rate: number;
  assessments_summary: AssessmentOfferingSummary[];
  concepts_analytics: ConceptOfferingAnalytics[];
  difficult_concepts: string[];
  active_intervention_signals_count: number;
  project_evidence_count: number;
  algorithm_version: string;
  calculated_at: string;
}

export interface FacultyDashboardAnalytics {
  assigned_offerings_count: number;
  total_enrolled_students: number;
  pending_grading_count: number;
  active_intervention_signals_count: number;
  recent_assessments_count: number;
  average_cohort_completion: number;
  offerings: Array<{
    offering_id: string;
    course_id: string;
    course_code: string;
    course_title: string;
    section_name: string;
    enrolled_count: number;
    completion_rate: number;
    pending_grading_count: number;
  }>;
  urgent_signals: AcademicInterventionSignal[];
}

export interface DepartmentAnalytics {
  department_id: string;
  department_name: string;
  department_code: string;
  total_programs: number;
  total_courses: number;
  total_offerings: number;
  total_faculty: number;
  total_students: number;
  average_course_completion: number;
  average_assessment_score?: number | null;
  concept_mastery_average?: number | null;
  career_readiness_average?: number | null;
  verified_projects_count: number;
  active_intervention_signals_count: number;
  interventions_by_severity: {
    urgent: number;
    high: number;
    medium: number;
    low: number;
  };
  top_difficult_concepts: Array<Record<string, unknown>>;
  algorithm_version: string;
  calculated_at: string;
}

export interface DepartmentComparisonItem {
  department_id: string;
  department_name: string;
  department_code: string;
  student_count: number;
  is_suppressed: boolean;
  completion_rate?: number | null;
  average_score?: number | null;
  concept_mastery?: number | null;
  career_readiness?: number | null;
  active_interventions?: number | null;
}

export interface DepartmentComparisonResponse {
  institution_id: string;
  minimum_cohort_size: number;
  suppression_policy: string;
  departments: DepartmentComparisonItem[];
  generated_at: string;
}

export interface PlacementAnalytics {
  institution_id: string;
  total_targetable_students: number;
  career_target_distribution: Record<string, number>;
  career_readiness_tiers: {
    ready: number;
    approaching: number;
    developing: number;
    not_assessed: number;
  };
  average_readiness_percentage?: number | null;
  systemic_skill_gaps: Array<{
    skill_name: string;
    gap_count: number;
    average_gap_severity: number;
  }>;
  verified_project_coverage_rate: number;
  portfolio_completeness_average?: number | null;
  communication_readiness_rate?: number | null;
  resume_readiness_rate?: number | null;
  algorithm_version: string;
  calculated_at: string;
}
