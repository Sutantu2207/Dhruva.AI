/**
 * Domain 3: Student & Faculty Management, Mentorship & Academic Profiles Type Definitions.
 */

export interface StudentProfileDetail {
  id: string;
  student_profile_id: string;
  headline?: string | null;
  bio?: string | null;
  learning_preferences?: Record<string, unknown> | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  website_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentSkill {
  id: string;
  student_profile_id: string;
  skill_catalog_id: string;
  skill_name: string;
  skill_code: string;
  proficiency: "beginner" | "developing" | "intermediate" | "advanced" | "expert";
  source: "self_declared" | "assessment_verified" | "course_verified" | "project_verified" | "faculty_verified";
  is_verified: boolean;
  verified_by_user_id?: string | null;
  last_assessed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentInterest {
  id: string;
  student_profile_id: string;
  interest_title: string;
  discipline_id?: string | null;
  career_catalog_id?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface StudentCareerGoal {
  id: string;
  student_profile_id: string;
  career_catalog_id: string;
  career_title: string;
  career_code: string;
  priority: number;
  short_term_goals?: string | null;
  long_term_goals?: string | null;
  target_industry?: string | null;
  preferred_locations?: string[] | null;
  target_organizations?: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface StudentProject {
  id: string;
  student_profile_id: string;
  title: string;
  description?: string | null;
  project_type: string;
  status: string;
  start_date?: string | null;
  end_date?: string | null;
  repository_url?: string | null;
  demo_url?: string | null;
  documentation_url?: string | null;
  technologies?: string[] | null;
  team_or_individual: string;
  role?: string | null;
  outcomes?: string | null;
  is_verified: boolean;
  verified_by_user_id?: string | null;
  skill_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface StudentCertification {
  id: string;
  student_profile_id: string;
  title: string;
  issuer: string;
  credential_id?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  credential_url?: string | null;
  document_reference?: string | null;
  status: "unverified" | "pending" | "verified" | "rejected";
  verified_by_user_id?: string | null;
  verification_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentAchievement {
  id: string;
  student_profile_id: string;
  title: string;
  description?: string | null;
  category: string;
  achievement_date?: string | null;
  issuer_event?: string | null;
  evidence_url?: string | null;
  is_verified: boolean;
  verified_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentPortfolio {
  id: string;
  student_profile_id: string;
  headline?: string | null;
  bio?: string | null;
  featured_project_ids?: string[] | null;
  featured_skill_ids?: string[] | null;
  public_visibility: boolean;
  custom_links?: Array<{ title: string; url: string }> | null;
  created_at: string;
  updated_at: string;
}

export interface StudentResume {
  id: string;
  student_profile_id: string;
  summary?: string | null;
  selected_project_ids?: string[] | null;
  selected_skill_ids?: string[] | null;
  selected_certification_ids?: string[] | null;
  selected_achievement_ids?: string[] | null;
  experience_entries?: Array<Record<string, unknown>> | null;
  custom_sections?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface TeacherProfileDetail {
  id: string;
  teacher_profile_id: string;
  biography?: string | null;
  experience_years?: number | null;
  qualifications?: string[] | null;
  expertise_areas?: string[] | null;
  office_location?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MentorshipRelation {
  id: string;
  institution_id: string;
  mentor_user_id: string;
  student_profile_id: string;
  start_date: string;
  end_date?: string | null;
  status: string;
  assignment_source: string;
  created_at: string;
  updated_at: string;
  student_name?: string | null;
  student_enrollment_number?: string | null;
  mentor_name?: string | null;
}

export interface MentorNote {
  id: string;
  institution_id: string;
  mentor_user_id: string;
  student_profile_id: string;
  content: string;
  visibility: "private_mentor" | "shared_faculty" | "institutional_admin";
  follow_up_date?: string | null;
  status: "open" | "resolved" | "archived";
  created_at: string;
  updated_at: string;
}

export interface StudentIntervention {
  id: string;
  institution_id: string;
  student_profile_id: string;
  created_by_user_id: string;
  category: string;
  priority: string;
  status: string;
  reason: string;
  action_plan?: string | null;
  follow_up_date?: string | null;
  resolution_notes?: string | null;
  resolved_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StudentDashboardOverview {
  user_id: string;
  student_profile_id: string;
  enrollment_number: string;
  academic_status: string;
  institution_name: string;
  program_name: string;
  batch_name: string;
  section_name?: string | null;
  completion_percentage: number;
  completed_sections: string[];
  missing_sections: string[];
  active_courses_count: number;
  total_skills_count: number;
  verified_skills_count: number;
  projects_count: number;
  certifications_count: number;
  achievements_count: number;
  mentor_name?: string | null;
  active_interventions_count: number;
}

export interface FacultyDashboardOverview {
  user_id: string;
  teacher_profile_id: string;
  employee_id: string;
  designation: string;
  department_name: string;
  institution_name: string;
  assigned_offerings_count: number;
  total_enrolled_students: number;
  assigned_mentees_count: number;
  pending_follow_ups_count: number;
  profile_status: string;
}

export interface AdminInstitutionOverview {
  institution_id: string;
  institution_name: string;
  total_students: number;
  total_faculty: number;
  active_programs: number;
  active_batches: number;
  total_sections: number;
  total_courses: number;
  status_distribution: Record<string, number>;
  pending_onboarding_jobs: number;
}
