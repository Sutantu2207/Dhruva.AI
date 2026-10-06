/**
 * Domain 2.5: National Academic Taxonomy & India-Wide Academic Catalog Types.
 * Aligns strictly with backend Pydantic V2 schemas and SQLAlchemy models.
 */

export interface AcademicCatalogSource {
  id: string;
  code: string;
  name: string;
  organization: string;
  website_url?: string | null;
  is_authoritative: boolean;
  created_at: string;
}

export interface AcademicCatalogVersion {
  id: string;
  version_tag: string;
  source_id?: string | null;
  status: string;
  effective_date: string;
  notes?: string | null;
  created_at: string;
}

export interface AcademicDiscipline {
  id: string;
  code: string;
  name: string;
  display_name: string;
  slug: string;
  description?: string | null;
  aliases?: string[] | null;
  status: string;
  version_id?: string | null;
  source_id?: string | null;
  created_at: string;
}

export interface DegreeType {
  id: string;
  code: string;
  name: string;
  short_name: string;
  level: number;
  typical_duration_years: number;
  status: string;
  created_at: string;
}

export interface ProgramCatalog {
  id: string;
  code: string;
  name: string;
  short_name: string;
  slug: string;
  discipline_id: string;
  degree_type_id: string;
  duration_years: number;
  description?: string | null;
  aliases?: string[] | null;
  status: string;
  version_id?: string | null;
  source_id?: string | null;
  created_at: string;
}

export interface ProgramSpecialization {
  id: string;
  program_catalog_id: string;
  code: string;
  name: string;
  slug: string;
  description?: string | null;
  aliases?: string[] | null;
  status: string;
  created_at: string;
}

export interface CourseCatalog {
  id: string;
  code: string;
  title: string;
  slug: string;
  discipline_id: string;
  default_credits: number;
  academic_level: string;
  description?: string | null;
  prerequisites?: string[] | null;
  aliases?: string[] | null;
  status: string;
  version_id?: string | null;
  source_id?: string | null;
  created_at: string;
}

export interface SkillCatalog {
  id: string;
  code: string;
  name: string;
  slug: string;
  category: string;
  description?: string | null;
  aliases?: string[] | null;
  status: string;
  created_at: string;
}

export interface CareerCatalog {
  id: string;
  code: string;
  title: string;
  slug: string;
  industry: string;
  description?: string | null;
  aliases?: string[] | null;
  status: string;
  created_at: string;
}

export interface InstitutionProgramMapping {
  id: string;
  institution_id: string;
  institution_program_id: string;
  national_program_id: string;
  specialization_id?: string | null;
  local_code: string;
  local_name: string;
  is_active: boolean;
  effective_from?: string | null;
  effective_to?: string | null;
  confidence_score: number;
  notes?: string | null;
  created_at: string;
}

export interface InstitutionCourseMapping {
  id: string;
  institution_id: string;
  institution_course_id: string;
  national_course_id: string;
  local_code: string;
  local_title: string;
  is_active: boolean;
  effective_from?: string | null;
  effective_to?: string | null;
  confidence_score: number;
  notes?: string | null;
  created_at: string;
}

export interface CatalogImportJob {
  id: string;
  entity_type: string;
  source_id?: string | null;
  version_id?: string | null;
  is_dry_run: boolean;
  status: string;
  total_records: number;
  processed_records: number;
  successful_records: number;
  failed_records: number;
  duplicate_records: number;
  errors?: Record<string, unknown>[] | null;
  created_at: string;
}


export interface CatalogSearchResult {
  programs: ProgramCatalog[];
  courses: CourseCatalog[];
  skills: SkillCatalog[];
  careers: CareerCatalog[];
}
