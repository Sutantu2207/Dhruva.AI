"use client";

import * as React from "react";
import Link from "next/link";
import {
  Network,
  ShieldCheck,
  Award,
  Layers,
  FolderGit2,
  FileCheck2,
  Briefcase,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Info,
  Clock,
  Compass,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  fetchMySkillGraph,
  fetchSkillEvidenceGraph,
  fetchProjectsStrengtheningGaps,
  fetchProjectsWithInsufficientEvidence,
} from "@/lib/api";
import type {
  StudentSkillGraphData,
  SkillEvidenceGraphData,
  ProjectGapStrengtheningItem,
  ProjectInsufficientEvidenceItem,
} from "@/lib/types";

export default function SkillGraphPage() {
  const [skillGraph, setSkillGraph] = React.useState<StudentSkillGraphData | null>(null);
  const [selectedSkillId, setSelectedSkillId] = React.useState<string | null>(null);
  const [skillEvidence, setSkillEvidence] = React.useState<SkillEvidenceGraphData | null>(null);
  const [gapProjects, setGapProjects] = React.useState<ProjectGapStrengtheningItem[]>([]);
  const [insufficientProjects, setInsufficientProjects] = React.useState<ProjectInsufficientEvidenceItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [evidenceLoading, setEvidenceLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadSkillDetail = React.useCallback(async (skillId: string) => {
    try {
      setEvidenceLoading(true);
      const data = await fetchSkillEvidenceGraph(skillId);
      setSkillEvidence(data);
    } catch {
      // Non-fatal if detail fails
    } finally {
      setEvidenceLoading(false);
    }
  }, []);

  React.useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        const [graphData, gaps, insufficient] = await Promise.all([
          fetchMySkillGraph(),
          fetchProjectsStrengtheningGaps().catch(() => []),
          fetchProjectsWithInsufficientEvidence().catch(() => []),
        ]);
        setSkillGraph(graphData);
        setGapProjects(gaps);
        setInsufficientProjects(insufficient);

        if (graphData.skills.length > 0) {
          const firstSkill = graphData.skills[0];
          setSelectedSkillId(firstSkill.skill_id);
          void loadSkillDetail(firstSkill.skill_id);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load skill graph");
      } finally {
        setLoading(false);
      }
    }
    void loadInitialData();
  }, [loadSkillDetail]);

  const handleSelectSkill = (skillId: string) => {
    setSelectedSkillId(skillId);
    loadSkillDetail(skillId);
  };

  if (loading) {
    return (
      <div className="container max-w-7xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
          <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-1/2"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="h-96 bg-slate-200 dark:bg-slate-800 rounded"></div>
            <div className="lg:col-span-2 h-96 bg-slate-200 dark:bg-slate-800 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !skillGraph) {
    return (
      <div className="container max-w-7xl mx-auto px-4 py-8">
        <Card className="border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/20">
          <CardContent className="pt-6 text-center text-red-600 dark:text-red-400">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
            <p className="font-semibold">{error || "Skill graph unavailable"}</p>
            <p className="text-sm mt-1">Please ensure your student profile and academic track are active.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Network className="h-5 w-5" />
            </span>
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
              Domain 8 Evidence Engine
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Skill & Evidence Graph
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Multi-dimensional deterministic provenance connecting what you learned, practiced, built, and verified.
          </p>
        </div>

        {skillGraph.primary_career && (
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <Briefcase className="h-5 w-5 text-indigo-600 dark:text-indigo-400 shrink-0" />
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Target Career Track</p>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {skillGraph.primary_career.title}
              </p>
            </div>
            <Link href="/career">
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        )}
      </div>

      {/* Top Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-slate-50/50 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Skills Evaluated</p>
                <p className="text-2xl font-bold mt-1 text-slate-900 dark:text-white">
                  {skillGraph.total_evaluated_skills}
                </p>
              </div>
              <Award className="h-6 w-6 text-indigo-500 shrink-0" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-50/50 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Faculty/System Verified</p>
                <p className="text-2xl font-bold mt-1 text-emerald-600 dark:text-emerald-400">
                  {skillGraph.verified_skills_count}
                </p>
              </div>
              <ShieldCheck className="h-6 w-6 text-emerald-500 shrink-0" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-50/50 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Claimed / Observed Only</p>
                <p className="text-2xl font-bold mt-1 text-amber-600 dark:text-amber-400">
                  {skillGraph.unverified_skills_count}
                </p>
              </div>
              <Clock className="h-6 w-6 text-amber-500 shrink-0" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-50/50 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Projects Backing Skills</p>
                <p className="text-2xl font-bold mt-1 text-indigo-600 dark:text-indigo-400">
                  {skillGraph.skills.filter((s) => s.has_project_evidence).length}
                </p>
              </div>
              <FolderGit2 className="h-6 w-6 text-indigo-500 shrink-0" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Skill Selector / Catalog */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="border-slate-200 dark:border-slate-800 shadow-sm">
            <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
              <CardTitle className="text-base font-semibold flex items-center justify-between">
                <span>Evaluated Skills</span>
                <span className="text-xs text-slate-500 font-normal">Select to inspect provenance</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2 space-y-1.5 max-h-[640px] overflow-y-auto">
              {skillGraph.skills.length === 0 ? (
                <div className="p-6 text-center text-slate-500 text-sm">
                  No evaluated skills recorded yet. Complete assessments or add projects to populate your graph.
                </div>
              ) : (
                skillGraph.skills.map((s) => {
                  const isSelected = selectedSkillId === s.skill_id;
                  return (
                    <button
                      key={s.skill_id}
                      onClick={() => handleSelectSkill(s.skill_id)}
                      className={`w-full text-left p-3 rounded-lg transition-all border ${
                        isSelected
                          ? "bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-800 shadow-xs"
                          : "bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-sm text-slate-900 dark:text-white">
                              {s.name}
                            </span>
                            {s.is_career_required && (
                              <Badge variant="outline" className="text-[10px] py-0 px-1 border-indigo-200 text-indigo-600 dark:text-indigo-400">
                                Career Core
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 dark:text-slate-400 capitalize mt-0.5">
                            {s.category || "General"} · {s.tier || "foundation"}
                          </p>
                        </div>
                        <Badge
                          variant={s.verification_status === "verified" ? "default" : "secondary"}
                          className={`text-[10px] shrink-0 ${
                            s.verification_status === "verified"
                              ? "bg-emerald-600 hover:bg-emerald-600 text-white"
                              : "bg-amber-100 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400"
                          }`}
                        >
                          {s.verification_status === "verified" ? "Verified" : "Claimed/Observed"}
                        </Badge>
                      </div>

                      <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                        <span>Proficiency: {Math.round(s.observed_proficiency * 100)}%</span>
                        <span>{s.projects_count} project{s.projects_count !== 1 ? "s" : ""}</span>
                      </div>
                      <Progress
                        value={s.observed_proficiency * 100}
                        className="h-1.5 mt-1.5"
                      />
                    </button>
                  );
                })
              )}
            </CardContent>
          </Card>

          {/* Gap Strengthening Suggestions */}
          {gapProjects.length > 0 && (
            <Card className="border-indigo-200 dark:border-indigo-900 bg-indigo-50/30 dark:bg-indigo-950/20 shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2 text-indigo-900 dark:text-indigo-300">
                  <Sparkles className="h-4 w-4 text-indigo-600" />
                  Projects Strengthening Career Gaps
                </CardTitle>
                <CardDescription className="text-xs">
                  These existing projects contain skills critical to your target career.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-xs">
                {gapProjects.slice(0, 3).map((gp) => (
                  <div key={gp.project_id} className="p-2.5 rounded-md bg-white dark:bg-slate-900 border border-indigo-100 dark:border-indigo-950 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">{gp.title}</p>
                      <p className="text-[11px] text-indigo-600 dark:text-indigo-400 mt-0.5">
                        Matches {gp.matching_gap_skills?.length || 0} gap skills
                      </p>
                    </div>
                    <Link href={`/projects/${gp.project_id}`}>
                      <Button size="sm" variant="outline" className="h-7 text-xs">
                        View
                      </Button>
                    </Link>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Insufficient Evidence Alerts */}
          {insufficientProjects.length > 0 && (
            <Card className="border-amber-200 dark:border-amber-900 bg-amber-50/30 dark:bg-amber-950/20 shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2 text-amber-900 dark:text-amber-300">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  Projects Needing Evidence
                </CardTitle>
                <CardDescription className="text-xs">
                  Submit repositories, demos, or testing reports to verify claimed skills.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-xs">
                {insufficientProjects.slice(0, 3).map((ip) => (
                  <div key={ip.project_id} className="p-2.5 rounded-md bg-white dark:bg-slate-900 border border-amber-100 dark:border-amber-950 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">{ip.title}</p>
                      <p className="text-[11px] text-amber-600 dark:text-amber-400 mt-0.5">
                        0 verified evidence items
                      </p>
                    </div>
                    <Link href={`/projects/${ip.project_id}/evidence`}>
                      <Button size="sm" variant="outline" className="h-7 text-xs border-amber-300 text-amber-700">
                        Add Evidence
                      </Button>
                    </Link>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column: Deep Evidence Provenance Graph */}
        <div className="lg:col-span-7 space-y-6">
          {evidenceLoading ? (
            <div className="h-96 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse flex items-center justify-center text-slate-400">
              Traversing skill provenance graph...
            </div>
          ) : skillEvidence ? (
            <div className="space-y-6">
              {/* Provenance Card */}
              <Card className="border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
                <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 text-white">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs uppercase tracking-wider font-semibold text-indigo-300">
                          Deterministic Provenance
                        </span>
                        <Badge variant="outline" className="border-indigo-400 text-indigo-200 text-xs">
                          {skillEvidence.category || "Skill Node"}
                        </Badge>
                      </div>
                      <h2 className="text-2xl font-bold mt-1 text-white">
                        {skillEvidence.skill_name}
                      </h2>
                      <p className="text-xs text-indigo-200/80 mt-1">
                        Code: {skillEvidence.skill_code || "N/A"}
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="text-xs text-slate-300">Confidence</div>
                      <div className="text-2xl font-extrabold text-indigo-300">
                        {Math.round((skillEvidence.state.confidence || 0) * 100)}%
                      </div>
                    </div>
                  </div>

                  {/* Graph Traversal Blueprint */}
                  <div className="mt-6 pt-6 border-t border-indigo-800/40 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                    <div className="p-2.5 rounded-lg bg-indigo-900/30 border border-indigo-700/30">
                      <div className="text-xs text-indigo-300">Mastered Concepts</div>
                      <div className="text-lg font-bold mt-0.5">{skillEvidence.provenance_summary.mastered_concepts_count}</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-indigo-900/30 border border-indigo-700/30">
                      <div className="text-xs text-indigo-300">Courses</div>
                      <div className="text-lg font-bold mt-0.5">{skillEvidence.provenance_summary.courses_count}</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-indigo-900/30 border border-indigo-700/30">
                      <div className="text-xs text-indigo-300">Assessments</div>
                      <div className="text-lg font-bold mt-0.5">{skillEvidence.provenance_summary.assessments_count}</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-indigo-900/30 border border-indigo-700/30">
                      <div className="text-xs text-indigo-300">Projects</div>
                      <div className="text-lg font-bold mt-0.5">{skillEvidence.provenance_summary.projects_count}</div>
                    </div>
                  </div>
                </div>

                <CardContent className="p-6 space-y-6">
                  {/* "Why does Dhruva think this student has this skill?" */}
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                      <Info className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                      Verification Graph Explanation
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                      Proficiency in <strong className="text-slate-900 dark:text-white">{skillEvidence.skill_name}</strong> is deterministically derived from{" "}
                      <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                        {skillEvidence.provenance_summary.mastered_concepts_count} mastered concepts
                      </span>
                      , <span className="font-semibold text-indigo-600 dark:text-indigo-400">{skillEvidence.provenance_summary.courses_count} formal academic courses</span>,{" "}
                      <span className="font-semibold text-indigo-600 dark:text-indigo-400">{skillEvidence.provenance_summary.assessments_count} proctored assessments</span>, and{" "}
                      <span className="font-semibold text-indigo-600 dark:text-indigo-400">{skillEvidence.provenance_summary.projects_count} applied engineering projects</span>{" "}
                      ({skillEvidence.provenance_summary.verified_projects_count} verified with {skillEvidence.provenance_summary.project_evidence_items_count} verified artifact submissions).
                    </p>
                  </div>

                  {/* Section 1: Connected Canonical Concepts */}
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5" />
                      Canonical Concepts ({skillEvidence.concepts.length})
                    </h4>
                    {skillEvidence.concepts.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">No concept mappings recorded.</p>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {skillEvidence.concepts.map((c) => (
                          <div
                            key={c.concept_id}
                            className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between text-xs"
                          >
                            <div>
                              <p className="font-medium text-slate-900 dark:text-white">{c.concept_name}</p>
                              <p className="text-[11px] text-slate-500 mt-0.5">
                                Mastery: {Math.round((c.mastery || 0) * 100)}% · {c.classification || "standard"}
                              </p>
                            </div>
                            {c.is_core && (
                              <Badge variant="outline" className="text-[10px] py-0 px-1 border-indigo-200 text-indigo-600">
                                Core
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Section 2: Projects Demonstrating This Skill */}
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                      <FolderGit2 className="h-3.5 w-3.5" />
                      Applied Engineering Projects ({skillEvidence.projects.length})
                    </h4>
                    {skillEvidence.projects.length === 0 ? (
                      <div className="p-4 rounded-lg border border-dashed border-slate-300 dark:border-slate-800 text-center">
                        <p className="text-xs text-slate-500">No projects currently associate with this skill.</p>
                        <Link href="/projects/new">
                          <Button size="sm" variant="outline" className="mt-2 text-xs">
                            Create Project
                          </Button>
                        </Link>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {skillEvidence.projects.map((p) => (
                          <div
                            key={p.project_id}
                            className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between"
                          >
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-sm text-slate-900 dark:text-white">
                                  {p.project_title}
                                </span>
                                <Badge
                                  variant={p.is_verified ? "default" : "outline"}
                                  className={`text-[10px] ${
                                    p.is_verified ? "bg-emerald-600 text-white" : "text-amber-600 border-amber-300"
                                  }`}
                                >
                                  {p.is_verified ? "Faculty Verified" : "Claimed/Observed"}
                                </Badge>
                              </div>
                              <p className="text-xs text-slate-500 mt-1 capitalize">
                                Type: {p.project_type} · Claimed: {p.claimed_level} · Strength: {Math.round(p.evidence_strength * 100)}%
                              </p>
                            </div>

                            <Link href={`/projects/${p.project_id}`}>
                              <Button variant="ghost" size="sm" className="h-8 text-xs">
                                Inspect
                              </Button>
                            </Link>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Section 3: Verified Artifact Submissions */}
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                      <FileCheck2 className="h-3.5 w-3.5" />
                      Verified Artifact Provenance ({skillEvidence.project_evidence.length})
                    </h4>
                    {skillEvidence.project_evidence.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">No granular artifacts submitted for verification yet.</p>
                    ) : (
                      <div className="space-y-2">
                        {skillEvidence.project_evidence.map((e) => (
                          <div
                            key={e.evidence_id}
                            className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 flex items-center justify-between text-xs"
                          >
                            <div className="space-y-0.5">
                              <p className="font-medium text-slate-900 dark:text-white">{e.title}</p>
                              <p className="text-slate-500 text-[11px] font-mono truncate max-w-md">
                                {e.evidence_type} · {e.source}: {e.source_reference}
                              </p>
                            </div>
                            <Badge
                              className={`text-[10px] ${
                                e.verification_status === "verified"
                                  ? "bg-emerald-600 text-white"
                                  : "bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                              }`}
                            >
                              {e.verification_status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Section 4: Target Career Demand */}
                  {skillEvidence.target_careers.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                        <Compass className="h-3.5 w-3.5" />
                        Target Career Demand
                      </h4>
                      <div className="space-y-1.5">
                        {skillEvidence.target_careers.map((tc) => (
                          <div
                            key={tc.career_id}
                            className="p-2.5 rounded-lg bg-indigo-50/40 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/50 flex items-center justify-between text-xs"
                          >
                            <span className="font-medium text-indigo-950 dark:text-indigo-200">
                              {tc.career_title}
                            </span>
                            <Badge variant="outline" className="text-[10px] border-indigo-200 text-indigo-700 dark:text-indigo-300 uppercase">
                              {tc.importance} importance
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-400">Select a skill to inspect provenance</div>
          )}
        </div>
      </div>
    </div>
  );
}
