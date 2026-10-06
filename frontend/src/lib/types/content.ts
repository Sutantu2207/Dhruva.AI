/**
 * TypeScript Interfaces for Domain 4: Course Delivery, Curriculum Structure & Learning Content Engine
 */

export type LessonType =
  | "text"
  | "video"
  | "article"
  | "interactive"
  | "coding"
  | "quiz"
  | "assignment"
  | "project"
  | "mixed";

export type ContentBlockType =
  | "heading"
  | "paragraph"
  | "image"
  | "video"
  | "code"
  | "callout"
  | "quote"
  | "resource"
  | "embed";

export type ContentStatus = "draft" | "in_review" | "published" | "archived";
export type ProgressStatus = "not_started" | "in_progress" | "completed";

export interface ContentBlock {
  id: string;
  lesson_id: string;
  block_type: ContentBlockType;
  order_index: number;
  content: string;
  media_url?: string | null;
  block_metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Lesson {
  id: string;
  module_id: string;
  title: string;
  slug: string;
  description?: string | null;
  lesson_type: LessonType;
  order_index: number;
  estimated_minutes?: number | null;
  learning_objectives?: string[] | null;
  prerequisites?: string[] | null;
  status: string;
  content_version: number;
  is_required: boolean;
  created_at: string;
  updated_at: string;
  content_blocks: ContentBlock[];
}

export interface Module {
  id: string;
  curriculum_id: string;
  title: string;
  slug: string;
  description?: string | null;
  order_index: number;
  estimated_minutes?: number | null;
  learning_objectives?: string[] | null;
  prerequisites?: string[] | null;
  status: string;
  created_at: string;
  updated_at: string;
  lessons: Lesson[];
}

export interface Curriculum {
  id: string;
  course_content_id: string;
  title: string;
  description?: string | null;
  ordering_type: string;
  estimated_duration?: string | null;
  learning_objectives?: string[] | null;
  status: string;
  created_at: string;
  updated_at: string;
  modules: Module[];
}

export interface CourseContentDetail {
  id: string;
  institution_id: string;
  course_id: string;
  course_catalog_id?: string | null;
  title: string;
  short_description?: string | null;
  detailed_description?: string | null;
  learning_objectives?: string[] | null;
  target_audience?: string | null;
  difficulty: string;
  estimated_duration?: string | null;
  language: string;
  status: ContentStatus;
  version: number;
  author_id?: string | null;
  owner_id?: string | null;
  created_at: string;
  updated_at: string;
  curriculum?: Curriculum | null;
}

export interface CourseSearchItem {
  course_id: string;
  course_code: string;
  course_title: string;
  institution_id: string;
  course_content_id?: string | null;
  content_title?: string | null;
  short_description?: string | null;
  difficulty?: string | null;
  status?: string | null;
  modules_count?: number;
  lessons_count?: number;
}

export interface LessonProgress {
  id: string;
  student_profile_id: string;
  lesson_id: string;
  course_offering_id: string;
  content_version: number;
  status: ProgressStatus;
  completion_percentage: number;
  time_spent_seconds: number;
  started_at?: string | null;
  completed_at?: string | null;
  last_accessed_at: string;
}

export interface CourseProgress {
  id: string;
  student_profile_id: string;
  course_offering_id: string;
  course_content_id: string;
  content_version: number;
  completed_lessons: number;
  total_required_lessons: number;
  completed_modules: number;
  total_modules: number;
  percentage: number;
  is_completed: boolean;
  started_at?: string | null;
  completed_at?: string | null;
  last_activity_at: string;
}

export interface StudentBookmark {
  id: string;
  student_profile_id: string;
  target_type: "course" | "module" | "lesson" | "resource";
  target_id: string;
  title?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface StudentLearningNote {
  id: string;
  student_profile_id: string;
  target_type: "course" | "module" | "lesson" | "concept" | "resource";
  target_id: string;
  title?: string | null;
  content: string;
  is_private: boolean;
  created_at: string;
  updated_at: string;
}

export interface Concept {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  discipline_id?: string | null;
  difficulty: string;
  parent_concept_id?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface LearningResource {
  id: string;
  institution_id?: string | null;
  title: string;
  description?: string | null;
  resource_type: string;
  storage_key?: string | null;
  url?: string | null;
  provider?: string | null;
  duration_seconds?: number | null;
  file_metadata?: Record<string, unknown> | null;
  access_level: string;
  copyright_license?: string | null;
  status: string;
  current_version: number;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContentReview {
  id: string;
  course_content_id: string;
  version_id?: string | null;
  submitted_by: string;
  reviewed_by?: string | null;
  status: "submitted" | "approved" | "changes_requested" | "cancelled";
  review_notes?: string | null;
  submitted_at: string;
  reviewed_at?: string | null;
  comments: Array<{
    id: string;
    review_id: string;
    author_id: string;
    module_id?: string | null;
    lesson_id?: string | null;
    comment: string;
    created_at: string;
  }>;
}
