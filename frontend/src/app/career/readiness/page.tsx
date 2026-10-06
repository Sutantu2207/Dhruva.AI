"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, BarChart3, Briefcase, AlertTriangle, ShieldCheck, RefreshCw, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { fetchMyCareerReadiness, fetchMyPlacementReadiness, triggerRecomputeCareer } from "@/lib/api";
import type { StudentCareerReadiness, PlacementReadiness } from "@/lib/types";

export default function CareerReadinessPage() {
  const [readiness, setReadiness] = React.useState<StudentCareerReadiness | null>(null);
  const [placement, setPlacement] = React.useState<PlacementReadiness | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadData = React.useCallback(async () => {
    try {
      const [r, p] = await Promise.all([
        fetchMyCareerReadiness().catch(() => null),
        fetchMyPlacementReadiness().catch(() => null),
      ]);
      setReadiness(r);
      setPlacement(p);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load readiness data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    let ignore = false;
    async function fetchInitial() {
      try {
        const [r, p] = await Promise.all([
          fetchMyCareerReadiness().catch(() => null),
          fetchMyPlacementReadiness().catch(() => null),
        ]);
        if (!ignore) {
          setReadiness(r);
          setPlacement(p);
          setError(null);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load readiness data");
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
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      if (readiness?.career_id) {
        await triggerRecomputeCareer(readiness.career_id);
      }
      await loadData();
    } catch {
      await loadData();
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-5xl text-center space-y-4">
        <RefreshCw className="h-6 w-6 animate-spin text-indigo-600 mx-auto" />
        <p className="text-xs text-slate-500">Computing authoritative readiness metrics...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl space-y-6">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Link href="/career">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Career Intelligence
          </Button>
        </Link>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshing}
          className="text-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 mr-1 ${refreshing ? "animate-spin" : ""}`} />
          Recalculate Readiness
        </Button>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-indigo-600" />
          Authoritative Career &amp; Placement Readiness
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Deterministic readiness evaluation. Dhruva.AI never fabricates hiring probabilities or job market percentages.
        </p>
      </div>

      {error ? (
        <Card className="p-6 text-center text-rose-600 bg-white dark:bg-slate-900">
          <p className="text-xs">{error}</p>
        </Card>
      ) : !readiness ? (
        <Card className="p-8 text-center bg-white dark:bg-slate-900">
          <Info className="h-8 w-8 text-indigo-600 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            No Career Goal Evaluated
          </h4>
          <p className="text-xs text-slate-500 mt-1 mb-4">
            Select a target career in the career catalog to evaluate readiness and skill gaps.
          </p>
          <Link href="/career">
            <Button size="sm" className="bg-indigo-600 text-white text-xs">
              Go to Career Overview
            </Button>
          </Link>
        </Card>
      ) : (
        <>
          {/* Target Role Readiness Card */}
          <Card className="bg-white dark:bg-slate-900 border-indigo-100 dark:border-indigo-900/40">
            <CardHeader className="pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <Badge variant="outline" className="text-[10px] font-mono uppercase mb-1">
                    Target Role
                  </Badge>
                  <CardTitle className="text-xl font-bold text-slate-900 dark:text-slate-100">
                    {readiness.career_title}
                  </CardTitle>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-4xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">
                    {Math.round(readiness.readiness_score * 100)}%
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Readiness</span>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              <Progress value={Math.round(readiness.readiness_score * 100)} className="h-3 bg-slate-100 dark:bg-slate-800" />

              {/* Explainability Breakdown */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-5 dark:border-slate-800 dark:bg-slate-800/40 space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-indigo-600" />
                  Deterministic Explainability Breakdown
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-slate-500 block">Required Skill Coverage</span>
                    <span className="text-lg font-bold text-slate-900 dark:text-slate-100 font-mono">
                      {Math.round(readiness.required_skill_coverage * 100)}%
                    </span>
                    <p className="text-[10px] text-slate-400 mt-1">Weighted verified proficiency in core required skills</p>
                  </div>

                  <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-slate-500 block">Critical Skill Coverage</span>
                    <span className="text-lg font-bold text-slate-900 dark:text-slate-100 font-mono">
                      {Math.round(readiness.critical_skill_coverage * 100)}%
                    </span>
                    <p className="text-[10px] text-slate-400 mt-1">Proportion of mandatory threshold skills met</p>
                  </div>

                  <div className="p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-slate-500 block">Preferred Skill Coverage</span>
                    <span className="text-lg font-bold text-slate-900 dark:text-slate-100 font-mono">
                      {Math.round(readiness.preferred_skill_coverage * 100)}%
                    </span>
                    <p className="text-[10px] text-slate-400 mt-1">Competence in supplementary elective technologies</p>
                  </div>
                </div>

                {readiness.critical_gaps_count > 0 && (
                  <div className="flex items-center gap-2 p-3 bg-rose-50 text-rose-800 rounded-lg text-xs dark:bg-rose-950/30 dark:text-rose-300">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span>
                      <strong>{readiness.critical_gaps_count} critical skill(s)</strong> are currently below minimum career proficiency thresholds.
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Placement Preparedness Framework Card */}
          <Card className="bg-white dark:bg-slate-900">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <Briefcase className="h-5 w-5 text-indigo-600" />
                    Institutional Placement Preparedness Framework
                  </CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    Multi-dimensional employability readiness. Status is strictly evidence-backed.
                  </CardDescription>
                </div>
                {placement && (
                  <Badge variant="outline" className="font-mono text-xs uppercase">
                    Status: {placement.overall_status.replace(/_/g, " ")}
                  </Badge>
                )}
              </div>
            </CardHeader>

            <CardContent>
              {placement ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-xs text-slate-500 block">Technical Readiness</span>
                    <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                      {typeof placement.technical_readiness === "number" ? `${Math.round(placement.technical_readiness * 100)}%` : "Not Assessed"}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-xs text-slate-500 block">Assessment Readiness</span>
                    <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                      {typeof placement.assessment_readiness === "number" ? `${Math.round(placement.assessment_readiness * 100)}%` : "Not Assessed"}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-xs text-slate-500 block">Project Evidence</span>
                    <div className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
                      {typeof placement.project_evidence === "number" ? `${Math.round(placement.project_evidence * 100)}%` : "Not Assessed"}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-xs text-slate-500 block">Communication Readiness</span>
                    <div className="text-sm font-semibold font-mono text-slate-400 mt-2">
                      {typeof placement.communication_readiness === "number" ? `${Math.round(placement.communication_readiness * 100)}%` : "Not Assessed"}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-xs text-slate-500 block">Resume Readiness</span>
                    <div className="text-sm font-semibold font-mono text-slate-400 mt-2">
                      {typeof placement.resume_readiness === "number" ? `${Math.round(placement.resume_readiness * 100)}%` : "Not Assessed"}
                    </div>
                  </div>

                  <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                    <span className="text-xs text-slate-500 block">Interview Readiness</span>
                    <div className="text-sm font-semibold font-mono text-slate-400 mt-2">
                      {typeof placement.interview_readiness === "number" ? `${Math.round(placement.interview_readiness * 100)}%` : "Not Assessed"}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No placement readiness state generated yet.</p>
              )}

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500">
                Ethical Product Standard: Unassessed placement competencies are honestly rendered as &quot;Not Assessed&quot; rather than synthetic mock numbers.
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
