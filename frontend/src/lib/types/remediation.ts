/**
 * Domain 10: Autonomous Adaptive Remediation & Institutional Intelligence Closing Types
 */

export interface RemediationPlanStep {
  id: string;
  remediation_plan_id: string;
  sequence_order: number;
  step_type:
    | "PREREQUISITE"
    | "MICRO_LESSON"
    | "GUIDED_PRACTICE"
    | "PRACTICE_ASSESSMENT"
    | "APPLICATION"
    | "REASSESSMENT"
    | "REFLECTION";
  concept_id: string | null;
  lesson_id: string | null;
  resource_id: string | null;
  assessment_id: string | null;
  title: string;
  description: string | null;
  required: boolean;
  scaffold_level: number;
  completion_status: "pending" | "in_progress" | "completed" | "skipped" | "failed";
  started_at: string | null;
  completed_at: string | null;
  result_summary: Record<string, unknown> | null;
}

export interface RemediationDiagnosis {
  id: string;
  remediation_plan_id: string;
  concept_id: string;
  evidence_count: number;
  mastery_before: number | null;
  confidence_before: number;
  retention_before: number;
  prerequisite_readiness: number | null;
  failure_count: number;
  overdue_review_count: number;
  recent_performance: number | null;
  diagnosis_category: string;
  diagnosis_reason: string;
  explanation_payload: {
    diagnosis_category: string;
    mastery_before: number | null;
    confidence_before: number;
    retention_before: number;
    prerequisite_blocking_count: number;
    blocking_prerequisites: string[];
    failure_count: number;
    evidence_count: number;
    algorithm_version: string;
  };
  algorithm_version: string;
  calculated_at: string;
}

export interface RemediationOutcome {
  id: string;
  remediation_plan_id: string;
  concept_id: string;
  mastery_before: number | null;
  confidence_before: number;
  retention_before: number;
  assessment_score_before: number | null;
  mastery_after: number | null;
  confidence_after: number;
  retention_after: number;
  assessment_score_after: number | null;
  improvement_delta: number;
  outcome_status:
    | "IMPROVED"
    | "PARTIALLY_IMPROVED"
    | "NO_SIGNIFICANT_CHANGE"
    | "REGRESSED"
    | "INSUFFICIENT_EVIDENCE";
  closure_decision: "CLOSE_SUCCESS" | "CONTINUE" | "ESCALATE";
  closure_reason: string;
  algorithm_version: string;
  measured_at: string;
}

export interface RemediationPlan {
  id: string;
  student_profile_id: string;
  originating_signal_id: string | null;
  originating_intervention_id: string | null;
  target_concept_id: string;
  target_skill_id: string | null;
  target_course_offering_id: string | null;
  diagnosis_type: string;
  diagnosis_reason: string;
  priority_score: number;
  status:
    | "draft"
    | "recommended"
    | "assigned"
    | "in_progress"
    | "paused"
    | "completed"
    | "failed"
    | "closed"
    | "cancelled";
  idempotency_key: string;
  algorithm_version: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  closed_at: string | null;
  faculty_override_reason: string | null;
  faculty_reviewer_id: string | null;
  steps: RemediationPlanStep[];
  diagnoses: RemediationDiagnosis[];
  outcomes: RemediationOutcome[];
  target_concept_name?: string;
  student_name?: string;
  course_name?: string;
}

export interface InstitutionalRemediationAnalytics {
  plans_created: number;
  plans_completed: number;
  completion_rate: number;
  improvement_rate: number;
  partial_improvement_rate: number;
  no_significant_change_rate: number;
  regression_rate: number;
  average_mastery_improvement: number;
  prerequisite_bottlenecks: Array<{ name: string; count: number }>;
  concepts_highest_demand: Array<{ name: string; count: number }>;
  courses_highest_demand: Array<{ name: string; count: number }>;
  content_availability_gaps: number;
  closure_rate: number;
  algorithm_version: string;
}

export interface ContentGap {
  id: string;
  institution_id: string;
  concept_id: string;
  concept_name: string;
  course_id: string | null;
  course_name: string | null;
  demand_count: number;
  gap_type: "NO_APPROVED_LESSON" | "NO_PRACTICE_QUESTION" | "NO_REASSESSMENT";
  status: "unresolved" | "acknowledged" | "resolved";
  detected_at: string;
  resolved_at: string | null;
}

export interface AccreditationEvidence {
  id: string;
  institution_id: string;
  framework: string;
  criterion: string;
  metric_code: string;
  metric_payload: {
    framework: string;
    criterion: string;
    metric_title: string;
    evidence_indicators: {
      total_remediation_interventions: number;
      successfully_completed_interventions: number;
      completion_rate: number;
      documented_learning_improvements: number;
      improvement_success_rate: number;
      average_mastery_gain: number;
      unresolved_curriculum_content_gaps: number;
    };
    compliance_claim: string;
    algorithm_version: string;
  };
  source_domain: string;
  generated_at: string;
}
