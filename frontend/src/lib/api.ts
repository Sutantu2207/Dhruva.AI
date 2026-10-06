import { SystemHealth, SystemArchitecture, User, AuthTokens } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// In-memory token storage (NEVER localStorage)
let memoryAccessToken: string | null = null;

export function setMemoryAccessToken(token: string | null): void {
  memoryAccessToken = token;
}

export function getMemoryAccessToken(): string | null {
  return memoryAccessToken;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Attach in-memory access token if available
  if (memoryAccessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${memoryAccessToken}`);
  }

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: "include", // Transmit HttpOnly cookies for session/refresh
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && typeof errJson.detail === "string") {
        errorDetail = errJson.detail;
      }
    } catch {
      // Non-json error
    }
    throw new ApiError(res.status, errorDetail);
  }

  return res.json();
}

/**
 * System and Health Probes
 */
export async function fetchSystemHealth(): Promise<SystemHealth> {
  return request<SystemHealth>("/health", { cache: "no-store" });
}

export async function fetchSystemArchitecture(): Promise<SystemArchitecture> {
  return request<SystemArchitecture>("/system/architecture", { cache: "no-store" });
}

/**
 * Authentication Endpoints
 */
export async function registerStudent(data: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  institution_id?: string;
}): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function loginUser(data: {
  email: string;
  password: string;
}): Promise<AuthTokens> {
  const tokens = await request<AuthTokens>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
  setMemoryAccessToken(tokens.access_token);
  return tokens;
}

export async function refreshSession(): Promise<AuthTokens> {
  const tokens = await request<AuthTokens>("/auth/refresh", {
    method: "POST",
  });
  setMemoryAccessToken(tokens.access_token);
  return tokens;
}

export async function logoutUser(): Promise<{ message: string }> {
  try {
    return await request<{ message: string }>("/auth/logout", {
      method: "POST",
    });
  } finally {
    setMemoryAccessToken(null);
  }
}

export async function fetchCurrentUser(): Promise<User> {
  return request<User>("/auth/me");
}

export async function changePassword(data: {
  current_password: string;
  new_password: string;
}): Promise<{ message: string }> {
  return request<{ message: string }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
  return request<{ message: string }>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(data: {
  token: string;
  new_password: string;
}): Promise<{ message: string }> {
  return request<{ message: string }>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function verifyEmail(token: string): Promise<{ message: string }> {
  return request<{ message: string }>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

// =========================================================================
// Academic Management APIs (Domain 2)
// =========================================================================

import type {
  Institution,
  Department,
  Program,
  CourseOffering,
  StudentAcademicProfile,
  TeacherAcademicProfile,
  StudentEnrollment,
} from "./types/academic";

export async function fetchInstitutions(): Promise<Institution[]> {
  return request<Institution[]>("/academic/institutions");
}

export async function fetchInstitution(id: string): Promise<Institution> {
  return request<Institution>(`/academic/institutions/${id}`);
}

export async function fetchDepartments(institutionId?: string): Promise<Department[]> {
  const query = institutionId ? `?institution_id=${encodeURIComponent(institutionId)}` : "";
  return request<Department[]>(`/academic/departments${query}`);
}

export async function fetchPrograms(departmentId?: string): Promise<Program[]> {
  const query = departmentId ? `?department_id=${encodeURIComponent(departmentId)}` : "";
  return request<Program[]>(`/academic/programs${query}`);
}

export async function fetchMyStudentProfile(): Promise<StudentAcademicProfile> {
  return request<StudentAcademicProfile>("/academic/student-profiles/me");
}

export async function fetchMyTeacherProfile(): Promise<TeacherAcademicProfile> {
  return request<TeacherAcademicProfile>("/academic/teacher-profiles/me");
}

export async function fetchMyEnrollments(): Promise<StudentEnrollment[]> {
  return request<StudentEnrollment[]>("/academic/enrollments");
}

export async function fetchCourseOfferings(courseId?: string): Promise<CourseOffering[]> {
  const query = courseId ? `?course_id=${encodeURIComponent(courseId)}` : "";
  return request<CourseOffering[]>(`/academic/course-offerings${query}`);
}

// =========================================================================
// National Academic Taxonomy & India-Wide Catalog APIs (Domain 2.5)
// =========================================================================

import type {
  AcademicCatalogSource,
  AcademicCatalogVersion,
  AcademicDiscipline,
  DegreeType,
  ProgramCatalog,
  CourseCatalog,
  SkillCatalog,
  CareerCatalog,
  InstitutionProgramMapping,
  InstitutionCourseMapping,
  CatalogSearchResult,
} from "./types/catalog";

export async function fetchCatalogDisciplines(skip = 0, limit = 50): Promise<AcademicDiscipline[]> {
  return request<AcademicDiscipline[]>(`/catalog/disciplines?skip=${skip}&limit=${limit}`);
}

export async function fetchCatalogDegreeTypes(skip = 0, limit = 50): Promise<DegreeType[]> {
  return request<DegreeType[]>(`/catalog/degree-types?skip=${skip}&limit=${limit}`);
}

export async function fetchCatalogPrograms(
  params?: { disciplineId?: string; degreeTypeId?: string; search?: string; skip?: number; limit?: number }
): Promise<ProgramCatalog[]> {
  const q = new URLSearchParams();
  if (params?.disciplineId) q.append("discipline_id", params.disciplineId);
  if (params?.degreeTypeId) q.append("degree_type_id", params.degreeTypeId);
  if (params?.search) q.append("search", params.search);
  q.append("skip", String(params?.skip || 0));
  q.append("limit", String(params?.limit || 50));
  return request<ProgramCatalog[]>(`/catalog/programs?${q.toString()}`);
}

export async function fetchCatalogCourses(
  params?: { disciplineId?: string; search?: string; skip?: number; limit?: number }
): Promise<CourseCatalog[]> {
  const q = new URLSearchParams();
  if (params?.disciplineId) q.append("discipline_id", params.disciplineId);
  if (params?.search) q.append("search", params.search);
  q.append("skip", String(params?.skip || 0));
  q.append("limit", String(params?.limit || 50));
  return request<CourseCatalog[]>(`/catalog/courses?${q.toString()}`);
}

export async function fetchCatalogSkills(
  params?: { category?: string; search?: string; skip?: number; limit?: number }
): Promise<SkillCatalog[]> {
  const q = new URLSearchParams();
  if (params?.category) q.append("category", params.category);
  if (params?.search) q.append("search", params.search);
  q.append("skip", String(params?.skip || 0));
  q.append("limit", String(params?.limit || 50));
  return request<SkillCatalog[]>(`/catalog/skills?${q.toString()}`);
}

export async function fetchCatalogCareers(
  params?: { industry?: string; search?: string; skip?: number; limit?: number }
): Promise<CareerCatalog[]> {
  const q = new URLSearchParams();
  if (params?.industry) q.append("industry", params.industry);
  if (params?.search) q.append("search", params.search);
  q.append("skip", String(params?.skip || 0));
  q.append("limit", String(params?.limit || 50));
  return request<CareerCatalog[]>(`/catalog/careers?${q.toString()}`);
}

export async function fetchCatalogVersions(): Promise<AcademicCatalogVersion[]> {
  return request<AcademicCatalogVersion[]>("/catalog/catalog-versions");
}

export async function fetchCatalogSources(): Promise<AcademicCatalogSource[]> {
  return request<AcademicCatalogSource[]>("/catalog/sources");
}

export async function searchCatalog(query: string): Promise<CatalogSearchResult> {
  return request<CatalogSearchResult>(`/catalog/search?q=${encodeURIComponent(query)}`);
}

export async function fetchInstitutionProgramMappings(institutionId?: string): Promise<InstitutionProgramMapping[]> {
  const query = institutionId ? `?institution_id=${encodeURIComponent(institutionId)}` : "";
  return request<InstitutionProgramMapping[]>(`/catalog/institution-program-mappings${query}`);
}

export async function fetchInstitutionCourseMappings(institutionId?: string): Promise<InstitutionCourseMapping[]> {
  const query = institutionId ? `?institution_id=${encodeURIComponent(institutionId)}` : "";
  return request<InstitutionCourseMapping[]>(`/catalog/institution-course-mappings${query}`);
}

// =========================================================================
// Student & Faculty Management, Mentorship & Profiles APIs (Domain 3)
// =========================================================================

import type {
  StudentProfileDetail,
  StudentSkill,
  StudentCareerGoal,
  StudentProject,
  StudentCertification,
  StudentAchievement,
  StudentPortfolio,
  StudentResume,
  MentorshipRelation,
  MentorNote,
  StudentDashboardOverview,
  FacultyDashboardOverview,
  AdminInstitutionOverview,
} from "./types/profile";

// --- Student Self Workspace ---

export async function fetchMyStudentProfileDetail(): Promise<StudentProfileDetail> {
  return request<StudentProfileDetail>("/students/me");
}

export async function updateMyStudentProfile(data: Partial<StudentProfileDetail>): Promise<StudentProfileDetail> {
  return request<StudentProfileDetail>("/students/me", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function fetchMyStudentOverview(): Promise<StudentDashboardOverview> {
  return request<StudentDashboardOverview>("/students/me/overview");
}

export async function fetchMySkills(): Promise<StudentSkill[]> {
  return request<StudentSkill[]>("/students/me/skills");
}

export async function addMySkill(data: { skill_catalog_id: string; proficiency?: string; source?: string }): Promise<StudentSkill> {
  return request<StudentSkill>("/students/me/skills", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteMySkill(skillId: string): Promise<void> {
  return request<void>(`/students/me/skills/${skillId}`, { method: "DELETE" });
}

export async function fetchMyProjects(): Promise<StudentProject[]> {
  return request<StudentProject[]>("/students/me/projects");
}

export async function createMyProject(data: Partial<StudentProject>): Promise<StudentProject> {
  return request<StudentProject>("/students/me/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchMyCertifications(): Promise<StudentCertification[]> {
  return request<StudentCertification[]>("/students/me/certifications");
}

export async function addMyCertification(data: Partial<StudentCertification>): Promise<StudentCertification> {
  return request<StudentCertification>("/students/me/certifications", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchMyAchievements(): Promise<StudentAchievement[]> {
  return request<StudentAchievement[]>("/students/me/achievements");
}

export async function addMyAchievement(data: Partial<StudentAchievement>): Promise<StudentAchievement> {
  return request<StudentAchievement>("/students/me/achievements", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchMyCareerGoals(): Promise<StudentCareerGoal[]> {
  return request<StudentCareerGoal[]>("/students/me/career-goals");
}

export async function addMyCareerGoal(data: Partial<StudentCareerGoal>): Promise<StudentCareerGoal> {
  return request<StudentCareerGoal>("/students/me/career-goals", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchStudentLegacyPortfolio(): Promise<StudentPortfolio> {
  return request<StudentPortfolio>("/students/me/portfolio");
}

export async function updateStudentLegacyPortfolio(data: Partial<StudentPortfolio>): Promise<StudentPortfolio> {
  return request<StudentPortfolio>("/students/me/portfolio", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function fetchMyResume(): Promise<StudentResume> {
  return request<StudentResume>("/students/me/resume");
}

export async function updateMyResume(data: Partial<StudentResume>): Promise<StudentResume> {
  return request<StudentResume>("/students/me/resume", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// --- Faculty & Mentorship ---

export async function fetchMyFacultyOverview(): Promise<FacultyDashboardOverview> {
  return request<FacultyDashboardOverview>("/faculty/me/overview");
}

export async function fetchMyAssignedOfferings(): Promise<Array<Record<string, unknown>>> {
  return request<Array<Record<string, unknown>>>("/faculty/me/offerings");
}

export async function fetchMyAssignedStudents(): Promise<Array<Record<string, unknown>>> {
  return request<Array<Record<string, unknown>>>("/faculty/me/students");
}

export async function fetchMyMentees(): Promise<MentorshipRelation[]> {
  return request<MentorshipRelation[]>("/mentorship/me");
}

export async function fetchStudentMentorNotes(studentProfileId: string): Promise<MentorNote[]> {
  return request<MentorNote[]>(`/mentorship/students/${studentProfileId}/notes`);
}

export async function addMentorNote(data: { student_profile_id: string; content: string; visibility?: string; follow_up_date?: string }): Promise<MentorNote> {
  return request<MentorNote>("/mentorship/notes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// --- Admin & Onboarding ---

export async function fetchAdminOverview(): Promise<AdminInstitutionOverview> {
  return request<AdminInstitutionOverview>("/imports/admin/overview");
}

export async function bulkImportStudents(data: { file_name: string; is_dry_run: boolean; records: Array<Record<string, unknown>> }): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/imports/students", {
    method: "POST",
    body: JSON.stringify({ import_type: "students", ...data }),
  });
}

export async function bulkImportFaculty(data: { file_name: string; is_dry_run: boolean; records: Array<Record<string, unknown>> }): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/imports/faculty", {
    method: "POST",
    body: JSON.stringify({ import_type: "faculty", ...data }),
  });
}

// =========================================================================
// Domain 4: Course Delivery, Curriculum Structure & Learning Content Engine
// =========================================================================

export async function fetchCoursesSearch(params?: {
  q?: string;
  difficulty?: string;
  status?: string;
  institution_id?: string;
  limit?: number;
  offset?: number;
}): Promise<import("./types").CourseSearchItem[]> {
  const query = new URLSearchParams();
  if (params?.q) query.set("q", params.q);
  if (params?.difficulty) query.set("difficulty", params.difficulty);
  if (params?.status) query.set("status", params.status);
  if (params?.institution_id) query.set("institution_id", params.institution_id);
  if (params?.limit) query.set("limit", params.limit.toString());
  if (params?.offset) query.set("offset", params.offset.toString());
  const queryString = query.toString() ? `?${query.toString()}` : "";
  return request<import("./types").CourseSearchItem[]>(`/courses${queryString}`);
}

export async function fetchCourseContent(id: string): Promise<import("./types").CourseContentDetail> {
  return request<import("./types").CourseContentDetail>(`/courses/${id}`);
}

export async function fetchCourseCurriculum(id: string): Promise<import("./types").Curriculum> {
  return request<import("./types").Curriculum>(`/courses/${id}/curriculum`);
}

export async function createCourseContent(courseId: string, data: {
  title: string;
  short_description?: string;
  detailed_description?: string;
  difficulty?: string;
  language?: string;
}): Promise<import("./types").CourseContentDetail> {
  return request<import("./types").CourseContentDetail>(`/courses/${courseId}/content`, {
    method: "POST",
    body: JSON.stringify({ course_id: courseId, ...data }),
  });
}

export async function updateCourseContent(contentId: string, data: Partial<import("./types").CourseContentDetail>): Promise<import("./types").CourseContentDetail> {
  return request<import("./types").CourseContentDetail>(`/courses/${contentId}/content`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function createCourseModule(courseId: string, data: {
  curriculum_id: string;
  title: string;
  slug: string;
  description?: string;
  order_index?: number;
}): Promise<import("./types").Module> {
  return request<import("./types").Module>(`/courses/${courseId}/modules`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function reorderCurriculumModules(curriculumId: string, moduleIds: string[]): Promise<import("./types").Module[]> {
  return request<import("./types").Module[]>(`/modules/reorder?curriculum_id=${curriculumId}`, {
    method: "POST",
    body: JSON.stringify({ module_ids: moduleIds }),
  });
}

export async function createModuleLesson(moduleId: string, data: {
  title: string;
  slug: string;
  description?: string;
  lesson_type?: string;
  order_index?: number;
  is_required?: boolean;
}): Promise<import("./types").Lesson> {
  return request<import("./types").Lesson>(`/modules/${moduleId}/lessons`, {
    method: "POST",
    body: JSON.stringify({ module_id: moduleId, ...data }),
  });
}

export async function reorderModuleLessons(moduleId: string, lessonIds: string[]): Promise<import("./types").Lesson[]> {
  return request<import("./types").Lesson[]>(`/lessons/reorder?module_id=${moduleId}`, {
    method: "POST",
    body: JSON.stringify({ lesson_ids: lessonIds }),
  });
}

export async function addLessonContentBlock(lessonId: string, data: {
  block_type: string;
  content: string;
  media_url?: string;
  order_index?: number;
}): Promise<import("./types").ContentBlock> {
  return request<import("./types").ContentBlock>(`/lessons/${lessonId}/blocks`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Student Learning & Deterministic Progress
export async function startLessonProgress(lessonId: string, courseOfferingId: string): Promise<import("./types").LessonProgress> {
  return request<import("./types").LessonProgress>(`/learning/lessons/${lessonId}/start`, {
    method: "POST",
    body: JSON.stringify({ course_offering_id: courseOfferingId }),
  });
}

export async function updateLessonProgress(
  lessonId: string,
  courseOfferingId: string,
  timeSpentSeconds: number,
  completionPercentage: number
): Promise<import("./types").LessonProgress> {
  return request<import("./types").LessonProgress>(`/learning/lessons/${lessonId}/progress`, {
    method: "POST",
    body: JSON.stringify({
      course_offering_id: courseOfferingId,
      time_spent_seconds: timeSpentSeconds,
      completion_percentage: completionPercentage,
    }),
  });
}

export async function completeLessonProgress(
  lessonId: string,
  courseOfferingId: string,
  timeSpentSeconds: number = 0
): Promise<import("./types").LessonProgress> {
  return request<import("./types").LessonProgress>(`/learning/lessons/${lessonId}/complete`, {
    method: "POST",
    body: JSON.stringify({
      course_offering_id: courseOfferingId,
      time_spent_seconds: timeSpentSeconds,
    }),
  });
}

export async function fetchCourseOfferingProgress(courseOfferingId: string): Promise<import("./types").CourseProgress> {
  return request<import("./types").CourseProgress>(`/learning/courses/${courseOfferingId}/progress`);
}

// Student Bookmarks
export async function fetchStudentBookmarks(): Promise<import("./types").StudentBookmark[]> {
  return request<import("./types").StudentBookmark[]>("/bookmarks");
}

export async function createStudentBookmark(data: {
  target_type: string;
  target_id: string;
  title?: string;
  notes?: string;
}): Promise<import("./types").StudentBookmark> {
  return request<import("./types").StudentBookmark>("/bookmarks", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteStudentBookmark(id: string): Promise<void> {
  return request<void>(`/bookmarks/${id}`, { method: "DELETE" });
}

// Student Notes
export async function fetchStudentNotes(targetType?: string, targetId?: string): Promise<import("./types").StudentLearningNote[]> {
  const query = new URLSearchParams();
  if (targetType) query.set("target_type", targetType);
  if (targetId) query.set("target_id", targetId);
  const qs = query.toString() ? `?${query.toString()}` : "";
  return request<import("./types").StudentLearningNote[]>(`/notes${qs}`);
}

export async function createStudentNote(data: {
  target_type: string;
  target_id: string;
  title?: string;
  content: string;
  is_private?: boolean;
}): Promise<import("./types").StudentLearningNote> {
  return request<import("./types").StudentLearningNote>("/notes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteStudentNote(id: string): Promise<void> {
  return request<void>(`/notes/${id}`, { method: "DELETE" });
}

// Content Review Workflow
export async function submitContentForReview(contentId: string, reviewNotes?: string): Promise<import("./types").ContentReview> {
  return request<import("./types").ContentReview>(`/content-review/${contentId}/submit`, {
    method: "POST",
    body: JSON.stringify({ review_notes: reviewNotes }),
  });
}

export async function approveContentReview(reviewId: string, reviewNotes?: string): Promise<import("./types").ContentReview> {
  return request<import("./types").ContentReview>(`/content-review/${reviewId}/approve`, {
    method: "POST",
    body: JSON.stringify({ review_notes: reviewNotes }),
  });
}

export async function requestChangesContentReview(reviewId: string, reviewNotes: string): Promise<import("./types").ContentReview> {
  return request<import("./types").ContentReview>(`/content-review/${reviewId}/request-changes`, {
    method: "POST",
    body: JSON.stringify({ review_notes: reviewNotes }),
  });
}

export async function fetchConcepts(q?: string): Promise<import("./types").Concept[]> {
  const qs = q ? `?q=${encodeURIComponent(q)}` : "";
  return request<import("./types").Concept[]>(`/concepts${qs}`);
}

// Domain 5: Question Banks & Questions
export async function fetchQuestionBanks(): Promise<import("./types").QuestionBank[]> {
  return request<import("./types").QuestionBank[]>("/question-banks");
}

export async function createQuestionBank(data: {
  title: string;
  description?: string;
  department_id?: string;
  course_id?: string;
  visibility?: string;
}): Promise<import("./types").QuestionBank> {
  return request<import("./types").QuestionBank>("/question-banks", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchQuestions(bankId: string, params?: {
  q?: string;
  question_type?: string;
  difficulty?: string;
  status?: string;
}): Promise<import("./types").Question[]> {
  const query = new URLSearchParams();
  if (params?.q) query.set("q", params.q);
  if (params?.question_type) query.set("question_type", params.question_type);
  if (params?.difficulty) query.set("difficulty", params.difficulty);
  if (params?.status) query.set("status", params.status);
  const qs = query.toString() ? `?${query.toString()}` : "";
  return request<import("./types").Question[]>(`/question-banks/${bankId}/questions${qs}`);
}

export async function createQuestion(bankId: string, data: {
  title: string;
  question_type: string;
  prompt: string;
  instructions?: string;
  difficulty?: string;
  points?: number;
  negative_marks?: number;
  estimated_time_minutes?: number;
  explanation?: string;
  options?: Array<{
    option_text: string;
    option_order: number;
    is_correct?: boolean;
    explanation?: string;
  }>;
  concept_ids?: string[];
  skill_ids?: string[];
}): Promise<import("./types").Question> {
  return request<import("./types").Question>(`/question-banks/${bankId}/questions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Domain 5: Assessments
export async function fetchAssessments(courseOfferingId?: string): Promise<import("./types").Assessment[]> {
  const qs = courseOfferingId ? `?course_offering_id=${courseOfferingId}` : "";
  return request<import("./types").Assessment[]>(`/assessments${qs}`);
}

export async function createAssessment(data: {
  course_offering_id: string;
  title: string;
  description?: string;
  instructions?: string;
  assessment_type: string;
  duration_minutes: number;
  total_marks: number;
  passing_marks: number;
  attempts_allowed?: number;
  feedback_policy?: string;
}): Promise<import("./types").Assessment> {
  return request<import("./types").Assessment>("/assessments", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function publishAssessment(assessmentId: string, data: {
  question_version_ids: string[];
  duration_minutes?: number;
  total_marks?: number;
  passing_marks?: number;
}): Promise<import("./types").AssessmentVersion> {
  return request<import("./types").AssessmentVersion>(`/assessments/${assessmentId}/publish`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Domain 5: Attempts & Delivery
export async function startAssessmentAttempt(assessmentId: string): Promise<import("./types").AssessmentAttempt> {
  return request<import("./types").AssessmentAttempt>(`/assessments/${assessmentId}/attempts`, {
    method: "POST",
  });
}

export async function fetchAttemptDelivery(attemptId: string): Promise<import("./types").AttemptDelivery> {
  return request<import("./types").AttemptDelivery>(`/attempts/${attemptId}/delivery`);
}

export async function autosaveResponse(
  attemptId: string,
  questionVersionId: string,
  responsePayload: Record<string, unknown>
): Promise<import("./types").AssessmentResponse> {
  return request<import("./types").AssessmentResponse>(`/attempts/${attemptId}/responses`, {
    method: "POST",
    body: JSON.stringify({
      question_version_id: questionVersionId,
      response_payload: responsePayload,
    }),
  });
}

export async function submitAssessmentAttempt(attemptId: string): Promise<import("./types").AssessmentResult> {
  return request<import("./types").AssessmentResult>(`/attempts/${attemptId}/submit`, {
    method: "POST",
  });
}

export async function fetchAttemptResult(attemptId: string): Promise<import("./types").AssessmentResult> {
  return request<import("./types").AssessmentResult>(`/attempts/${attemptId}/result`);
}

export async function fetchMyAssessmentResults(): Promise<import("./types").AssessmentResult[]> {
  return request<import("./types").AssessmentResult[]>("/students/me/assessment-results");
}

export async function fetchMyConceptEvidence(): Promise<import("./types").ConceptEvidence[]> {
  return request<import("./types").ConceptEvidence[]>("/students/me/evidence/concepts");
}

export async function fetchMySkillEvidence(): Promise<import("./types").SkillEvidence[]> {
  return request<import("./types").SkillEvidence[]>("/students/me/evidence/skills");
}

// =========================================================================
// Domain 6: Knowledge State, Concept Mastery & Spaced Repetition (SM-2)
// =========================================================================

export async function fetchMyKnowledgeSummary(): Promise<import("./types").StudentKnowledgeSummary> {
  return request<import("./types").StudentKnowledgeSummary>("/knowledge/me");
}

export async function fetchMyConceptStates(params?: {
  state?: string;
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<import("./types").ConceptKnowledgeState[]> {
  const query = new URLSearchParams();
  if (params?.state) query.set("state", params.state);
  if (params?.q) query.set("q", params.q);
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  const qs = query.toString();
  return request<import("./types").ConceptKnowledgeState[]>(`/knowledge/me/concepts${qs ? `?${qs}` : ""}`);
}

export async function fetchMyConceptDetail(conceptId: string): Promise<import("./types").ConceptDetail> {
  return request<import("./types").ConceptDetail>(`/knowledge/me/concepts/${conceptId}`);
}

export async function fetchMyWeakConcepts(): Promise<import("./types").ConceptKnowledgeState[]> {
  return request<import("./types").ConceptKnowledgeState[]>("/knowledge/me/weak-concepts");
}

export async function fetchMyAtRiskConcepts(): Promise<import("./types").ConceptKnowledgeState[]> {
  return request<import("./types").ConceptKnowledgeState[]>("/knowledge/me/at-risk");
}

export async function triggerKnowledgeRebuild(): Promise<{
  status: string;
  student_profile_id: string;
  rebuilt_concept_states: number;
  timestamp: string;
}> {
  return request("/knowledge/rebuild", { method: "POST" });
}

export async function fetchDueReviews(): Promise<import("./types").ConceptReviewState[]> {
  return request<import("./types").ConceptReviewState[]>("/reviews/me/due");
}

export async function fetchUpcomingReviews(limit: number = 20): Promise<import("./types").ConceptReviewState[]> {
  return request<import("./types").ConceptReviewState[]>(`/reviews/me/upcoming?limit=${limit}`);
}

export async function completeConceptReview(
  conceptId: string,
  payload: import("./types").ConceptReviewCompletionPayload
): Promise<import("./types").ConceptReviewState> {
  return request<import("./types").ConceptReviewState>(`/reviews/${conceptId}/complete`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchMyLearningPriorities(limit: number = 20): Promise<import("./types").LearningPriority[]> {
  return request<import("./types").LearningPriority[]>(`/learning-priority/me?limit=${limit}`);
}

export async function fetchMyDailyMission(): Promise<import("./types").DailyMission> {
  return request<import("./types").DailyMission>("/learning-priority/me/daily");
}

export async function fetchStudentKnowledgeById(studentId: string): Promise<import("./types").StudentKnowledgeSummary> {
  return request<import("./types").StudentKnowledgeSummary>(`/students/${studentId}/knowledge`);
}

// ==========================================
// DOMAIN 7: CAREER INTELLIGENCE & SKILLS API
// ==========================================

export async function fetchMyCareerIntelligence(): Promise<import("./types").CareerIntelligenceOverview> {
  return request<import("./types").CareerIntelligenceOverview>("/career/intelligence");
}

export async function fetchMyCareerReadiness(): Promise<import("./types").StudentCareerReadiness> {
  return request<import("./types").StudentCareerReadiness>("/career/readiness");
}

export async function fetchMyCareerGaps(): Promise<import("./types").SkillGap[]> {
  return request<import("./types").SkillGap[]>("/career/gaps");
}

export async function fetchMyCareerTrajectory(): Promise<import("./types").CareerTrajectory> {
  return request<import("./types").CareerTrajectory>("/career/trajectory");
}

export async function compareCareers(careerIds: string[]): Promise<import("./types").CareerComparisonItem[]> {
  return request<import("./types").CareerComparisonItem[]>(`/career/compare?career_ids=${careerIds.join(",")}`);
}

export async function fetchMyPlacementReadiness(): Promise<import("./types").PlacementReadiness> {
  return request<import("./types").PlacementReadiness>("/career/placement-readiness");
}

export async function fetchMySkillIntelligence(): Promise<import("./types").StudentSkillIntelligence[]> {
  return request<import("./types").StudentSkillIntelligence[]>("/skills");
}

export async function fetchSkillDetail(skillId: string): Promise<import("./types").StudentSkillIntelligence> {
  return request<import("./types").StudentSkillIntelligence>(`/skills/${skillId}`);
}

export async function fetchStudentSkillIntelligence(
  studentProfileId: string
): Promise<import("./types").StudentSkillIntelligence[]> {
  return request<import("./types").StudentSkillIntelligence[]>(`/students/${studentProfileId}/skills`);
}

export async function fetchStudentCareerReadiness(
  studentProfileId: string,
  careerId: string
): Promise<import("./types").StudentCareerReadiness> {
  return request<import("./types").StudentCareerReadiness>(`/students/${studentProfileId}/career/${careerId}/readiness`);
}

export async function triggerRecomputeSkills(): Promise<{ status: string; evaluated_skills_count: number }> {
  return request<{ status: string; evaluated_skills_count: number }>("/career/recompute/skills", {
    method: "POST",
  });
}

export async function triggerRecomputeCareer(careerId: string): Promise<import("./types").StudentCareerReadiness> {
  return request<import("./types").StudentCareerReadiness>(`/career/recompute/career/${careerId}`, {
    method: "POST",
  });
}

// ==========================================
// DOMAIN 8: PROJECT INTELLIGENCE, EVIDENCE & PORTFOLIO API
// ==========================================

export async function fetchProjects(params?: {
  project_type?: string;
  status?: string;
  is_verified?: boolean;
  student_profile_id?: string;
}): Promise<import("./types").StudentProjectSummary[]> {
  const query = new URLSearchParams();
  if (params?.project_type) query.append("project_type", params.project_type);
  if (params?.status) query.append("status", params.status);
  if (params?.is_verified !== undefined) query.append("is_verified", String(params.is_verified));
  if (params?.student_profile_id) query.append("student_profile_id", params.student_profile_id);

  const qs = query.toString();
  return request<import("./types").StudentProjectSummary[]>(`/projects${qs ? `?${qs}` : ""}`);
}

export async function fetchProjectDetail(projectId: string): Promise<import("./types").StudentProjectDetail> {
  return request<import("./types").StudentProjectDetail>(`/projects/${projectId}`);
}

export async function createProject(
  payload: import("./types").CreateProjectPayload
): Promise<import("./types").StudentProjectSummary> {
  return request<import("./types").StudentProjectSummary>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateProject(
  projectId: string,
  payload: import("./types").UpdateProjectPayload
): Promise<import("./types").StudentProjectSummary> {
  return request<import("./types").StudentProjectSummary>(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  return request<void>(`/projects/${projectId}`, {
    method: "DELETE",
  });
}

export async function fetchProjectEvidence(
  projectId: string
): Promise<import("./types").ProjectEvidenceItem[]> {
  return request<import("./types").ProjectEvidenceItem[]>(`/projects/${projectId}/evidence`);
}

export async function submitProjectEvidence(
  projectId: string,
  payload: import("./types").SubmitEvidencePayload
): Promise<import("./types").ProjectEvidenceItem> {
  return request<import("./types").ProjectEvidenceItem>(`/projects/${projectId}/evidence`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function verifyProjectEvidence(
  projectId: string,
  evidenceId: string,
  decision: "verified" | "rejected",
  verificationNotes?: string
): Promise<import("./types").ProjectEvidenceItem> {
  return request<import("./types").ProjectEvidenceItem>(
    `/projects/${projectId}/evidence/${evidenceId}/verify`,
    {
      method: "POST",
      body: JSON.stringify({ decision, verification_notes: verificationNotes }),
    }
  );
}

export async function fetchProjectReviews(
  projectId: string
): Promise<import("./types").ProjectReviewItem[]> {
  return request<import("./types").ProjectReviewItem[]>(`/projects/${projectId}/reviews`);
}

export async function submitProjectReview(
  projectId: string,
  payload: import("./types").SubmitReviewPayload
): Promise<import("./types").ProjectReviewItem> {
  return request<import("./types").ProjectReviewItem>(`/projects/${projectId}/reviews`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchProjectQuality(
  projectId: string
): Promise<import("./types").ProjectQualityScore> {
  return request<import("./types").ProjectQualityScore>(`/projects/${projectId}/quality`);
}

export async function fetchProjectCareerRelevance(
  projectId: string
): Promise<import("./types").CareerRelevanceItem | null> {
  return request<import("./types").CareerRelevanceItem | null>(`/projects/${projectId}/career-relevance`);
}

export async function fetchMyPortfolio(): Promise<import("./types").StudentPortfolioConfig> {
  return request<import("./types").StudentPortfolioConfig>("/portfolio");
}

export async function updateMyPortfolio(
  payload: Partial<import("./types").StudentPortfolioConfig>
): Promise<import("./types").StudentPortfolioConfig> {
  return request<import("./types").StudentPortfolioConfig>("/portfolio", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function fetchMyPortfolioHealth(): Promise<import("./types").PortfolioHealthData> {
  return request<import("./types").PortfolioHealthData>("/portfolio/health");
}

export async function fetchPublicPortfolio(
  slugOrUsername: string
): Promise<import("./types").PublicPortfolioData> {
  return request<import("./types").PublicPortfolioData>(`/portfolio/public/${slugOrUsername}`);
}

export async function fetchSkillEvidenceGraph(
  skillId: string,
  studentProfileId?: string
): Promise<import("./types").SkillEvidenceGraphData> {
  const qs = studentProfileId ? `?student_profile_id=${studentProfileId}` : "";
  return request<import("./types").SkillEvidenceGraphData>(`/skills/${skillId}/graph${qs}`);
}

export async function fetchMySkillGraph(): Promise<import("./types").StudentSkillGraphData> {
  return request<import("./types").StudentSkillGraphData>("/students/me/skill-graph");
}

export async function fetchProjectsStrengtheningGaps(careerId?: string): Promise<import("./types").ProjectGapStrengtheningItem[]> {
  const qs = careerId ? `?career_id=${careerId}` : "";
  return request<import("./types").ProjectGapStrengtheningItem[]>(`/students/me/projects/gap-strengthening${qs}`);
}

export async function fetchProjectsWithInsufficientEvidence(): Promise<import("./types").ProjectInsufficientEvidenceItem[]> {
  return request<import("./types").ProjectInsufficientEvidenceItem[]>("/students/me/projects/insufficient-evidence");
}

// =========================================================================
// Domain 9: Institutional Analytics, Faculty Grading Workflows & Departmental Intelligence
// =========================================================================

export async function fetchFacultyDashboardAnalytics(): Promise<import("./types").FacultyDashboardAnalytics> {
  return request<import("./types").FacultyDashboardAnalytics>("/faculty/dashboard-analytics");
}

export async function fetchCourseOfferingAnalytics(
  offeringId: string
): Promise<import("./types").CourseOfferingAnalytics> {
  return request<import("./types").CourseOfferingAnalytics>(`/faculty/courses/${offeringId}/analytics`);
}

export function getCourseOfferingExportCsvUrl(offeringId: string): string {
  return `${API_BASE_URL}/faculty/courses/${offeringId}/export`;
}

export async function fetchGradingQueue(params?: {
  courseOfferingId?: string;
  itemType?: import("./types").GradingQueueType;
  priority?: import("./types").GradingQueuePriority;
}): Promise<import("./types").GradingQueueItem[]> {
  const query = new URLSearchParams();
  if (params?.courseOfferingId) query.set("course_offering_id", params.courseOfferingId);
  if (params?.itemType) query.set("item_type", params.itemType);
  if (params?.priority) query.set("priority", params.priority);
  const qs = query.toString() ? `?${query.toString()}` : "";
  return request<import("./types").GradingQueueItem[]>(`/faculty/grading${qs}`);
}

export async function submitManualQuestionGrade(
  manualEvalId: string,
  payload: import("./types").GradeManualQuestionPayload
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/faculty/grading/questions/${manualEvalId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function regradeManualQuestion(
  manualEvalId: string,
  payload: import("./types").RegradeEvaluationPayload
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/faculty/grading/questions/${manualEvalId}/regrade`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchDepartmentAnalytics(
  departmentId: string
): Promise<import("./types").DepartmentAnalytics> {
  return request<import("./types").DepartmentAnalytics>(`/hod/departments/${departmentId}/analytics`);
}

export async function fetchDepartmentComparisons(): Promise<import("./types").DepartmentComparisonResponse> {
  return request<import("./types").DepartmentComparisonResponse>("/admin/departments/compare");
}

export async function fetchPlacementAnalytics(): Promise<import("./types").PlacementAnalytics> {
  return request<import("./types").PlacementAnalytics>("/placement/analytics");
}

export async function scanInterventionSignals(offeringId?: string): Promise<{ signals_generated_count: number }> {
  const qs = offeringId ? `?course_offering_id=${offeringId}` : "";
  return request<{ signals_generated_count: number }>(`/interventions/signals/scan${qs}`, {
    method: "POST",
  });
}

export async function acknowledgeInterventionSignal(
  signalId: string,
  payload?: import("./types").AcknowledgeSignalPayload
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/interventions/signals/${signalId}/acknowledge`, {
    method: "POST",
    body: JSON.stringify(payload || {}),
  });
}

export async function dismissInterventionSignal(
  signalId: string,
  payload: import("./types").DismissSignalPayload
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/interventions/signals/${signalId}/dismiss`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function convertSignalToIntervention(
  signalId: string,
  payload: import("./types").ConvertSignalToInterventionPayload
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/interventions/signals/${signalId}/convert`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Domain 10: Autonomous Adaptive Remediation & Accreditation Endpoints
 */

export async function fetchMyRemediationPlans(): Promise<import("./types").RemediationPlan[]> {
  return request<import("./types").RemediationPlan[]>("/remediation/me");
}

export async function fetchRemediationPlan(planId: string): Promise<import("./types").RemediationPlan> {
  return request<import("./types").RemediationPlan>(`/remediation/plans/${planId}`);
}

export async function startRemediationPlan(planId: string): Promise<import("./types").RemediationPlan> {
  return request<import("./types").RemediationPlan>(`/remediation/plans/${planId}/start`, {
    method: "POST",
  });
}

export async function completeRemediationStep(
  planId: string,
  stepId: string,
  data: {
    score?: number;
    completion_percentage?: number;
    evidence_generated?: Record<string, unknown>;
  }
): Promise<import("./types").RemediationPlanStep> {
  return request<import("./types").RemediationPlanStep>(`/remediation/plans/${planId}/steps/${stepId}/complete`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function generateRemediationPlanFromSignal(signalId: string): Promise<import("./types").RemediationPlan> {
  return request<import("./types").RemediationPlan>("/remediation/generate", {
    method: "POST",
    body: JSON.stringify({ signal_id: signalId }),
  });
}

export async function fetchFacultyRemediationPlans(): Promise<import("./types").RemediationPlan[]> {
  return request<import("./types").RemediationPlan[]>("/remediation/faculty/plans");
}

export async function facultyOverrideRemediationPlan(
  planId: string,
  action: "approve" | "pause" | "resume" | "close" | "modify",
  reason: string
): Promise<import("./types").RemediationPlan> {
  return request<import("./types").RemediationPlan>(`/remediation/plans/${planId}/override?action=${action}`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function fetchInstitutionalRemediationAnalytics(): Promise<import("./types").InstitutionalRemediationAnalytics> {
  return request<import("./types").InstitutionalRemediationAnalytics>("/remediation/analytics/institutional");
}

export async function fetchContentGaps(): Promise<import("./types").ContentGap[]> {
  return request<import("./types").ContentGap[]>("/remediation/content-gaps");
}

export async function generateAccreditationEvidence(
  framework: string,
  criterion: string
): Promise<import("./types").AccreditationEvidence> {
  return request<import("./types").AccreditationEvidence>("/remediation/accreditation/evidence/generate", {
    method: "POST",
    body: JSON.stringify({ framework, criterion }),
  });
}

/**
 * Domain 11: AI Orchestration & Natural Language Layer Endpoints
 */

export async function fetchAIConversations(scope?: string): Promise<import("./types").AIConversation[]> {
  const qs = scope ? `?scope=${scope}` : "";
  return request<import("./types").AIConversation[]>(`/ai/conversations${qs}`);
}

export async function createAIConversation(
  payload: import("./types").AIConversationCreate
): Promise<import("./types").AIConversation> {
  return request<import("./types").AIConversation>("/ai/conversations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchAIConversation(conversationId: string): Promise<import("./types").AIConversation> {
  return request<import("./types").AIConversation>(`/ai/conversations/${conversationId}`);
}

export async function deleteAIConversation(conversationId: string): Promise<void> {
  return request<void>(`/ai/conversations/${conversationId}`, {
    method: "DELETE",
  });
}

export async function sendAIMessage(
  conversationId: string,
  payload: import("./types").AIMessageCreate
): Promise<import("./types").AIMessage> {
  return request<import("./types").AIMessage>(`/ai/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function submitAIFeedback(
  payload: import("./types").AIFeedbackCreate
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/ai/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchAITrustManifest(): Promise<import("./types").AITrustManifest> {
  return request<import("./types").AITrustManifest>("/ai/trust");
}

export async function fetchAIUsageMetrics(): Promise<import("./types").AIUsageMetrics> {
  return request<import("./types").AIUsageMetrics>("/ai/usage");
}

/**
 * Domain 12: Production Readiness, Operations & Notifications Endpoints
 */

export async function fetchSystemHealthStatus(): Promise<import("./types").SystemHealthStatus> {
  return request<import("./types").SystemHealthStatus>("/health/ready");
}

export async function fetchAdminOperationsOverview(): Promise<import("./types").AdminOperationsOverview> {
  return request<import("./types").AdminOperationsOverview>("/admin/operations/overview");
}

export async function fetchWorkerJobs(limit: number = 20): Promise<import("./types").BackgroundJobRecord[]> {
  return request<import("./types").BackgroundJobRecord[]>(`/admin/operations/jobs?limit=${limit}`);
}

export async function fetchNotifications(unreadOnly: boolean = false): Promise<import("./types").NotificationItem[]> {
  const qs = unreadOnly ? "?unread_only=true" : "";
  return request<import("./types").NotificationItem[]>(`/notifications${qs}`);
}

export async function markNotificationRead(id: string): Promise<import("./types").NotificationItem> {
  return request<import("./types").NotificationItem>(`/notifications/${id}/read`, {
    method: "POST",
  });
}

export async function markAllNotificationsRead(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/notifications/read-all", {
    method: "POST",
  });
}

export async function fetchNotificationPreferences(): Promise<import("./types").NotificationPreferences> {
  return request<import("./types").NotificationPreferences>("/notifications/preferences");
}

export async function updateNotificationPreferences(
  payload: Partial<import("./types").NotificationPreferences>
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/notifications/preferences", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}


