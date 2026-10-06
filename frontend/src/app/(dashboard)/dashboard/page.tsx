"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useAuth } from "@/lib/auth-context";
import { CareerIntelligenceCard } from "@/components/career/CareerIntelligenceCard";
import {
  changePassword,
  ApiError,
  fetchMyStudentProfile,
  fetchMyTeacherProfile,
  fetchInstitutions,
  fetchDepartments,
  fetchMyEnrollments,
  fetchCatalogDisciplines,
  fetchCatalogDegreeTypes,
  fetchCatalogPrograms,
  fetchCatalogCourses,
  fetchCatalogSkills,
  fetchCatalogCareers,
  fetchCatalogVersions,
  fetchCatalogSources,
  searchCatalog,
  fetchMyStudentOverview,
  fetchMySkills,
  fetchMyProjects,
  fetchMyCertifications,
  fetchMyAchievements,
  fetchMyCareerGoals,
  fetchMyFacultyOverview,
  fetchAdminOverview,
} from "@/lib/api";
import type {
  StudentAcademicProfile,
  TeacherAcademicProfile,
  Institution,
  Department,
  StudentEnrollment,
} from "@/lib/types/academic";
import type {
  AcademicDiscipline,
  DegreeType,
  ProgramCatalog,
  CourseCatalog,
  SkillCatalog,
  CareerCatalog,
  AcademicCatalogVersion,
  AcademicCatalogSource,
  CatalogSearchResult,
} from "@/lib/types/catalog";
import type {
  StudentDashboardOverview,
  FacultyDashboardOverview,
  AdminInstitutionOverview,
  StudentSkill,
  StudentProject,
  StudentCertification,
  StudentAchievement,
  StudentCareerGoal,
} from "@/lib/types/profile";
import {
  User as UserIcon,
  ShieldCheck,
  Key,
  LogOut,
  CheckCircle2,
  Building,
  Calendar,
  Lock,
  GraduationCap,
  BookOpen,
  Globe,
  Search,
  Sparkles,
  ExternalLink,
  Award,
  Briefcase,
  Layers,
  FolderGit2,
  Users2,
  BarChart3,
  FileCheck,
  ClipboardCheck,
} from "lucide-react";
import { CourseDeliveryView } from "@/components/lms/CourseDeliveryView";
import { AssessmentHub } from "@/components/assessment/AssessmentHub";


