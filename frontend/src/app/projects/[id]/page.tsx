"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ShieldCheck,
  AlertCircle,
  ExternalLink,
  Code2,
  FileText,
  Users,
  Award,
  Sparkles,
  Plus,
  Compass,
  ChevronRight,
  Globe,
  Lock,
  Building,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  fetchProjectDetail,
  fetchProjectQuality,
  fetchProjectCareerRelevance,
} from "@/lib/api";
import type {
  StudentProjectDetail,
  ProjectQualityScore,
  CareerRelevanceItem,
} from "@/lib/types";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = React.useState<StudentProjectDetail | null>(null);
  const [quality, setQuality] = React.useState<ProjectQualityScore | null>(null);
  const [careerRelevance, setCareerRelevance] = React.useState<CareerRelevanceItem | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!projectId) return;
    let active = true;
    Promise.all([
      fetchProjectDetail(projectId),
      fetchProjectQuality(projectId).catch(() => null),
      fetchProjectCareerRelevance(projectId).catch(() => null),
    ])
      .then(([pData, qData, cData]) => {
        if (active) {
          setProject(pData);
          setQuality(qData);
          setCareerRelevance(cData);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load project details");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex items-center justify-center font-mono text-sm text-slate-400">
        Loading project intelligence graph...
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 max-w-4xl mx-auto space-y-4">
        <Link href="/projects" className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to projects
        </Link>
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-900/60 text-rose-300 font-mono text-sm">
          {error || "Project not found or private."}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 space-y-8 max-w-7xl mx-auto">
      {/* Navigation & Header */}
      <div className="space-y-4 border-b border-slate-800/80 pb-6">
        <Link
          href="/projects"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Projects Dashboard
        </Link>

        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge
                variant="outline"
                className="capitalize font-mono text-xs border-indigo-500/40 bg-indigo-950/30 text-indigo-300"
              >
                {project.project_type.replace("_", " ")}
              </Badge>
              <Badge
                variant="outline"
                className="capitalize font-mono text-xs border-slate-700 bg-slate-900 text-slate-300"
              >
                {project.status.replace("_", " ")}
              </Badge>
              {project.visibility === "public" ? (
                <Badge variant="outline" className="text-xs border-emerald-800/60 bg-emerald-950/30 text-emerald-400 flex items-center gap-1 font-mono">
                  <Globe className="w-3 h-3" /> Public
                </Badge>
              ) : project.visibility === "institution" ? (
                <Badge variant="outline" className="text-xs border-sky-800/60 bg-sky-950/30 text-sky-400 flex items-center gap-1 font-mono">
                  <Building className="w-3 h-3" /> Institution
                </Badge>
              ) : (
                <Badge variant="outline" className="text-xs border-slate-800 bg-slate-900 text-slate-500 flex items-center gap-1 font-mono">
                  <Lock className="w-3 h-3" /> Private
                </Badge>
              )}
              {project.is_verified ? (
                <Badge className="bg-emerald-950 text-emerald-300 border border-emerald-800 text-xs font-mono flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Faculty Verified
                </Badge>
              ) : (
                <Badge variant="outline" className="text-slate-400 border-slate-700 text-xs font-mono">
                  {project.verification_status}
                </Badge>
              )}
            </div>

            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-100">
              {project.title}
            </h1>
            <p className="text-sm md:text-base text-slate-400 max-w-3xl">
              {project.short_description || project.description || "No description provided."}
            </p>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-wrap items-center gap-3 self-start">
            <Link href={`/projects/${project.id}/evidence`}>
              <Button className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs">
                <Plus className="w-3.5 h-3.5 mr-1.5" /> Submit Evidence
              </Button>
            </Link>
            <Link href={`/projects/${project.id}/review`}>
              <Button variant="outline" className="border-indigo-500/40 text-indigo-300 hover:bg-indigo-950/40 text-xs">
                <Award className="w-3.5 h-3.5 mr-1.5" /> Faculty Review
              </Button>
            </Link>
          </div>
        </div>

        {/* Quick External Links */}
        <div className="flex flex-wrap items-center gap-4 pt-2 text-xs font-mono text-slate-400">
          {project.repository_url && (
            <a
              href={project.repository_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-indigo-400 hover:text-indigo-300 transition underline underline-offset-4"
            >
              <Code2 className="w-4 h-4" /> Source Code <ExternalLink className="w-3 h-3" />
            </a>
          )}
          {project.live_url && (
            <a
              href={project.live_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-emerald-400 hover:text-emerald-300 transition underline underline-offset-4"
            >
              <ExternalLink className="w-4 h-4" /> Live Deployment
            </a>
          )}
          {project.documentation_url && (
            <a
              href={project.documentation_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-sky-400 hover:text-sky-300 transition underline underline-offset-4"
            >
              <FileText className="w-4 h-4" /> Documentation
            </a>
          )}
          {project.demo_url && (
            <a
              href={project.demo_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-purple-400 hover:text-purple-300 transition underline underline-offset-4"
            >
              <Sparkles className="w-4 h-4" /> Demo Video
            </a>
          )}
        </div>
      </div>

      {/* Primary Intelligence Metrics Ribbon */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Quality Card */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-mono uppercase text-indigo-400 flex items-center justify-between">
              <span>Deterministic Quality Score</span>
              <span className="text-[10px] text-slate-500">{quality?.algorithm_version || "v1.0.0"}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-bold text-slate-100">
                {project.quality_score !== null && project.quality_score !== undefined
                  ? `${project.quality_score}`
                  : "N/A"}
              </span>
              <span className="text-xs text-slate-400">/ 100 benchmark</span>
            </div>
            <Progress
              value={project.quality_score || 0}
              className="h-1.5 bg-slate-800 mt-3"
            />
            <p className="text-xs text-slate-500 mt-2">
              Weighted composite across Technical Depth, Architecture, Testing, and Faculty Verification.
            </p>
          </CardContent>
        </Card>

        {/* Career Fit Card */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-mono uppercase text-sky-400 flex items-center justify-between">
              <span>Career Trajectory Relevance</span>
              <Compass className="w-4 h-4 text-sky-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            {careerRelevance ? (
              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-slate-100 capitalize">
                    {careerRelevance.relevance_tier} Fit
                  </span>
                  <span className="text-xs text-indigo-300 font-mono">({careerRelevance.relevance_score}/100)</span>
                </div>
                <div className="text-xs text-slate-400 mt-1 line-clamp-1">
                  Target: <strong className="text-slate-200">{careerRelevance.career_title}</strong>
                </div>
                <div className="text-xs text-slate-500 mt-2">
                  {careerRelevance.matched_skills_count} skills overlap with industry requirements.
                </div>
              </div>
            ) : (
              <div>
                <div className="text-base font-semibold text-slate-300">Goal Not Mapped</div>
                <p className="text-xs text-slate-500 mt-1">
                  Set a primary career goal in Career Intelligence to compute practical skill relevance.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Contribution Bounds Card */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-mono uppercase text-purple-400 flex items-center justify-between">
              <span>My Contributed Scope</span>
              <Users className="w-4 h-4 text-purple-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-slate-100 capitalize">
                {project.team_or_individual === "individual" ? "Solo Author" : project.role || "Team Contributor"}
              </span>
              {project.team_size > 1 && (
                <span className="text-xs text-slate-400">({project.team_size} members)</span>
              )}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {project.modules_contributed && project.modules_contributed.length > 0 ? (
                <span>Modules: {project.modules_contributed.join(", ")}</span>
              ) : (
                <span>Contribution scope defined in description.</span>
              )}
            </div>
            <div className="text-xs text-slate-500 mt-2">
              Evidence strength is weighted by personal execution, not team proxy.
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Tabbed Intelligence View */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-slate-900 border border-slate-800 p-1 flex-wrap">
          <TabsTrigger value="overview" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white text-xs">
            Overview & Problem
          </TabsTrigger>
          <TabsTrigger value="quality" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white text-xs">
            Quality Breakdown
          </TabsTrigger>
          <TabsTrigger value="skills" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white text-xs">
            Skills & Concepts ({project.skills.length + project.concepts.length})
          </TabsTrigger>
          <TabsTrigger value="evidence" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white text-xs">
            Empirical Evidence ({project.evidence.length})
          </TabsTrigger>
          <TabsTrigger value="reviews" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white text-xs">
            Faculty Reviews ({project.reviews.length})
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader>
                <CardTitle className="text-sm font-bold text-slate-200">Problem Statement</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                {project.problem_statement || "No formal problem statement documented."}
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader>
                <CardTitle className="text-sm font-bold text-slate-200">Engineered Solution</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                {project.solution || "No formal solution architecture documented."}
              </CardContent>
            </Card>
          </div>

          <Card className="bg-slate-900/60 border-slate-800">
            <CardHeader>
              <CardTitle className="text-sm font-bold text-slate-200">Technologies & Architecture Stack</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {project.technologies && project.technologies.length > 0 ? (
                  project.technologies.map((t, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-md font-mono text-xs bg-slate-800/90 text-indigo-300 border border-slate-700"
                    >
                      {t}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500 font-mono">No technologies tagged.</span>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Deterministic Quality Breakdown */}
        <TabsContent value="quality" className="space-y-6">
          {quality ? (
            <div className="space-y-6">
              <Card className="bg-slate-900/60 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-base font-bold text-slate-200">
                    6-Dimension Explainable Quality Breakdown
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-400">
                    Calculated by ProjectQualityEngine without arbitrary numbers. Every dimension has provenance.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-slate-300">Technical Depth (25%)</span>
                        <span className="text-indigo-400 font-bold">{quality.technical_depth}/100</span>
                      </div>
                      <Progress value={quality.technical_depth} className="h-1.5 bg-slate-800" />
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-slate-300">Implementation Quality (20%)</span>
                        <span className="text-indigo-400 font-bold">{quality.implementation_quality}/100</span>
                      </div>
                      <Progress value={quality.implementation_quality} className="h-1.5 bg-slate-800" />
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-slate-300">Documentation Quality (15%)</span>
                        <span className="text-indigo-400 font-bold">{quality.documentation_quality}/100</span>
                      </div>
                      <Progress value={quality.documentation_quality} className="h-1.5 bg-slate-800" />
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-slate-300">Testing Quality (15%)</span>
                        <span className="text-indigo-400 font-bold">{quality.testing_quality}/100</span>
                      </div>
                      <Progress value={quality.testing_quality} className="h-1.5 bg-slate-800" />
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-slate-300">Architecture Quality (15%)</span>
                        <span className="text-indigo-400 font-bold">{quality.architecture_quality}/100</span>
                      </div>
                      <Progress value={quality.architecture_quality} className="h-1.5 bg-slate-800" />
                    </div>

                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                      <div className="flex justify-between items-center text-xs font-mono">
                        <span className="text-slate-300">Verification Strength (10%)</span>
                        <span className="text-indigo-400 font-bold">{quality.verification_strength}/100</span>
                      </div>
                      <Progress value={quality.verification_strength} className="h-1.5 bg-slate-800" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {quality.missing_elements && quality.missing_elements.length > 0 && (
                <Card className="bg-amber-950/20 border-amber-900/50">
                  <CardHeader>
                    <CardTitle className="text-sm font-bold text-amber-300 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-amber-400" /> Completeness Recommendations
                    </CardTitle>
                    <CardDescription className="text-xs text-amber-400/80">
                      Actionable steps to elevate this project score into verified advanced tiers:
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {quality.missing_elements.map((rec, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-slate-300 font-mono">
                        <ChevronRight className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>{rec}</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <div className="p-10 text-center text-slate-500 font-mono text-sm">
              Quality evaluation not yet computed.
            </div>
          )}
        </TabsContent>

        {/* Tab 3: Skills & Concepts */}
        <TabsContent value="skills" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Skills */}
            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader>
                <CardTitle className="text-sm font-bold text-slate-200">Skills Demonstrated</CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Distinguishing student claim from verified proficiency.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {project.skills.length === 0 ? (
                  <p className="text-xs text-slate-500 font-mono">No skills mapped yet.</p>
                ) : (
                  project.skills.map((s) => (
                    <div
                      key={s.id}
                      className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-sm text-slate-200">{s.skill_name}</div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Claimed: {s.claimed_level} • Source: {s.source}
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={
                          s.verification_status === "verified"
                            ? "border-emerald-700 bg-emerald-950/40 text-emerald-300 font-mono text-[10px]"
                            : "border-slate-700 bg-slate-800 text-slate-400 font-mono text-[10px]"
                        }
                      >
                        {s.verification_status}
                      </Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Concepts */}
            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader>
                <CardTitle className="text-sm font-bold text-slate-200">Canonical Concepts</CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Connected directly to curriculum concept nodes.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {project.concepts.length === 0 ? (
                  <p className="text-xs text-slate-500 font-mono">No concepts mapped.</p>
                ) : (
                  project.concepts.map((c) => (
                    <div
                      key={c.id}
                      className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-sm text-slate-200">{c.concept_name}</div>
                        <div className="text-[11px] text-slate-500 font-mono">
                          Level: {c.demonstrated_level}
                        </div>
                      </div>
                      <Badge variant="outline" className="border-slate-700 text-slate-400 font-mono text-[10px]">
                        {c.verification_status}
                      </Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 4: Empirical Evidence */}
        <TabsContent value="evidence" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-slate-200">Empirical Evidence Ledger</h3>
            <Link href={`/projects/${project.id}/evidence`}>
              <Button size="sm" className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs">
                <Plus className="w-3.5 h-3.5 mr-1" /> Add Evidence Item
              </Button>
            </Link>
          </div>

          {project.evidence.length === 0 ? (
            <Card className="bg-slate-900/40 border-dashed border-slate-800 p-8 text-center">
              <p className="text-sm text-slate-400">
                No empirical evidence records submitted yet. Add test reports, live links, or architecture diagrams.
              </p>
            </Card>
          ) : (
            <div className="space-y-3">
              {project.evidence.map((ev) => (
                <Card key={ev.id} className="bg-slate-900/60 border-slate-800">
                  <CardContent className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-slate-200">{ev.title}</span>
                        <Badge
                          variant="outline"
                          className="font-mono text-[10px] uppercase border-slate-700 bg-slate-800 text-slate-400"
                        >
                          {ev.evidence_type.replace("_", " ")}
                        </Badge>
                      </div>
                      <div className="text-xs text-slate-400 font-mono line-clamp-1">
                        Ref: <span className="text-indigo-300">{ev.source_reference}</span> (Source: {ev.source})
                      </div>
                      {ev.description && <p className="text-xs text-slate-400">{ev.description}</p>}
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-[10px] font-mono text-slate-500">Strength</div>
                        <div className="text-xs font-bold text-slate-200 font-mono">
                          {Math.round(ev.evidence_strength * 100)}%
                        </div>
                      </div>
                      <Badge
                        className={
                          ev.verification_status === "verified"
                            ? "bg-emerald-950 text-emerald-300 border-emerald-800 text-xs font-mono"
                            : ev.verification_status === "rejected"
                            ? "bg-rose-950 text-rose-300 border-rose-800 text-xs font-mono"
                            : "bg-slate-800 text-slate-300 border-slate-700 text-xs font-mono"
                        }
                      >
                        {ev.verification_status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Tab 5: Faculty Reviews */}
        <TabsContent value="reviews" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-slate-200">Faculty & Mentor Rubric Reviews</h3>
            <Link href={`/projects/${project.id}/review`}>
              <Button size="sm" variant="outline" className="border-indigo-500/40 text-indigo-300 text-xs">
                <Award className="w-3.5 h-3.5 mr-1" /> Submit Review
              </Button>
            </Link>
          </div>

          {project.reviews.length === 0 ? (
            <Card className="bg-slate-900/40 border-dashed border-slate-800 p-8 text-center">
              <p className="text-sm text-slate-400">
                This project has not yet received a structured faculty or mentor rubric evaluation.
              </p>
            </Card>
          ) : (
            <div className="space-y-4">
              {project.reviews.map((r) => (
                <Card key={r.id} className="bg-slate-900/60 border-slate-800">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-base font-bold text-slate-200 flex items-center gap-2">
                          <span>{r.reviewer_name || "Faculty Reviewer"}</span>
                          <Badge
                            className={
                              r.decision === "approved"
                                ? "bg-emerald-950 text-emerald-300 border-emerald-800 text-xs"
                                : "bg-rose-950 text-rose-300 border-rose-800 text-xs"
                            }
                          >
                            {r.decision}
                          </Badge>
                        </CardTitle>
                        <CardDescription className="text-xs text-slate-500 font-mono mt-0.5">
                          Evaluated on {new Date(r.reviewed_at).toLocaleDateString()}
                        </CardDescription>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-indigo-300">{r.overall_score}/100</div>
                        <div className="text-[10px] font-mono text-slate-500">10-Criteria Average</div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {r.feedback && (
                      <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300 italic">
                        &quot;{r.feedback}&quot;
                      </div>
                    )}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 pt-2 text-[11px] font-mono text-slate-400">
                      <div>Tech Depth: <strong className="text-slate-200">{r.technical_depth}</strong></div>
                      <div>Problem Solving: <strong className="text-slate-200">{r.problem_solving}</strong></div>
                      <div>Code Quality: <strong className="text-slate-200">{r.code_quality}</strong></div>
                      <div>Architecture: <strong className="text-slate-200">{r.architecture_quality}</strong></div>
                      <div>Documentation: <strong className="text-slate-200">{r.documentation_quality}</strong></div>
                      <div>Testing: <strong className="text-slate-200">{r.testing_quality}</strong></div>
                      <div>Application: <strong className="text-slate-200">{r.practical_application}</strong></div>
                      <div>Originality: <strong className="text-slate-200">{r.originality}</strong></div>
                      <div>Contribution: <strong className="text-slate-200">{r.student_contribution_score}</strong></div>
                      <div>Presentation: <strong className="text-slate-200">{r.professional_presentation}</strong></div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
