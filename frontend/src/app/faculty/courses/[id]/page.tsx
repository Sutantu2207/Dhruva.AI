"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Download,
  Users,
  TrendingUp,
  AlertTriangle,
  FolderGit2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchCourseOfferingAnalytics, getCourseOfferingExportCsvUrl } from "@/lib/api";
import type { CourseOfferingAnalytics } from "@/lib/types";

export default function CourseOfferingAnalyticsPage() {
  const params = useParams();
  const offeringId = params?.id as string;

  const [data, setData] = React.useState<CourseOfferingAnalytics | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!offeringId) return;
    let active = true;
    fetchCourseOfferingAnalytics(offeringId)
      .then((res) => {
        if (active) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load offering analytics.");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [offeringId]);

  if (loading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <div className="flex h-64 items-center justify-center">
          <div className="text-center space-y-2">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent mx-auto" />
            <p className="text-sm text-slate-500 font-medium">Computing offering and question analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <Card className="border-red-200 bg-red-50/50">
          <CardContent className="p-6 text-center space-y-3">
            <p className="text-sm font-semibold text-red-700">{error || "Course offering not found or unauthorized."}</p>
            <Link href="/faculty">
              <Button variant="outline" size="sm">Back to Dashboard</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <Link href="/faculty" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 mb-2">
            <ArrowLeft className="h-3 w-3" />
            Back to Faculty Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-mono text-xs">
              {data.course_code}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              Section {data.section_name}
            </Badge>
            <Badge variant="outline" className="text-xs font-mono text-slate-500">
              {data.algorithm_version}
            </Badge>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 mt-1">
            {data.course_title}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <a href={getCourseOfferingExportCsvUrl(data.offering_id)} download>
            <Button variant="outline" className="gap-2 text-xs">
              <Download className="h-4 w-4" />
              Export Roster CSV
            </Button>
          </a>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Learners</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{data.enrolled_count}</p>
              <p className="text-xs text-blue-600 mt-0.5 font-medium">{data.active_learners_count} active in modules</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Lesson Progress</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {data.average_lesson_progress.toFixed(1)}%
              </p>
              <p className="text-xs text-slate-500 mt-0.5">{(data.completion_rate * 100).toFixed(1)}% full completion</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Academic Signals</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{data.active_intervention_signals_count}</p>
              <p className="text-xs text-amber-600 mt-0.5 font-medium">Students needing support</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
              <FolderGit2 className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Project Evidence</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{data.project_evidence_count}</p>
              <p className="text-xs text-purple-600 mt-0.5 font-medium">Verified artifacts</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Difficult Concepts Watchlist */}
      {data.difficult_concepts && data.difficult_concepts.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/40">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
            <div>
              <p className="text-xs font-bold text-amber-900 uppercase tracking-wider">Attention: Low Concept Mastery Detected</p>
              <p className="text-xs text-amber-700 mt-0.5">
                The cohort has under 50% average mastery in: <span className="font-semibold">{data.difficult_concepts.join(", ")}</span>. Consider reviewing these concepts in upcoming class sessions.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Assessments Breakdown */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Assessment Analytics & Question Performance</h2>

        {data.assessments_summary.length === 0 ? (
          <Card className="border-slate-200 p-6 text-center">
            <p className="text-sm text-slate-500">No assessments recorded for this course offering yet.</p>
          </Card>
        ) : (
          <div className="space-y-6">
            {data.assessments_summary.map((ass) => (
              <Card key={ass.assessment_id} className="border-slate-200 shadow-sm">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <CardTitle className="text-base text-slate-900">{ass.title}</CardTitle>
                      <CardDescription className="text-xs">
                        Completed: {ass.total_completed} / {ass.total_assigned} ({(ass.completion_rate * 100).toFixed(0)}%)
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-medium">
                      <div>
                        <span className="text-slate-500">Average: </span>
                        <span className="font-bold text-slate-900">{ass.average_score !== null ? `${ass.average_score}%` : "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Median: </span>
                        <span className="font-bold text-slate-900">{ass.median_score !== null ? `${ass.median_score}%` : "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Pass Rate: </span>
                        <span className="font-bold text-emerald-600">{ass.pass_rate != null ? `${(ass.pass_rate * 100).toFixed(0)}%` : "N/A"}</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-4 space-y-4">
                  {/* Score Distribution Buckets */}
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Score Distribution</p>
                    <div className="grid grid-cols-4 gap-2 text-center text-xs">
                      <div className="p-2 rounded-lg bg-red-50 border border-red-100">
                        <span className="block text-[11px] text-red-600 font-medium">0 - 49%</span>
                        <span className="text-base font-bold text-red-900">{ass.score_distribution["0_to_49"]}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-amber-50 border border-amber-100">
                        <span className="block text-[11px] text-amber-600 font-medium">50 - 69%</span>
                        <span className="text-base font-bold text-amber-900">{ass.score_distribution["50_to_69"]}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-blue-50 border border-blue-100">
                        <span className="block text-[11px] text-blue-600 font-medium">70 - 84%</span>
                        <span className="text-base font-bold text-blue-900">{ass.score_distribution["70_to_84"]}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-100">
                        <span className="block text-[11px] text-emerald-600 font-medium">85 - 100%</span>
                        <span className="text-base font-bold text-emerald-900">{ass.score_distribution["85_to_100"]}</span>
                      </div>
                    </div>
                  </div>

                  {/* Question Drill-Down */}
                  {ass.questions && ass.questions.length > 0 && (
                    <div className="border-t border-slate-100 pt-3">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Question Diagnostics</p>
                      <div className="divide-y divide-slate-100 text-xs">
                        {ass.questions.map((q) => (
                          <div key={q.question_id} className="py-2 flex items-center justify-between gap-4">
                            <div className="min-w-0">
                              <p className="font-medium text-slate-800 truncate">{q.question_title}</p>
                              <div className="flex items-center gap-2 text-slate-400 text-[11px]">
                                <span>Type: {q.question_type}</span>
                                <span>•</span>
                                <span>Attempts: {q.attempts_count}</span>
                                {q.accuracy_rate !== null && (
                                  <>
                                    <span>•</span>
                                    <span>Accuracy: {((q.accuracy_rate || 0) * 100).toFixed(0)}%</span>
                                  </>
                                )}
                              </div>
                            </div>
                            <div>
                              {q.review_recommended ? (
                                <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-800 text-[10px]">
                                  Review Recommended
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="border-slate-200 text-slate-500 text-[10px]">
                                  Normal
                                </Badge>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Concept Mastery Analytics */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Concept Mastery Distribution</h2>
        {data.concepts_analytics.length === 0 ? (
          <Card className="border-slate-200 p-6 text-center">
            <p className="text-sm text-slate-500">No canonical concept states mapped to this course curriculum.</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.concepts_analytics.map((c) => (
              <Card key={c.concept_id} className="border-slate-200 shadow-sm">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-slate-900">{c.concept_name}</CardTitle>
                    <span className="text-xs font-bold font-mono text-indigo-600">
                      {(c.average_mastery * 100).toFixed(0)}% Avg
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 pt-0 text-xs">
                  <div className="grid grid-cols-4 gap-1 text-center font-mono text-[11px]">
                    <div className="bg-slate-50 p-1.5 rounded">
                      <span className="text-slate-400 block text-[9px]">BEG</span>
                      {c.mastery_distribution.beginner}
                    </div>
                    <div className="bg-slate-50 p-1.5 rounded">
                      <span className="text-slate-400 block text-[9px]">DEV</span>
                      {c.mastery_distribution.developing}
                    </div>
                    <div className="bg-slate-50 p-1.5 rounded">
                      <span className="text-slate-400 block text-[9px]">PROF</span>
                      {c.mastery_distribution.proficient}
                    </div>
                    <div className="bg-slate-50 p-1.5 rounded">
                      <span className="text-slate-400 block text-[9px]">ADV</span>
                      {c.mastery_distribution.advanced}
                    </div>
                  </div>
                  <div className="flex justify-between text-slate-500 text-[11px] pt-1 border-t border-slate-100">
                    <span>High Retention Risk: <strong className="text-slate-800">{c.high_retention_risk_count}</strong></span>
                    <span>Overdue Reviews: <strong className="text-slate-800">{c.overdue_reviews_count}</strong></span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