export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  // Password change state
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [pwdError, setPwdError] = React.useState<string | null>(null);
  const [pwdSuccess, setPwdSuccess] = React.useState<string | null>(null);
  const [isChangingPwd, setIsChangingPwd] = React.useState(false);

  // RBAC live verification test state
  const [rbacTestResult, setRbacTestResult] = React.useState<{
    endpoint: string;
    status: number;
    message: string;
    isSuccess: boolean;
  } | null>(null);
  const [isTestingRbac, setIsTestingRbac] = React.useState(false);

  // Academic Context state
  const [studentProfile, setStudentProfile] = React.useState<StudentAcademicProfile | null>(null);
  const [teacherProfile, setTeacherProfile] = React.useState<TeacherAcademicProfile | null>(null);
  const [institutions, setInstitutions] = React.useState<Institution[]>([]);
  const [departments, setDepartments] = React.useState<Department[]>([]);
  const [enrollments, setEnrollments] = React.useState<StudentEnrollment[]>([]);
  const [academicLoading, setAcademicLoading] = React.useState(false);
  const [academicError, setAcademicError] = React.useState<string | null>(null);

  // National Catalog state (Domain 2.5)
  const [catalogSubTab, setCatalogSubTab] = React.useState<"disciplines" | "degrees" | "programs" | "courses" | "skills" | "careers" | "sources">("disciplines");
  const [catalogSearch, setCatalogSearch] = React.useState("");
  const [catalogSearchResult, setCatalogSearchResult] = React.useState<CatalogSearchResult | null>(null);
  const [catalogLoading, setCatalogLoading] = React.useState(false);
  const [disciplines, setDisciplines] = React.useState<AcademicDiscipline[]>([]);
  const [degreeTypes, setDegreeTypes] = React.useState<DegreeType[]>([]);
  const [programs, setPrograms] = React.useState<ProgramCatalog[]>([]);
  const [courses, setCourses] = React.useState<CourseCatalog[]>([]);
  const [skills, setSkills] = React.useState<SkillCatalog[]>([]);
  const [careers, setCareers] = React.useState<CareerCatalog[]>([]);
  const [sources, setSources] = React.useState<AcademicCatalogSource[]>([]);
  const [versions, setVersions] = React.useState<AcademicCatalogVersion[]>([]);

  // Domain 3: Profile & Workspace State
  const [studentOverview, setStudentOverview] = React.useState<StudentDashboardOverview | null>(null);
  const [facultyOverview, setFacultyOverview] = React.useState<FacultyDashboardOverview | null>(null);
  const [adminOverview, setAdminOverview] = React.useState<AdminInstitutionOverview | null>(null);
  const [studentSkills, setStudentSkills] = React.useState<StudentSkill[]>([]);
  const [studentProjects, setStudentProjects] = React.useState<StudentProject[]>([]);
  const [studentCerts, setStudentCerts] = React.useState<StudentCertification[]>([]);
  const [studentAchievements, setStudentAchievements] = React.useState<StudentAchievement[]>([]);
  const [studentCareerGoals, setStudentCareerGoals] = React.useState<StudentCareerGoal[]>([]);


  // Academic Data Fetching Hook
  React.useEffect(() => {
    if (!isAuthenticated || !user) return;
    let isCancelled = false;

    async function loadAcademicContext() {
      setAcademicLoading(true);
      setAcademicError(null);
      try {
        if (user?.role === "student") {
          try {
            const prof = await fetchMyStudentProfile();
            if (!isCancelled) setStudentProfile(prof);
          } catch {
            // No profile provisioned yet
          }
          try {
            const enrs = await fetchMyEnrollments();
            if (!isCancelled) setEnrollments(enrs);
          } catch {
            // No enrollments yet
          }
          try {
            const [overview, skls, projs, crts, achs, goals] = await Promise.all([
              fetchMyStudentOverview(),
              fetchMySkills(),
              fetchMyProjects(),
              fetchMyCertifications(),
              fetchMyAchievements(),
              fetchMyCareerGoals(),
            ]);
            if (!isCancelled) {
              setStudentOverview(overview);
              setStudentSkills(skls);
              setStudentProjects(projs);
              setStudentCerts(crts);
              setStudentAchievements(achs);
              setStudentCareerGoals(goals);
            }
          } catch {
            // Optional records
          }
        } else if (user?.role === "teacher" || user?.role === "mentor" || user?.role === "hod") {
          try {
            const tProf = await fetchMyTeacherProfile();
            if (!isCancelled) setTeacherProfile(tProf);
          } catch {
            // No profile provisioned yet
          }
          try {
            const facOverview = await fetchMyFacultyOverview();
            if (!isCancelled) setFacultyOverview(facOverview);
          } catch {
            // No faculty overview
          }
        } else if (user?.role === "institution_admin" || user?.role === "super_admin") {
          try {
            const [instList, deptList, admOverview] = await Promise.all([
              fetchInstitutions(),
              fetchDepartments(user?.institution_id || undefined),
              user?.institution_id ? fetchAdminOverview().catch(() => null) : Promise.resolve(null),
            ]);
            if (!isCancelled) {
              setInstitutions(instList);
              setDepartments(deptList);
              if (admOverview) setAdminOverview(admOverview);
            }
          } catch (err: unknown) {
            if (!isCancelled) {
              setAcademicError(err instanceof Error ? err.message : "Failed to load academic records");
            }
          }
        }
      } finally {
        if (!isCancelled) setAcademicLoading(false);
      }
    }

    async function loadCatalogData() {
      setCatalogLoading(true);
      try {
        const [discList, degList, progList, courseList, skillList, careerList, srcList, verList] = await Promise.all([
          fetchCatalogDisciplines(0, 50).catch(() => []),
          fetchCatalogDegreeTypes(0, 50).catch(() => []),
          fetchCatalogPrograms({ skip: 0, limit: 50 }).catch(() => []),
          fetchCatalogCourses({ skip: 0, limit: 50 }).catch(() => []),
          fetchCatalogSkills({ skip: 0, limit: 50 }).catch(() => []),
          fetchCatalogCareers({ skip: 0, limit: 50 }).catch(() => []),
          fetchCatalogSources().catch(() => []),
          fetchCatalogVersions().catch(() => []),
        ]);
        if (!isCancelled) {
          setDisciplines(discList);
          setDegreeTypes(degList);
          setPrograms(progList);
          setCourses(courseList);
          setSkills(skillList);
          setCareers(careerList);
          setSources(srcList);
          setVersions(verList);
        }
      } finally {
        if (!isCancelled) setCatalogLoading(false);
      }
    }

    loadAcademicContext();
    loadCatalogData();
    return () => {
      isCancelled = true;
    };
  }, [isAuthenticated, user]);

  const handleCatalogSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!catalogSearch.trim()) {
      setCatalogSearchResult(null);
      return;
    }
    setCatalogLoading(true);
    try {
      const res = await searchCatalog(catalogSearch.trim());
      setCatalogSearchResult(res);
    } catch {
      setCatalogSearchResult(null);
    } finally {
      setCatalogLoading(false);
    }
  };


  // Route protection
  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !user) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 text-center space-y-4">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
        <p className="text-sm text-slate-500">Verifying session credentials...</p>
      </main>
    );
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdError(null);
    setPwdSuccess(null);
    setIsChangingPwd(true);

    try {
      const res = await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwdSuccess(res.message);
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setPwdError(err.message);
      } else {
        setPwdError("Could not update password. Please check current password.");
      }
    } finally {
      setIsChangingPwd(false);
    }
  };

  const testRbacEndpoint = async (roleEndpoint: string) => {
    setIsTestingRbac(true);
    setRbacTestResult(null);

    const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
    try {
      const token = (await import("@/lib/api")).getMemoryAccessToken();
      const res = await fetch(`${API_BASE}/auth/test/${roleEndpoint}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();
      setRbacTestResult({
        endpoint: `/api/v1/auth/test/${roleEndpoint}`,
        status: res.status,
        message: data.detail || data.message || JSON.stringify(data),
        isSuccess: res.ok,
      });
    } catch (err: unknown) {
      setRbacTestResult({
        endpoint: `/api/v1/auth/test/${roleEndpoint}`,
        status: 0,
        message: err instanceof Error ? err.message : "Network error",
        isSuccess: false,
      });
    } finally {
      setIsTestingRbac(false);
    }
  };


  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Top Header Card */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-6 dark:border-slate-800">
        <div className="flex items-center space-x-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-bold text-xl dark:bg-indigo-950 dark:text-indigo-300">
            {user.first_name[0]}
            {user.last_name[0]}
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                {user.display_name}
              </h1>
              <Badge variant="default" className="capitalize font-mono text-xs">
                {user.role}
              </Badge>
              {user.is_verified ? (
                <Badge variant="success" className="text-[10px]">
                  Verified Account
                </Badge>
              ) : (
                <Badge variant="warning" className="text-[10px]">
                  Unverified Email
                </Badge>
              )}
            </div>
            <p className="text-xs text-slate-500 font-mono mt-1">{user.email}</p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => logout()}
          className="flex items-center space-x-1.5 text-rose-600 border-rose-200 hover:bg-rose-50 dark:border-rose-900 dark:hover:bg-rose-950/30"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign Out</span>
        </Button>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="assessments" className="w-full">
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-8 max-w-6xl">
          <TabsTrigger value="assessments" className="flex items-center space-x-1.5">
            <ClipboardCheck className="h-3.5 w-3.5" />
            <span>Assessments</span>
          </TabsTrigger>
          <TabsTrigger value="courses" className="flex items-center space-x-1.5">
            <BookOpen className="h-3.5 w-3.5" />
            <span>Courses &amp; LMS</span>
          </TabsTrigger>
          <TabsTrigger value="workspace" className="flex items-center space-x-1.5">
            <Layers className="h-3.5 w-3.5" />
            <span>Profile &amp; Workspace</span>
          </TabsTrigger>
          <TabsTrigger value="identity" className="flex items-center space-x-1.5">
            <UserIcon className="h-3.5 w-3.5" />
            <span>Identity Profile</span>
          </TabsTrigger>
          <TabsTrigger value="academic" className="flex items-center space-x-1.5">
            <GraduationCap className="h-3.5 w-3.5" />
            <span>Academic Context</span>
          </TabsTrigger>
          <TabsTrigger value="catalog" className="flex items-center space-x-1.5">
            <Globe className="h-3.5 w-3.5" />
            <span>National Catalog</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center space-x-1.5">
            <Key className="h-3.5 w-3.5" />
            <span>Security</span>
          </TabsTrigger>
          <TabsTrigger value="rbac" className="flex items-center space-x-1.5">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>RBAC Verification</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab: Assessments (Domain 5) */}
        <TabsContent value="assessments" className="pt-4 space-y-6">
          <AssessmentHub />
        </TabsContent>

        {/* Tab: Courses & LMS (Domain 4) */}
        <TabsContent value="courses" className="pt-4 space-y-6">
          <CourseDeliveryView userRole={user.role} institutionId={user.institution_id} />
        </TabsContent>

        {/* Tab: Profile & Workspace (Domain 3) */}
        <TabsContent value="workspace" className="pt-4 space-y-6">
          {user.role === "student" && (
            <div className="space-y-6">
              {/* Profile Completion Card */}
              <Card>
                <CardHeader>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <FileCheck className="h-5 w-5 text-indigo-600" />
                        <span>Academic Profile &amp; Completion Engine</span>
                      </CardTitle>
                      <CardDescription>
                        Pure deterministic completion metric based strictly on real stored credentials and artifacts.
                      </CardDescription>
                    </div>
                    {studentOverview && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                          {studentOverview.completion_percentage}%
                        </span>
                        <div className="w-28 bg-slate-200 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
                          <div
                            className="bg-indigo-600 h-full rounded-full transition-all"
                            style={{ width: `${studentOverview.completion_percentage}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {studentOverview ? (
                    <div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
                        <div>
                          <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Enrollment</p>
                          <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{studentOverview.enrollment_number}</p>
                        </div>
                        <div>
                          <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Status</p>
                          <Badge variant="outline" className="capitalize text-xs font-mono">{studentOverview.academic_status}</Badge>
                        </div>
                        <div>
                          <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Assigned Mentor</p>
                          <p className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">
                            {studentOverview.mentor_name || "Unassigned"}
                          </p>
                        </div>
                        <div>
                          <p className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Active Support</p>
                          <p className="text-sm text-slate-700 dark:text-slate-300">
                            {studentOverview.active_interventions_count} active action(s)
                          </p>
                        </div>
                      </div>

                      <div className="pt-4 flex flex-wrap gap-2 items-center">
                        <span className="text-xs text-slate-500 font-medium">Completed Sections:</span>
                        {studentOverview.completed_sections.map((sec) => (
                          <Badge key={sec} variant="success" className="text-[11px]">
                            ✓ {sec}
                          </Badge>
                        ))}
                        {studentOverview.missing_sections.map((sec) => (
                          <Badge key={sec} variant="outline" className="text-[11px] text-slate-500">
                            ○ {sec}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-6 text-sm text-slate-500">
                      No student academic profile provisioned yet. Contact your institution administrator.
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Authoritative Career Intelligence (Domain 7) */}
              <CareerIntelligenceCard careerGoals={studentCareerGoals} skills={studentSkills} />

              {/* Verified Skills & Career Goals */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-amber-500" />
                      <span>Claimed &amp; Verified Skills</span>
                    </CardTitle>
                    <CardDescription>Referencing canonical National SkillCatalog.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {studentSkills.length === 0 ? (
                      <p className="text-xs text-slate-500 py-4 text-center">No skills mapped yet.</p>
                    ) : (
                      <div className="space-y-2">
                        {studentSkills.map((s) => (
                          <div key={s.id} className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 text-xs">
                            <div>
                              <span className="font-semibold text-slate-900 dark:text-slate-100">{s.skill_name || s.skill_code || "Skill"}</span>
                              <span className="text-slate-500 ml-2 capitalize">({s.proficiency})</span>
                            </div>
                            <Badge variant={s.is_verified ? "success" : "outline"} className="text-[10px]">
                              {s.is_verified ? "Verified" : "Self Declared"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Briefcase className="h-4 w-4 text-blue-500" />
                      <span>Target Career Goals</span>
                    </CardTitle>
                    <CardDescription>Anchored to canonical National CareerCatalog.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {studentCareerGoals.length === 0 ? (
                      <p className="text-xs text-slate-500 py-4 text-center">No career goals set yet.</p>
                    ) : (
                      <div className="space-y-2">
                        {studentCareerGoals.map((g) => (
                          <div key={g.id} className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-slate-900 dark:text-slate-100">{g.career_title || g.career_code || "Career Pathway"}</span>
                              <Badge variant="default" className="text-[10px]">Priority #{g.priority}</Badge>
                            </div>
                            {g.short_term_goals && <p className="text-slate-500">{g.short_term_goals}</p>}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Projects & Certifications */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <FolderGit2 className="h-4 w-4 text-emerald-500" />
                      <span>Projects &amp; Portfolio Artifacts</span>
                    </CardTitle>
                    <CardDescription>Academic, capstone, and verified open source contributions.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {studentProjects.length === 0 ? (
                      <p className="text-xs text-slate-500 py-4 text-center">No projects documented yet.</p>
                    ) : (
                      <div className="space-y-2">
                        {studentProjects.map((p) => (
                          <div key={p.id} className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-slate-900 dark:text-slate-100">{p.title}</span>
                              <Badge variant="outline" className="capitalize text-[10px]">{p.status}</Badge>
                            </div>
                            {p.description && <p className="text-slate-500 line-clamp-1">{p.description}</p>}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Award className="h-4 w-4 text-purple-500" />
                      <span>Certifications &amp; Achievements</span>
                    </CardTitle>
                    <CardDescription>Audited credentials with verification workflow.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {studentCerts.length === 0 && studentAchievements.length === 0 ? (
                      <p className="text-xs text-slate-500 py-4 text-center">No credentials entered yet.</p>
                    ) : (
                      <div className="space-y-2">
                        {studentCerts.map((c) => (
                          <div key={c.id} className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 text-xs">
                            <div>
                              <p className="font-semibold text-slate-900 dark:text-slate-100">{c.title}</p>
                              <p className="text-[11px] text-slate-500">{c.issuer}</p>
                            </div>
                            <Badge variant={c.status === "verified" ? "success" : c.status === "rejected" ? "destructive" : "outline"} className="capitalize text-[10px]">
                              {c.status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {(user.role === "teacher" || user.role === "mentor" || user.role === "hod") && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Users2 className="h-5 w-5 text-indigo-600" />
                  <span>Faculty &amp; Mentorship Teaching Context</span>
                </CardTitle>
                <CardDescription>
                  Scoped course offerings, assigned enrolled students, and mentee cohort overview.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {facultyOverview ? (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                      <p className="text-xs text-slate-500 font-semibold uppercase">Employee ID</p>
                      <p className="text-lg font-bold text-slate-900 dark:text-slate-100">{facultyOverview.employee_id}</p>
                    </div>
                    <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                      <p className="text-xs text-slate-500 font-semibold uppercase">Assigned Offerings</p>
                      <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">{facultyOverview.assigned_offerings_count}</p>
                    </div>
                    <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                      <p className="text-xs text-slate-500 font-semibold uppercase">Enrolled Students</p>
                      <p className="text-lg font-bold text-slate-900 dark:text-slate-100">{facultyOverview.total_enrolled_students}</p>
                    </div>
                    <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                      <p className="text-xs text-slate-500 font-semibold uppercase">Active Mentees</p>
                      <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">{facultyOverview.assigned_mentees_count}</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 py-4 text-center">Faculty teaching profile pending institutional assignment.</p>
                )}
              </CardContent>
            </Card>
          )}

          {(user.role === "institution_admin" || user.role === "super_admin") && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-indigo-600" />
                    <span>Institutional Real-Time Metrics</span>
                  </CardTitle>
                  <CardDescription>Real aggregated counts calculated directly from active database state.</CardDescription>
                </CardHeader>
                <CardContent>
                  {adminOverview ? (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                        <p className="text-xs text-slate-500 font-semibold uppercase">Students Enrolled</p>
                        <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{adminOverview.total_students}</p>
                      </div>
                      <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                        <p className="text-xs text-slate-500 font-semibold uppercase">Active Faculty</p>
                        <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{adminOverview.total_faculty}</p>
                      </div>
                      <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                        <p className="text-xs text-slate-500 font-semibold uppercase">Active Programs</p>
                        <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{adminOverview.active_programs}</p>
                      </div>
                      <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800">
                        <p className="text-xs text-slate-500 font-semibold uppercase">Courses Catalog</p>
                        <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{adminOverview.total_courses}</p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500 py-4 text-center">Institution overview metrics available when an institution is bound.</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Tab: Academic Context (Domain 2) */}
        <TabsContent value="academic" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Institutional &amp; Academic Hierarchy</CardTitle>
              <CardDescription>
                Persistent academic membership, cohort batch, and enrollment scoping (Domain 2).
              </CardDescription>
            </CardHeader>
            <CardContent>
              {academicLoading ? (
                <div className="flex items-center space-x-3 py-8 text-sm text-slate-500">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
                  <span>Loading institutional data...</span>
                </div>
              ) : academicError ? (
                <Alert variant="destructive">
                  <AlertTitle>Academic Record Error</AlertTitle>
                  <AlertDescription>{academicError}</AlertDescription>
                </Alert>
              ) : user.role === "student" ? (
                studentProfile ? (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                        <span className="text-xs text-slate-500">Official Enrollment Number</span>
                        <div className="font-mono text-sm font-semibold text-indigo-600">
                          {studentProfile.enrollment_number}
                        </div>
                      </div>
                      <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                        <span className="text-xs text-slate-500">Academic Status</span>
                        <div className="font-mono text-sm font-semibold capitalize text-emerald-600">
                          {studentProfile.academic_status}
                        </div>
                      </div>
                      <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                        <span className="text-xs text-slate-500">Academic Period</span>
                        <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                          {studentProfile.admission_year} - {studentProfile.graduation_year}
                        </div>
                      </div>
                    </div>

                    <div className="pt-2">
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center space-x-2">
                        <BookOpen className="h-4 w-4 text-indigo-600" />
                        <span>Current Course Enrollments ({enrollments.length})</span>
                      </h3>
                      {enrollments.length === 0 ? (
                        <p className="text-xs text-slate-500">No active course enrollments assigned for the current period.</p>
                      ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {enrollments.map((enr) => (
                            <div key={enr.id} className="p-3 rounded border border-slate-200 dark:border-slate-800 flex justify-between items-center text-xs">
                              <span className="font-mono">{enr.course_offering_id}</span>
                              <Badge variant="outline" className="capitalize text-[10px]">{enr.enrollment_status}</Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <Alert>
                    <AlertTitle>Pending Academic Profile Assignment</AlertTitle>
                    <AlertDescription className="text-xs">
                      Your identity account is active. Academic membership (Institution, Program, Batch, and Section) must be provisioned through your institution&apos;s administrative onboarding workflow.
                    </AlertDescription>
                  </Alert>
                )
              ) : user.role === "teacher" ? (
                teacherProfile ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                      <span className="text-xs text-slate-500">Faculty Designation</span>
                      <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                        {teacherProfile.designation}
                      </div>
                    </div>
                    <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                      <span className="text-xs text-slate-500">Employee ID</span>
                      <div className="font-mono text-sm font-semibold text-indigo-600">
                        {teacherProfile.employee_id}
                      </div>
                    </div>
                    <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                      <span className="text-xs text-slate-500">Faculty Status</span>
                      <div className="font-mono text-sm font-semibold capitalize text-emerald-600">
                        {teacherProfile.status}
                      </div>
                    </div>
                  </div>
                ) : (
                  <Alert>
                    <AlertTitle>Faculty Profile Not Yet Linked</AlertTitle>
                    <AlertDescription className="text-xs">
                      Teacher academic profile has not yet been assigned by the Institutional Administrator.
                    </AlertDescription>
                  </Alert>
                )
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                      <span className="text-xs text-slate-500">Managed Institutions</span>
                      <div className="text-lg font-bold text-indigo-600">
                        {institutions.length}
                      </div>
                    </div>
                    <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                      <span className="text-xs text-slate-500">Active Departments</span>
                      <div className="text-lg font-bold text-indigo-600">
                        {departments.length}
                      </div>
                    </div>
                  </div>
                  {institutions.length > 0 && (
                    <div className="pt-2">
                      <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Registered Institutions</h4>
                      <div className="space-y-2">
                        {institutions.map((inst) => (
                          <div key={inst.id} className="p-3 rounded border border-slate-200 dark:border-slate-800 flex justify-between items-center text-xs">
                            <span className="font-medium text-slate-900 dark:text-slate-100">{inst.name}</span>
                            <Badge variant="outline" className="font-mono text-[10px]">{inst.code}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>


        {/* Tab 1: Identity Profile Details */}
        <TabsContent value="identity" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Authenticated Account Attributes</CardTitle>
              <CardDescription>
                Core security identity record retrieved from PostgreSQL via FastAPI backend.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                  <span className="text-xs text-slate-500">Internal User ID</span>
                  <div className="font-mono text-xs font-semibold truncate text-slate-800 dark:text-slate-200">
                    {user.id}
                  </div>
                </div>

                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                  <span className="text-xs text-slate-500">Official Assigned Role</span>
                  <div className="font-mono text-xs font-semibold capitalize text-indigo-600">
                    {user.role}
                  </div>
                </div>

                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                  <span className="text-xs text-slate-500">Account Status</span>
                  <div className="flex items-center space-x-1 font-mono text-xs font-semibold text-emerald-600">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Active</span>
                  </div>
                </div>

                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                  <span className="text-xs text-slate-500">Institution Scope</span>
                  <div className="flex items-center space-x-1 text-xs font-semibold text-slate-800 dark:text-slate-200">
                    <Building className="h-3.5 w-3.5 text-slate-400" />
                    <span>{user.institution_id || "Global Campus"}</span>
                  </div>
                </div>

                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                  <span className="text-xs text-slate-500">Registered On</span>
                  <div className="flex items-center space-x-1 text-xs font-semibold text-slate-800 dark:text-slate-200">
                    <Calendar className="h-3.5 w-3.5 text-slate-400" />
                    <span>{new Date(user.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                  <span className="text-xs text-slate-500">Password Hashing</span>
                  <div className="flex items-center space-x-1 font-mono text-xs font-semibold text-slate-800 dark:text-slate-200">
                    <Lock className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Argon2id (RFC 9106)</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Security & Password Change */}
        <TabsContent value="security" className="pt-4">
          <Card className="max-w-xl">
            <CardHeader>
              <CardTitle className="text-lg">Update Account Password</CardTitle>
              <CardDescription>
                Changing your password automatically revokes active sessions across other devices.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleChangePassword}>
              <CardContent className="space-y-4">
                {pwdError && (
                  <Alert variant="destructive">
                    <AlertTitle>Password Update Failed</AlertTitle>
                    <AlertDescription>{pwdError}</AlertDescription>
                  </Alert>
                )}

                {pwdSuccess && (
                  <Alert variant="success">
                    <AlertTitle>Success</AlertTitle>
                    <AlertDescription>{pwdSuccess}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-1">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Current Password
                  </label>
                  <input
                    type="password"
                    required
                    className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900"
                    placeholder="Enter current password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    New Password
                  </label>
                  <input
                    type="password"
                    required
                    className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500 dark:border-slate-700 dark:bg-slate-900"
                    placeholder="Min 8 chars with uppercase, digit, symbol"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
              </CardContent>

              <CardFooter>
                <Button
                  type="submit"
                  isLoading={isChangingPwd}
                  disabled={isChangingPwd || !currentPassword || !newPassword}
                >
                  Change Password
                </Button>
              </CardFooter>
            </form>
          </Card>
        </TabsContent>

        {/* Tab 3: RBAC Live Authorization Verification */}
        <TabsContent value="rbac" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Backend RBAC Enforcement Verification</CardTitle>
              <CardDescription>
                Demonstrates that route protection is strictly enforced by the backend, not by frontend route hiding.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                You are currently authenticated as <span className="font-semibold text-indigo-600">{user.role}</span>.
                Click each button to fire an authorized request to the corresponding role-restricted backend endpoint:
              </p>

              <div className="flex flex-wrap gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => testRbacEndpoint("student-only")}
                  isLoading={isTestingRbac}
                >
                  Test Student-Only Endpoint
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => testRbacEndpoint("teacher-only")}
                  isLoading={isTestingRbac}
                >
                  Test Teacher-Only Endpoint
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => testRbacEndpoint("admin-only")}
                  isLoading={isTestingRbac}
                >
                  Test Admin-Only Endpoint
                </Button>
              </div>

              {rbacTestResult && (
                <div className="mt-4 p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500">Endpoint:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {rbacTestResult.endpoint}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500">HTTP Status:</span>
                    <Badge variant={rbacTestResult.isSuccess ? "success" : "destructive"}>
                      {rbacTestResult.status} {rbacTestResult.isSuccess ? "Authorized (200)" : "Forbidden (403)"}
                    </Badge>
                  </div>
                  <div className="text-xs font-mono text-slate-600 dark:text-slate-300 pt-1 border-t border-slate-200 dark:border-slate-800">
                    <span className="text-slate-400">Response: </span>
                    {rbacTestResult.message}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: National Academic Catalog (Domain 2.5) */}
        <TabsContent value="catalog" className="pt-4 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <CardTitle className="text-lg">National Academic Taxonomy &amp; Catalog</CardTitle>
                    <Badge variant="default" className="text-[10px] bg-indigo-600">
                      Domain 2.5 Active
                    </Badge>
                  </div>
                  <CardDescription className="mt-1">
                    India-wide higher-education taxonomy covering all legitimate disciplines, degree levels, programs, courses, skills, and career mappings.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    Multi-Disciplinary Model
                  </Badge>
                  <Badge variant="success" className="text-xs">
                    Versioned Ingestion
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Search Bar */}
              <form onSubmit={handleCatalogSearch} className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={catalogSearch}
                    onChange={(e) => setCatalogSearch(e.target.value)}
                    placeholder="Search national programs, courses, skills, or careers (e.g., Computer Science, Robotics, Python)..."
                    className="w-full pl-9 pr-4 py-2 text-sm rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <Button type="submit" size="sm" isLoading={catalogLoading}>
                  Search
                </Button>
                {catalogSearchResult && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setCatalogSearch("");
                      setCatalogSearchResult(null);
                    }}
                  >
                    Clear
                  </Button>
                )}
              </form>

              {/* Search Results Display */}
              {catalogSearchResult && (
                <div className="p-4 rounded-lg border border-indigo-200 dark:border-indigo-900 bg-indigo-50/50 dark:bg-indigo-950/20 space-y-4">
                  <h3 className="text-sm font-semibold text-indigo-900 dark:text-indigo-200 flex items-center gap-1.5">
                    <Sparkles className="h-4 w-4 text-indigo-600" />
                    <span>Search Results for &quot;{catalogSearch}&quot;</span>
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Programs */}
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        Programs ({catalogSearchResult.programs.length})
                      </span>
                      {catalogSearchResult.programs.length === 0 ? (
                        <p className="text-xs text-slate-500">None found</p>
                      ) : (
                        catalogSearchResult.programs.map((p) => (
                          <div key={p.id} className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
                            <div className="font-semibold text-slate-900 dark:text-slate-100">{p.name}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{p.code} &bull; {p.duration_years} Years</div>
                          </div>
                        ))
                      )}
                    </div>
                    {/* Courses */}
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        Courses ({catalogSearchResult.courses.length})
                      </span>
                      {catalogSearchResult.courses.length === 0 ? (
                        <p className="text-xs text-slate-500">None found</p>
                      ) : (
                        catalogSearchResult.courses.map((c) => (
                          <div key={c.id} className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
                            <div className="font-semibold text-slate-900 dark:text-slate-100">{c.title}</div>
                            <div className="text-[10px] text-slate-500 font-mono">{c.code} &bull; {c.default_credits} Credits</div>
                          </div>
                        ))
                      )}
                    </div>
                    {/* Skills */}
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        Skills ({catalogSearchResult.skills.length})
                      </span>
                      {catalogSearchResult.skills.length === 0 ? (
                        <p className="text-xs text-slate-500">None found</p>
                      ) : (
                        catalogSearchResult.skills.map((s) => (
                          <div key={s.id} className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
                            <div className="font-semibold text-slate-900 dark:text-slate-100">{s.name}</div>
                            <Badge variant="outline" className="text-[10px] capitalize">{s.category}</Badge>
                          </div>
                        ))
                      )}
                    </div>
                    {/* Careers */}
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        Careers ({catalogSearchResult.careers.length})
                      </span>
                      {catalogSearchResult.careers.length === 0 ? (
                        <p className="text-xs text-slate-500">None found</p>
                      ) : (
                        catalogSearchResult.careers.map((cr) => (
                          <div key={cr.id} className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
                            <div className="font-semibold text-slate-900 dark:text-slate-100">{cr.title}</div>
                            <div className="text-[10px] text-slate-500">{cr.industry}</div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-Navigation Pills */}
              <div className="flex flex-wrap gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
                <button
                  type="button"
                  onClick={() => setCatalogSubTab("disciplines")}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    catalogSubTab === "disciplines"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                  }`}
                >
                  Disciplines ({disciplines.length})
                </button>
                <button
                  type="button"
                  onClick={() => setCatalogSubTab("degrees")}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    catalogSubTab === "degrees"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                  }`}
                >
                  Degree Types ({degreeTypes.length})
                </button>
                <button
                  type="button"
                  onClick={() => setCatalogSubTab("programs")}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    catalogSubTab === "programs"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                  }`}
                >
                  National Programs ({programs.length})
                </button>
                <button
                  type="button"
                  onClick={() => setCatalogSubTab("courses")}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    catalogSubTab === "courses"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                  }`}
                >
                  National Courses ({courses.length})
                </button>
                <button
                  type="button"
                  onClick={() => setCatalogSubTab("skills")}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    catalogSubTab === "skills"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                  }`}
                >
                  Skills Taxonomy ({skills.length})
                </button>
                <button
                  type="button"
                  onClick={() => setCatalogSubTab("careers")}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    catalogSubTab === "careers"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                  }`}
                >
                  Careers ({careers.length})
                </button>
                <button
                  type="button"
                  onClick={() => setCatalogSubTab("sources")}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    catalogSubTab === "sources"
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                  }`}
                >
                  Authorities &amp; Versions ({sources.length}/{versions.length})
                </button>
              </div>

              {/* Sub-tab Content: Disciplines */}
              {catalogSubTab === "disciplines" && (
                <div className="space-y-3">
                  <div className="text-xs text-slate-500 font-mono">
                    Broad academic disciplines establishing India-wide institutional eligibility.
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {disciplines.length === 0 ? (
                      <p className="text-sm text-slate-500 col-span-full">No disciplines loaded.</p>
                    ) : (
                      disciplines.map((d) => (
                        <div key={d.id} className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{d.name}</span>
                            <Badge variant="outline" className="font-mono text-[10px]">{d.code}</Badge>
                          </div>
                          {d.description && <p className="text-xs text-slate-500 line-clamp-2">{d.description}</p>}
                          {d.aliases && d.aliases.length > 0 && (
                            <div className="flex flex-wrap gap-1 pt-1">
                              {d.aliases.map((al, idx) => (
                                <span key={idx} className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-1.5 py-0.5 rounded">
                                  {al}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Sub-tab Content: Degree Types */}
              {catalogSubTab === "degrees" && (
                <div className="space-y-3">
                  <div className="text-xs text-slate-500 font-mono">
                    Data-driven academic degree tiers: Certificate, Diploma, UG, PG, and Doctoral levels.
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {degreeTypes.length === 0 ? (
                      <p className="text-sm text-slate-500 col-span-full">No degree types loaded.</p>
                    ) : (
                      degreeTypes.map((deg) => (
                        <div key={deg.id} className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{deg.name}</span>
                            <Badge variant="outline" className="font-mono text-[10px]">{deg.short_name}</Badge>
                          </div>
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span>Level {deg.level}</span>
                            <span>{deg.typical_duration_years} Years Typical</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Sub-tab Content: Programs */}
              {catalogSubTab === "programs" && (
                <div className="space-y-3">
                  <div className="text-xs text-slate-500 font-mono">
                    National program definitions decoupled from specific institutions.
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {programs.length === 0 ? (
                      <p className="text-sm text-slate-500 col-span-full">No national programs loaded.</p>
                    ) : (
                      programs.map((p) => (
                        <div key={p.id} className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">{p.name}</h4>
                              <p className="text-xs text-slate-500">{p.short_name} &bull; {p.duration_years} Years Duration</p>
                            </div>
                            <Badge variant="outline" className="font-mono text-[10px]">{p.code}</Badge>
                          </div>
                          {p.description && <p className="text-xs text-slate-600 dark:text-slate-400">{p.description}</p>}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Sub-tab Content: Courses */}
              {catalogSubTab === "courses" && (
                <div className="space-y-3">
                  <div className="text-xs text-slate-500 font-mono">
                    National course catalog with credits, level, and prerequisite taxonomies.
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {courses.length === 0 ? (
                      <p className="text-sm text-slate-500 col-span-full">No national courses loaded.</p>
                    ) : (
                      courses.map((c) => (
                        <div key={c.id} className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">{c.title}</h4>
                              <p className="text-xs text-slate-500 font-mono">{c.code} &bull; {c.default_credits} Credits &bull; Level: {c.academic_level}</p>
                            </div>
                            <Badge variant="outline" className="text-[10px] capitalize">{c.status}</Badge>
                          </div>
                          {c.description && <p className="text-xs text-slate-600 dark:text-slate-400">{c.description}</p>}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Sub-tab Content: Skills */}
              {catalogSubTab === "skills" && (
                <div className="space-y-3">
                  <div className="text-xs text-slate-500 font-mono">
                    Deterministic skill catalog independently mapped to programs, courses, and careers.
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {skills.length === 0 ? (
                      <p className="text-sm text-slate-500 col-span-full">No skills loaded.</p>
                    ) : (
                      skills.map((s) => (
                        <div key={s.id} className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{s.name}</span>
                            <Badge variant="outline" className="text-[10px] capitalize">{s.category}</Badge>
                          </div>
                          <p className="text-xs text-slate-500 font-mono">{s.code}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Sub-tab Content: Careers */}
              {catalogSubTab === "careers" && (
                <div className="space-y-3">
                  <div className="text-xs text-slate-500 font-mono">
                    Career pathways aligned with skills for deterministic recommendation intelligence.
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {careers.length === 0 ? (
                      <p className="text-sm text-slate-500 col-span-full">No careers loaded.</p>
                    ) : (
                      careers.map((cr) => (
                        <div key={cr.id} className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">{cr.title}</h4>
                              <p className="text-xs text-slate-500 font-mono">{cr.code} &bull; {cr.industry}</p>
                            </div>
                          </div>
                          {cr.description && <p className="text-xs text-slate-600 dark:text-slate-400">{cr.description}</p>}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Sub-tab Content: Sources & Versions */}
              {catalogSubTab === "sources" && (
                <div className="space-y-4">
                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                      Regulatory &amp; Statutory Academic Bodies
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {sources.length === 0 ? (
                        <p className="text-xs text-slate-500">No sources registered yet.</p>
                      ) : (
                        sources.map((src) => (
                          <div key={src.id} className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{src.name}</span>
                              <Badge variant="outline" className="font-mono text-[10px]">{src.code}</Badge>
                            </div>
                            <p className="text-xs text-slate-500">{src.organization}</p>
                            {src.website_url && (
                              <a
                                href={src.website_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-[11px] text-indigo-600 dark:text-indigo-400 hover:underline"
                              >
                                <span>Official Portal</span>
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  <div className="pt-2">
                    <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                      Catalog Release Releases &amp; Version History
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {versions.length === 0 ? (
                        <p className="text-xs text-slate-500">No version releases recorded yet.</p>
                      ) : (
                        versions.map((v) => (
                          <div key={v.id} className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">Release {v.version_tag}</span>
                              <Badge variant="success" className="text-[10px] capitalize">{v.status}</Badge>
                            </div>
                            <p className="text-xs text-slate-500">Effective: {v.effective_date}</p>
                            {v.notes && <p className="text-xs text-slate-600 dark:text-slate-400">{v.notes}</p>}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  );
}

