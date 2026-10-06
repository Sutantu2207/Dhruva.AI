"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, AlertCircle, CheckCircle2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { triggerRecomputeCareer } from "@/lib/api";
import type { StudentCareerReadiness } from "@/lib/types";

export default function CareerDetailPage() {
  const params = useParams();
  const careerId = params.id as string;

  const [readiness, setReadiness] = React.useState<StudentCareerReadiness | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let ignore = false;
    async function fetchCareerReadiness() {
      try {
        const data = await triggerRecomputeCareer(careerId);
        if (!ignore) {
          setReadiness(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load career requirements");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    fetchCareerReadiness();
    return () => {
      ignore = true;
    };
  }, [careerId]);

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-5xl text-center space-y-4">
        <RefreshCw className="h-6 w-6 animate-spin text-indigo-600 mx-auto" />
        <p className="text-xs text-slate-500">Evaluating career readiness against canonical catalog requirements...</p>
      </div>
    );
  }

  if (error || !readiness) {
    return (
      <div className="container mx-auto p-6 max-w-5xl space-y-4">
        <Link href="/career">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Career Intelligence
          </Button>
        </Link>
        <Card className="p-6 text-center text-rose-600 bg-white dark:bg-slate-900">
          <p className="text-xs">{error || "Career not found or insufficient catalog data"}</p>
        </Card>
      </div>
    );
  }

  const scorePct = Math.round(readiness.readiness_score * 100);
  const confidencePct = Math.round(readiness.confidence * 100);

  return (
    <div className="container mx-auto p-6 max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/career">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Career Overview
          </Button>
        </Link>
        <Badge variant="outline" className="font-mono text-xs uppercase">
          Engine {readiness.algorithm_version}
        </Badge>
      </div>

      <Card className="bg-white dark:bg-slate-900 border-indigo-100 dark:border-indigo-900/40">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <CardTitle className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {readiness.career_title}
              </CardTitle>
              <CardDescription className="text-xs mt-1">
                Deterministic readiness evaluation based on canonical career skill mappings.
              </CardDescription>
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono">
                {scorePct}%
              </span>
              <span className="text-xs text-slate-400 font-mono">Readiness</span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-xs">
            <div>
              <span className="text-slate-400 block">Required Coverage</span>
              <span className="font-bold text-slate-800 dark:text-slate-200 text-sm">
                {Math.round(readiness.required_skill_coverage * 100)}%
              </span>
            </div>
            <div>
              <span className="text-slate-400 block">Critical Coverage</span>
              <span className="font-bold text-slate-800 dark:text-slate-200 text-sm">
                {Math.round(readiness.critical_skill_coverage * 100)}%
              </span>
            </div>
            <div>
              <span className="text-slate-400 block">Preferred Coverage</span>
              <span className="font-bold text-slate-800 dark:text-slate-200 text-sm">
                {Math.round(readiness.preferred_skill_coverage * 100)}%
              </span>
            </div>
            <div>
              <span className="text-slate-400 block">Evidence Confidence</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400 text-sm">
                {confidencePct}%
              </span>
            </div>
          </div>

          {/* Gaps Section */}
          <div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-rose-600" />
              Skill Gaps ({readiness.gaps.length})
            </h4>
            {readiness.gaps.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No significant gaps detected for this career.</p>
            ) : (
              <div className="space-y-2">
                {readiness.gaps.map((g) => (
                  <div
                    key={g.skill_id}
                    className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                        <span className="text-rose-600">🔴</span>
                        <span>{g.skill_name}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 pl-4 mt-0.5">{g.reason}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-slate-400 text-[11px]">
                        Delta: {Math.round(g.gap_size * 100)}%
                      </span>
                      <Badge variant={g.severity === "critical" ? "destructive" : "secondary"} className="uppercase text-[9px]">
                        {g.severity}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Strengths Section */}
          <div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              Strengths ({readiness.strengths.length})
            </h4>
            {readiness.strengths.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No verified skills at proficient or advanced level for this career yet.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {readiness.strengths.map((s) => (
                  <div
                    key={s.skill_id}
                    className="p-3 rounded-lg border border-emerald-100 bg-emerald-50/20 dark:border-emerald-900/30 dark:bg-emerald-950/10 flex items-center justify-between"
                  >
                    <span className="font-semibold text-slate-900 dark:text-slate-100">{s.skill_name}</span>
                    <Badge variant="outline" className="border-emerald-200 text-emerald-700 dark:text-emerald-300 capitalize text-[10px]">
                      {s.proficiency_tier}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
