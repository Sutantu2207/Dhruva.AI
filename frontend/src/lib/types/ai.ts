/**
 * Dhruva.AI Domain 11 — System-wide AI Orchestration & Natural Language Layer
 * Type Definitions
 */

export type AIConversationScope = 'STUDENT' | 'FACULTY' | 'MENTOR' | 'HOD' | 'PLACEMENT' | 'ADMIN';

export type AIConversationalMode = 'EXPLAIN' | 'SOCRATIC' | 'PRACTICE' | 'REVIEW' | 'EXAM_PREP' | 'PROJECT_GUIDANCE';

export type AIMessageRole = 'USER' | 'ASSISTANT' | 'SYSTEM' | 'TOOL';

export interface AIRetrievalCitation {
  id: string;
  source_type: string;
  source_id: string;
  title: string;
  chunk_id: string | null;
  relevance_score: number;
}

export interface AIToolInvocation {
  id: string;
  tool_name: string;
  result_summary: Record<string, unknown>;
  status: string;
  latency_ms: number;
}

export interface AIMessage {
  id: string;
  conversation_id: string;
  role: AIMessageRole;
  content: string;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  status: string;
  created_at: string;
  citations?: AIRetrievalCitation[];
  tool_invocations?: AIToolInvocation[];
}

export interface AIConversation {
  id: string;
  user_id: string;
  scope: AIConversationScope;
  title: string;
  mode: AIConversationalMode;
  context_ref: Record<string, unknown> | null;
  status: string;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  messages?: AIMessage[];
}

export interface AIConversationCreate {
  scope: AIConversationScope;
  title?: string;
  mode?: AIConversationalMode;
  context_ref?: Record<string, unknown>;
}

export interface AIMessageCreate {
  content: string;
  context_ref?: Record<string, unknown>;
}

export interface AIFeedbackCreate {
  message_id: string;
  rating: number; // 1 (thumbs up) or -1 (thumbs down)
  reason?: string;
}

export interface AITrustManifest {
  product_principle: string;
  deterministic_authority: string;
  source_of_truth_domains: Record<string, string>;
  model_safety_invariants: string[];
  privacy_and_redaction: string[];
  algorithm_version: string;
}

export interface AIUsageMetrics {
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  records_count: number;
}
