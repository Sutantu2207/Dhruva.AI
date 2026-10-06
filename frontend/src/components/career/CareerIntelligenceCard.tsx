"use client";

import * as React from "react";
import Link from "next/link";
import {
  Compass,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowDown,
  Layers,
  Sparkles,
  BookOpen,
  FileCheck2,
  RefreshCw,
  Info,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { fetchMyCareerIntelligence, triggerRecomputeSkills, triggerRecomputeCareer } from "@/lib/api";
import type { CareerIntelligenceOverview, StudentCareerGoal, StudentSkill } from "@/lib/types";

interface CareerIntelligenceCardProps {
  careerGoals?: StudentCareerGoal[];
  skills?: StudentSkill[];
  initialData?: CareerIntelligenceOverview | null;
}

export function CareerIntelligenceCard({
  initialData = null,
}: CareerIntelligenceCardProps) {
  const [data, setData] = React.useState<CareerIntelligenceOverview | null>(initialData);
  const [loading, setLoading] = React.useState<boolean>(!initialData);
  const [refreshing, setRefreshing] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadData = React.useCallback(async () => {
    try {
      const res = await fetchMyCareerIntelligence();
      setData(res);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load career intelligence";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    if (initialData) return;
    let ignore = false;
    async function fetchInitial() {
      try {
        const res = await fetchMyCareerIntelligence();
        if (!ignore) {
          setData(res);
          setError(null);
        }
      } catch (err: unknown) {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : "Failed to load career intelligence";
          setError(msg);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }
    fetchInitial();
    return () => {
      ignore = true;
    };
  }, [initialData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await triggerRecomputeSkills();
      if (data?.career?.id) {
        await triggerRecomputeCareer(data.career.id);
      }
      await loadData();
    } catch {
      await loadData();
    }
  };

  if (loading) {
    return (
      <Card className="border-indigo-100 bg-white dark:border-indigo-900/40 dark:bg-slate-900 shadow-md p-8 text-center">
        <div className="flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="h-6 w-6 animate-spin text-indigo-600" />
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
            Evaluating skill evidence &amp; career readiness...
          </p>
        </div>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card className="border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 shadow-md p-6">
        <div className="flex items-center space-x-3 text-amber-600 dark:text-amber-400">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div className="text-xs">
            <p className="font-semibold">Career Intelligence Status</p>
            <p className="text-slate-500">{error || "No intelligence data available yet."}</p>
          </div>
        </div>
      </Card>
    );
  }

  const targetCareer = data.career ? data.career.title : "No Career Goal Set";
  const readiness = data.readiness;
  const readinessScore = readiness ? Math.round(readiness.readiness_score * 100) : null;
  const confidenceScore = readiness ? Math.round(readiness.confidence * 100) : null;
  const strengths = data.strengths || [];
  const developing = data.developing || [];
  const gaps = data.gaps || [];
  const trajectory = data.trajectory || [];
  const placement = data.placement;

  return (
    <Card className="border-indigo-100 bg-gradient-to-b from-white via-indigo-50/20 to-white dark:border-indigo-900/40 dark:from-slate-900 dark:via-indigo-950/10 dark:to-slate-900 shadow-md">
      <CardHeader className="border-b border-slate-100 dark:border-slate-800 pb-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-xs">
              <Compass className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <CardTitle className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                  Career Intelligence &amp; Trajectory
                </CardTitle>
                <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-wider text-indigo-700 border-indigo-300 dark:text-indigo-300 dark:border-indigo-800">
                  Domain 7 Real Deterministic Engine
                </Badge>
              </div>
              <CardDescription className="text-xs">
                Derived directly from verified skill evidence, concept mastery states, and canonical career catalogs.
              </CardDescription>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="h-8 text-xs font-medium text-slate-600 dark:text-slate-300"
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1 ${refreshing ? "animate-spin" : ""}`} />
              Re-evaluate
            </Button>
            <span className="text-xs font-medium text-slate-500">Target Role:</span>
            <Badge variant="default" className="bg-indigo-600 text-white font-semibold text-xs py-1 px-2.5">
              {targetCareer}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-6 space-y-7">
        {!data.has_career_goal ? (
          <div className="rounded-xl border border-dashed border-indigo-200 bg-indigo-50/30 p-6 text-center dark:border-indigo-900/50 dark:bg-indigo-950/20">
            <Info className="h-6 w-6 text-indigo-600 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              No Career Goal Selected
            </h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
              Select a target career to evaluate your skill profile against national curriculum standards and benchmark requirements.
            </p>
            <Link href="/career">
              <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs">
                Explore Career Catalog
              </Button>
            </Link>
          </div>
        ) : !readiness ? (
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <p className="text-xs text-slate-500">
              Readiness cannot yet be assessed. Canonical requirements for {targetCareer} require catalog skill mapping.
            </p>
          </div>
        ) : (
          <>
            {/* Career Readiness Meter */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900/80">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                      Authoritative Career Readiness
                    </h4>
                    {confidenceScore !== null && (
                      <Badge variant="secondary" className="text-[10px] font-mono">
                        {confidenceScore}% Evidence Confidence
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Evaluated against {targetCareer} specifications using deterministic evidence aggregation.
                  </p>
                </div>
                <div className="flex items-baseline space-x-1.5">
                  <span className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">
                    {readinessScore !== null ? `${readinessScore}%` : "Not Assessed"}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">/ 100%</span>
                </div>
              </div>

              {/* Progress Bar & Breakdown */}
              <div className="space-y-3">
                <Progress value={readinessScore ?? 0} className="h-3 bg-slate-100 dark:bg-slate-800" />
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px]">
                  <div>
                    <span className="text-slate-400 block">Required Coverage</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {Math.round(readiness.required_skill_coverage * 100)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Critical Coverage</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {Math.round(readiness.critical_skill_coverage * 100)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Preferred Coverage</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {Math.round(readiness.preferred_skill_coverage * 100)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Critical Gaps</span>
                    <span className={`font-semibold ${readiness.critical_gaps_count > 0 ? "text-rose-600 font-bold" : "text-emerald-600"}`}>
                      {readiness.critical_gaps_count} Blocking
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 3-Column Skills & Gaps Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Strong Skills */}
              <div className="rounded-lg border border-emerald-200 bg-emerald-50/40 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/20 flex flex-col justify-between">
                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                    <h5 className="font-bold text-xs uppercase tracking-wider text-emerald-900 dark:text-emerald-200">
                      Strong Skills ({strengths.length})
                    </h5>
                  </div>
                  {strengths.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No skills currently verified at proficient or advanced tier.</p>
                  ) : (
                    <ul className="space-y-2 text-xs">
                      {strengths.slice(0, 5).map((s) => (
                        <li key={s.skill_id} className="flex items-center justify-between">
                          <div className="flex items-center space-x-1.5 font-semibold text-slate-900 dark:text-slate-100">
                            <span className="text-emerald-600">✓</span>
                            <span>{s.skill_name}</span>
                          </div>
                          <Badge variant="outline" className="text-[10px] bg-white/70 dark:bg-slate-900/70 border-emerald-200 text-emerald-800 dark:text-emerald-300 font-normal uppercase">
                            {s.verification_status}
                          </Badge>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="mt-4 pt-2 border-t border-emerald-200/50 dark:border-emerald-900/50 text-[11px] text-emerald-800 dark:text-emerald-300">
                  Verified by multi-source assessment and project evidence.
                </div>
              </div>

              {/* Developing Skills */}
              <div className="rounded-lg border border-amber-200 bg-amber-50/40 p-4 dark:border-amber-900/40 dark:bg-amber-950/20 flex flex-col justify-between">
                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="h-4 w-4 rounded-full border-2 border-amber-500 border-r-transparent flex items-center justify-center text-[10px] font-bold text-amber-600">
                      ◐
                    </div>
                    <h5 className="font-bold text-xs uppercase tracking-wider text-amber-900 dark:text-amber-200">
                      Developing ({developing.length})
                    </h5>
                  </div>
                  {developing.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No skills in active developing tier.</p>
                  ) : (
                    <ul className="space-y-2.5 text-xs">
                      {developing.slice(0, 5).map((s) => {
                        const pct = Math.round(s.observed_proficiency * 100);
                        return (
                          <li key={s.skill_id} className="space-y-1">
                            <div className="flex items-center justify-between font-semibold text-slate-900 dark:text-slate-100">
                              <div className="flex items-center space-x-1.5">
                                <span className="text-amber-500 font-bold">◐</span>
                                <span>{s.skill_name}</span>
                              </div>
                              <span className="text-[11px] font-mono text-amber-700 dark:text-amber-400">{pct}%</span>
                            </div>
                            <Progress value={pct} className="h-1.5 bg-amber-100 dark:bg-amber-950" />
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
                <div className="mt-4 pt-2 border-t border-amber-200/50 dark:border-amber-900/50 text-[11px] text-amber-800 dark:text-amber-300">
                  Demonstrated in coursework or initial assessments.
                </div>
              </div>

              {/* Critical Gaps */}
              <div className="rounded-lg border border-rose-200 bg-rose-50/40 p-4 dark:border-rose-900/40 dark:bg-rose-950/20 flex flex-col justify-between">
                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <AlertCircle className="h-4 w-4 text-rose-600 dark:text-rose-400" />
                    <h5 className="font-bold text-xs uppercase tracking-wider text-rose-900 dark:text-rose-200">
                      Skill Gaps ({gaps.length})
                    </h5>
                  </div>
                  {gaps.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No significant gaps detected for target career requirements.</p>
                  ) : (
                    <ul className="space-y-2 text-xs">
                      {gaps.slice(0, 4).map((g) => (
                        <li key={g.skill_id} className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center space-x-1.5 font-semibold text-slate-900 dark:text-slate-100">
                              <span className="text-rose-600 font-bold">🔴</span>
                              <span>{g.skill_name}</span>
                            </div>
                            <p className="text-[10px] text-slate-500 pl-4">{g.reason}</p>
                          </div>
                          <Badge
                            variant={g.severity === "critical" ? "destructive" : "secondary"}
                            className="text-[9px] uppercase font-mono px-1 py-0 shrink-0 ml-1"
                          >
                            {g.severity}
                          </Badge>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="mt-4 pt-2 border-t border-rose-200/50 dark:border-rose-900/50 text-[11px] text-rose-800 dark:text-rose-300">
                  Deterministic gaps computed against career benchmark thresholds.
                </div>
              </div>
            </div>

            {/* Recommended Trajectory Path */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-5 dark:border-slate-800 dark:bg-slate-900/50">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    Recommended Trajectory Path
                  </h4>
                  <p className="text-xs text-slate-500">
                    Deterministic stepping stones addressing critical gaps first with prerequisite checks.
                  </p>
                </div>
                <Link href="/career/trajectory">
                  <Button variant="ghost" size="sm" className="text-xs text-indigo-600 font-semibold flex items-center space-x-1">
                    <span>Full Trajectory</span>
                    <ArrowRight className="h-3 w-3" />
                  </Button>
                </Link>
              </div>

              {trajectory.length === 0 ? (
                <div className="p-4 bg-white dark:bg-slate-900 rounded-lg text-xs text-slate-500 text-center border border-slate-200 dark:border-slate-800">
                  No mapped learning content available yet for target gaps.
                </div>
              ) : (
                <>
                  {/* Stepper Flow */}
                  <div className="hidden lg:flex items-center justify-between gap-2">
                    {trajectory.slice(0, 5).map((step, idx) => {
                      const Icon =
                        step.step_type === "concept_mastery"
                          ? BookOpen
                          : step.step_type === "lesson_learning"
                          ? Layers
                          : step.step_type === "skill_assessment"
                          ? FileCheck2
                          : Sparkles;
                      return (
                        <React.Fragment key={step.id}>
                          <div className="flex-1 rounded-lg border border-slate-200 bg-white p-3 shadow-2xs dark:border-slate-800 dark:bg-slate-900">
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-[10px] font-mono font-bold text-indigo-600 dark:text-indigo-400">
                                STEP 0{step.step_order}
                              </span>
                              <Icon className="h-3.5 w-3.5 text-slate-400" />
                            </div>
                            <div className="font-bold text-xs text-slate-900 dark:text-slate-100 truncate" title={step.title}>
                              {step.title}
                            </div>
                            <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
                              <span className="uppercase font-mono">{step.status}</span>
                              <Badge variant="outline" className="text-[9px] px-1 py-0">
                                {step.priority}
                              </Badge>
                            </div>
                          </div>
                          {idx < Math.min(trajectory.length, 5) - 1 && (
                            <div className="text-slate-300 dark:text-slate-700 font-bold px-1">
                              →
                            </div>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>

                  {/* Mobile Vertical Flow */}
                  <div className="flex lg:hidden flex-col space-y-2">
                    {trajectory.slice(0, 4).map((step, idx) => (
                      <React.Fragment key={step.id}>
                        <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs flex items-center justify-between shadow-2xs dark:border-slate-800 dark:bg-slate-900">
                          <div>
                            <span className="text-[10px] font-mono font-bold text-indigo-600">STEP 0{step.step_order}: </span>
                            <span className="font-bold text-slate-900 dark:text-slate-100">{step.title}</span>
                            <p className="text-[10px] text-slate-400 capitalize">{step.status} • {step.step_type}</p>
                          </div>
                          <Badge variant="outline" className="text-[9px]">
                            {step.priority}
                          </Badge>
                        </div>
                        {idx < Math.min(trajectory.length, 4) - 1 && (
                          <div className="flex justify-center text-slate-300 dark:text-slate-700">
                            <ArrowDown className="h-3 w-3" />
                          </div>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Placement Readiness Strip */}
            {placement && (
              <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                        Placement Preparedness Status
                      </h4>
                      <Badge variant="outline" className="font-mono text-[10px] capitalize">
                        {placement.overall_status.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {placement.assessed_components_count} of {placement.total_components_count} readiness components verified.
                    </p>
                  </div>
                  <div className="flex items-center space-x-3 text-xs font-mono">
                    <span className="text-slate-500">
                      Technical: {typeof placement.technical_readiness === "number" ? `${Math.round(placement.technical_readiness * 100)}%` : "Not Assessed"}
                    </span>
                    <span className="text-slate-500">
                      Projects: {typeof placement.project_evidence === "number" ? `${Math.round(placement.project_evidence * 100)}%` : "Not Assessed"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
