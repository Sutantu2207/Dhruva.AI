/**
 * Academic Management and Institutional Hierarchy TypeScript Type Definitions.
 * Aligns with backend SQLAlchemy models and API response schemas.
 */

export interface Institution {
  id: string;
  name: string;
  code: string;
  email_domains?: string | null;
  status: string;
  created_at: string;
}

export interface Department {
  id: string;
  institution_id: string;
  name: string;
  code: string;
  status: string;
  created_at: string;
}

export interface Program {
  id: string;
  department_id: string;
  name: string;
  code: string;
  degree_type: string;
  duration_years: number;
  status: string;
  created_at: string;
}

export interface AcademicYear {
  id: string;
  institution_id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
}

export interface Semester {
  id: string;
  academic_year_id: string;
  semester_number: number;
  label: string;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
}

export interface Batch {
  id: string;
  institution_id: string;
  program_id: string;
  admission_year: number;
  graduation_year: number;
  label: string;
  status: string;
  created_at: string;
}

export interface Section {
  id: string;
  batch_id: string;
  name: string;
  capacity: number;
  status: string;
  created_at: string;
}

export interface Course {
  id: string;
  institution_id: string;
  department_id: string;
  code: string;
  title: string;
  description?: string | null;
  credits: number;
  course_type: string;
  status: string;
  created_at: string;
}

export interface CourseOffering {
  id: string;
  course_id: string;
  academic_year_id: string;
  semester_id: string;
  section_id: string;
  status: string;
  start_date?: string | null;
  end_date?: string | null;
  created_at: string;
}

export interface StudentAcademicProfile {
  id: string;
  user_id: string;
  institution_id: string;
  program_id: string;
  batch_id: string;
  current_section_id?: string | null;
  enrollment_number: string;
  admission_year: number;
  graduation_year: number;
  academic_status: string;
  created_at: string;
}

export interface TeacherAcademicProfile {
  id: string;
  user_id: string;
  institution_id: string;
  department_id: string;
  designation: string;
  employee_id: string;
  status: string;
  created_at: string;
}

export interface StudentEnrollment {
  id: string;
  student_profile_id: string;
  course_offering_id: string;
  enrollment_status: string;
  enrolled_at: string;
}

export interface TeachingAssignment {
  id: string;
  teacher_profile_id: string;
  course_offering_id: string;
  assignment_role: string;
  assigned_at: string;
  status: string;
}

export interface AcademicContextState {
  institution: Institution | null;
  department: Department | null;
  program: Program | null;
  studentProfile: StudentAcademicProfile | null;
  teacherProfile: TeacherAcademicProfile | null;
  isLoading: boolean;
  error: string | null;
}
