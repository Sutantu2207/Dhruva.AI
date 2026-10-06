"use client";

import * as React from "react";
import Link from "next/link";
import {
  Clock,
  ArrowLeft,
  AlertTriangle,
  History,
  GitBranch,
  ShieldCheck,
  RotateCw,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { fetchMyConceptDetail } from "@/lib/api";
import type { ConceptDetail } from "@/lib/types";

interface ConceptDetailViewProps {
  conceptId: string;
}

export function ConceptDetailView({ conceptId }: ConceptDetailViewProps) {
  const [detail, setDetail] = React.useState<ConceptDetail | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let ignore = false;
    async function loadData() {
      try {
        const res = await fetchMyConceptDetail(conceptId);
        if (!ignore) {
          setDetail(res);
          setError(null);
        }
      } catch {
        if (!ignore) {
          setError("Concept knowledge record not found or access denied.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      ignore = true;
    };
  }, [conceptId]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <RotateCw className="h-8 w-8 animate-spin text-indigo-600" />
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
            Synthesizing concept knowledge state...
          </p>
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="space-y-4">
        <Link href="/knowledge">
          <Button variant="ghost" size="sm" className="flex items-center space-x-1">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Knowledge Dashboard</span>
          </Button>
        </Link>
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error || "Concept not found"}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const ks = detail.knowledge_state;
  const rs = detail.review_state;
  const masteryPct = ks?.current_mastery !== null && ks?.current_mastery !== undefined
    ? Math.round(ks.current_mastery * 100)
    : null;
  const confidencePct = ks ? Math.round(ks.confidence * 100) : 0;
  const retentionPct = ks ? Math.round(ks.retention_estimate * 100) : 0;
  const readinessPct = ks?.prerequisite_readiness !== null && ks?.prerequisite_readiness !== undefined
    ? Math.round(ks.prerequisite_readiness * 100)
    : null;

  return (
    <div className="space-y-8 pb-12">
      {/* Back button and title */}
      <div>
        <Link href="/knowledge">
          <Button variant="ghost" size="sm" className="mb-4 flex items-center space-x-1.5 text-slate-600">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Knowledge Dashboard</span>
          </Button>
        </Link>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-6 dark:border-slate-800">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                {detail.concept_name}
              </h1>
              <Badge variant="outline" className="font-mono text-xs uppercase">
                {detail.difficulty}
              </Badge>
              {ks && (
                <Badge
                  variant={
                    ks.state === "mastered"
                      ? "success"
                      : ks.state === "proficient"
                      ? "default"
                      : ks.state === "at_risk"
                      ? "destructive"
                      : ks.state === "developing"
                      ? "warning"
                      : "secondary"
                  }
                  className="uppercase text-xs font-mono"
                >
                  {ks.state.replace("_", " ")}
                </Badge>
              )}
            </div>
            <p className="mt-1 text-sm text-slate-500 font-mono">
              slug: {detail.concept_slug} • engine: {ks?.algorithm_version || "v1"}
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Link href="/review">
              <Button className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center space-x-2">
                <Clock className="h-4 w-4" />
                <span>Spaced Review</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Mastery */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-semibold">Mastery Estimate</CardDescription>
            <CardTitle className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              {masteryPct !== null ? `${masteryPct}%` : "Unknown"}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            {masteryPct !== null ? (
              <Progress value={masteryPct} className="h-2 mt-1" />
            ) : (
              <span className="text-xs text-slate-400">Insufficient evidence</span>
            )}
            <p className="text-[11px] text-slate-500 mt-2">
              Based on {ks?.evidence_count ?? 0} authoritative observations.
            </p>
          </CardContent>
        </Card>

        {/* Confidence */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-semibold">Confidence Metric</CardDescription>
            <CardTitle className="text-3xl font-bold text-slate-900 dark:text-slate-100">
              {confidencePct}%
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <Progress value={confidencePct} className="h-2 mt-1 bg-slate-100" />
            <p className="text-[11px] text-slate-500 mt-2">
              Statistical trust in estimate (penalizes variance and low sample size).
            </p>
          </CardContent>
        </Card>

        {/* Retention */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-semibold">Estimated Retention</CardDescription>
            <CardTitle className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
              {retentionPct}%
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <Progress value={retentionPct} className="h-2 mt-1" />
            <p className="text-[11px] text-slate-500 mt-2">
              Ebbinghaus decay curve based on elapsed review interval.
            </p>
          </CardContent>
        </Card>

        {/* Trend & Status */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-semibold">Mastery Trend</CardDescription>
            <CardTitle className="text-xl font-bold capitalize flex items-center space-x-2 text-slate-900 dark:text-slate-100">
              {ks?.trend === "strongly_improving" || ks?.trend === "improving" ? (
                <TrendingUp className="h-5 w-5 text-emerald-500" />
              ) : ks?.trend === "declining" || ks?.trend === "strongly_declining" ? (
                <TrendingDown className="h-5 w-5 text-rose-500" />
              ) : (
                <Minus className="h-5 w-5 text-slate-400" />
              )}
              <span>{ks?.trend ? ks.trend.replace("_", " ") : "N/A"}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="flex items-center space-x-2 text-xs text-slate-500 mt-2">
              <span>Next Review:</span>
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {rs ? new Date(rs.next_review_at).toLocaleDateString() : "Pending"}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Prerequisites Graph & Readiness */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <GitBranch className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              <CardTitle className="text-lg font-bold">Prerequisites & Readiness</CardTitle>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500">Prerequisite Health:</span>
              <Badge
                variant={
                  ks?.prerequisite_health === "healthy"
                    ? "success"
                    : ks?.prerequisite_health === "weak"
                    ? "destructive"
                    : "secondary"
                }
                className="uppercase text-xs"
              >
                {ks?.prerequisite_health || "Unknown"}
              </Badge>
              {readinessPct !== null && (
                <Badge variant="outline" className="font-mono text-xs">
                  Readiness: {readinessPct}%
                </Badge>
              )}
            </div>
          </div>
          <CardDescription className="text-xs">
            Evaluates upstream foundational concept masteries to guarantee readiness before advanced topics.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {detail.prerequisites.length === 0 ? (
            <p className="text-sm text-slate-500 py-3">
              This is a foundational concept with no required prerequisites.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {detail.prerequisites.map((p) => {
                const prereqPct = p.current_mastery !== null && p.current_mastery !== undefined
                  ? Math.round(p.current_mastery * 100)
                  : null;

                return (
                  <div
                    key={p.prerequisite_concept_id}
                    className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex justify-between items-center"
                  >
                    <div>
                      <Link
                        href={`/knowledge/concepts/${p.prerequisite_concept_id}`}
                        className="font-semibold text-sm hover:text-indigo-600"
                      >
                        {p.prerequisite_name}
                      </Link>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {p.relationship_type.replace("_", " ")}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-sm">
                        {prereqPct !== null ? `${prereqPct}%` : "N/A"}
                      </div>
                      <Badge variant="secondary" className="text-[9px] uppercase font-mono">
                        {p.state}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Multi-Tab Audit Histories */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Evidence History (Domain 5 immutable) */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              <CardTitle className="text-base font-bold">Authoritative Learning Evidence</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Immutable assessment observations ingested from Domain 5.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {detail.evidence_history.length === 0 ? (
              <p className="text-xs text-slate-500 py-3">No evidence records observed yet.</p>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {detail.evidence_history.map((ev) => (
                  <div
                    key={ev.id}
                    className="flex items-center justify-between p-2.5 rounded-md border border-slate-100 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-900 text-xs"
                  >
                    <div>
                      <span className="font-semibold capitalize text-slate-800 dark:text-slate-200">
                        {ev.evidence_type} Evidence
                      </span>
                      <div className="text-[10px] text-slate-400">
                        {new Date(ev.created_at).toLocaleString()}
                      </div>
                    </div>
                    <Badge
                      variant={ev.score >= 0.7 ? "success" : ev.score >= 0.5 ? "warning" : "destructive"}
                      className="font-mono"
                    >
                      Score: {Math.round(ev.score * 100)}%
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Mastery Progression History */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-2">
              <History className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              <CardTitle className="text-base font-bold">Mastery State History</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Append-only audit trail of deterministic recalculations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {detail.mastery_history.length === 0 ? (
              <p className="text-xs text-slate-500 py-3">No historical transitions recorded yet.</p>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {detail.mastery_history.map((mh) => (
                  <div
                    key={mh.id}
                    className="flex items-center justify-between p-2.5 rounded-md border border-slate-100 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-900 text-xs"
                  >
                    <div>
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        Trigger: {mh.trigger.replace("_", " ")}
                      </span>
                      <div className="text-[10px] text-slate-400">
                        {new Date(mh.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right font-mono">
                      <span>
                        {mh.previous_mastery !== null && mh.previous_mastery !== undefined
                          ? `${Math.round(mh.previous_mastery * 100)}%`
                          : "nil"}
                        {" → "}
                        <strong>
                          {mh.new_mastery !== null && mh.new_mastery !== undefined
                            ? `${Math.round(mh.new_mastery * 100)}%`
                            : "nil"}
                        </strong>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
