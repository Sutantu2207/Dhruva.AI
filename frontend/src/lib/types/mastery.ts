/**
 * Domain 6: Knowledge State, Concept Mastery & Spaced Repetition (SM-2) Types
 */

export type KnowledgeStateEnum =
  | "unknown"
  | "introduced"
  | "developing"
  | "proficient"
  | "mastered"
  | "at_risk";

export type MasteryTrendEnum =
  | "strongly_improving"
  | "improving"
  | "stable"
  | "declining"
  | "strongly_declining"
  | "insufficient_data";

export type PrerequisiteHealthEnum = "healthy" | "partial" | "weak" | "unknown";

export type ReviewStatusEnum = "due" | "upcoming" | "overdue" | "completed";

export interface ConceptKnowledgeState {
  id: string;
  concept_id: string;
  concept_name?: string | null;
  concept_slug?: string | null;
  current_mastery?: number | null;
  confidence: number;
  retention_estimate: number;
  state: KnowledgeStateEnum;
  trend: MasteryTrendEnum;
  evidence_count: number;
  first_evidence_at?: string | null;
  last_evidence_at?: string | null;
  last_successful_evidence_at?: string | null;
  last_failed_evidence_at?: string | null;
  prerequisite_readiness?: number | null;
  prerequisite_health: PrerequisiteHealthEnum;
  algorithm_version: string;
  updated_at: string;
}

export interface ConceptReviewState {
  id: string;
  concept_id: string;
  concept_name?: string | null;
  repetition: number;
  ease_factor: number;
  interval_days: number;
  last_reviewed_at?: string | null;
  next_review_at: string;
  last_quality?: number | null;
  review_status: ReviewStatusEnum;
  algorithm_version: string;
}

export interface ConceptReviewCompletionPayload {
  quality: number;
  duration_seconds?: number | null;
  trigger?: string;
}

export interface LearningPriority {
  concept_id: string;
  concept_name: string;
  priority_score: number;
  reason_codes: string[];
  mastery_gap: number;
  retention_risk: number;
  prerequisite_readiness: number;
  recommended_task_type: string;
  reference_lesson_id?: string | null;
  reference_assessment_id?: string | null;
}

export interface DailyMissionTask {
  task_id: string;
  task_type: "review" | "practice" | "lesson" | "assessment" | "application";
  title: string;
  concept_id: string;
  concept_name: string;
  priority_score: number;
  reason_codes: string[];
  reference_id?: string | null;
  estimated_minutes: number;
}

export interface DailyMission {
  date: string;
  tasks: DailyMissionTask[];
  total_estimated_minutes: number;
}

export interface StudentKnowledgeSummary {
  student_profile_id: string;
  total_observed_concepts: number;
  mastered_count: number;
  proficient_count: number;
  developing_count: number;
  at_risk_count: number;
  unknown_count: number;
  due_reviews_count: number;
  overdue_reviews_count: number;
  average_mastery?: number | null;
  average_retention: number;
  average_confidence: number;
}

export interface ConceptPrerequisiteStatus {
  prerequisite_concept_id: string;
  prerequisite_name: string;
  relationship_type: string;
  current_mastery?: number | null;
  state: string;
}

export interface EvidenceHistoryItem {
  id: string;
  evidence_type: string;
  score: number;
  created_at: string;
  assessment_id?: string | null;
}

export interface MasteryHistoryItem {
  id: string;
  previous_mastery?: number | null;
  new_mastery?: number | null;
  change_delta?: number | null;
  trigger: string;
  created_at: string;
}

export interface ReviewHistoryItem {
  id: string;
  quality: number;
  new_interval_days: number;
  new_ease_factor: number;
  created_at: string;
}

export interface ConceptDetail {
  concept_id: string;
  concept_name: string;
  concept_slug: string;
  difficulty: string;
  knowledge_state?: ConceptKnowledgeState | null;
  review_state?: ConceptReviewState | null;
  prerequisites: ConceptPrerequisiteStatus[];
  evidence_history: EvidenceHistoryItem[];
  mastery_history: MasteryHistoryItem[];
  review_history: ReviewHistoryItem[];
}
