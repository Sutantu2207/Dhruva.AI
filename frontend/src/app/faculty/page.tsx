"use client";

import * as React from "react";
import Link from "next/link";
import {
  BookOpen,
  AlertTriangle,
  ClipboardCheck,
  ArrowRight,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchFacultyDashboardAnalytics } from "@/lib/api";
import type { FacultyDashboardAnalytics } from "@/lib/types";

export default function FacultyDashboardPage() {
  const [data, setData] = React.useState<FacultyDashboardAnalytics | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    fetchFacultyDashboardAnalytics()
      .then((res) => {
        if (active) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load faculty analytics.");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <div className="flex h-64 items-center justify-center">
          <div className="text-center space-y-2">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent mx-auto" />
            <p className="text-sm text-slate-500 font-medium">Aggregating authorized academic intelligence...</p>
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
            <AlertCircle className="h-8 w-8 text-red-500 mx-auto" />
            <p className="text-sm font-semibold text-red-700">{error || "No authorized faculty data available."}</p>
            <p className="text-xs text-red-600">Ensure your account has assigned courses or teaching credentials in your department.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-indigo-600 border-indigo-200 bg-indigo-50 font-mono text-xs">
              Domain 9 — Academic Intelligence
            </Badge>
            <Badge variant="outline" className="text-slate-600 font-mono text-xs">
              Role Scoped
            </Badge>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 mt-2">
            Faculty Academic Oversight
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Deterministic progress, rubric grading queues, and observable early intervention signals.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/faculty/grading">
            <Button className="bg-indigo-600 hover:bg-indigo-700 text-white gap-2">
              <ClipboardCheck className="h-4 w-4" />
              Grading Queue
              {data.pending_grading_count > 0 && (
                <span className="ml-1 rounded-full bg-indigo-500 px-2 py-0.5 text-xs text-white">
                  {data.pending_grading_count}
                </span>
              )}
            </Button>
          </Link>
          <Link href="/faculty/interventions">
            <Button variant="outline" className="border-amber-300 text-amber-700 hover:bg-amber-50 gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              Intervention Signals
              {data.active_intervention_signals_count > 0 && (
                <span className="ml-1 rounded-full bg-amber-500 px-2 py-0.5 text-xs text-white">
                  {data.active_intervention_signals_count}
                </span>
              )}
            </Button>
          </Link>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <BookOpen className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Assigned Offerings</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{data.assigned_offerings_count}</p>
              <p className="text-xs text-slate-500 mt-0.5">{data.total_enrolled_students} enrolled learners</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Avg Completion</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {(data.average_cohort_completion * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-emerald-600 mt-0.5 font-medium">Deterministic course progress</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <ClipboardCheck className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Grading</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{data.pending_grading_count}</p>
              <p className="text-xs text-indigo-600 mt-0.5 font-medium">Questions & evidence</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Signals</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{data.active_intervention_signals_count}</p>
              <p className="text-xs text-amber-600 mt-0.5 font-medium">Observable distress facts</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Urgent Intervention Signals Alert Strip */}
      {data.urgent_signals && data.urgent_signals.length > 0 && (
        <Card className="border-red-200 bg-red-50/40">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <CardTitle className="text-base text-red-900">High-Priority Academic Signals Detected</CardTitle>
              </div>
              <Link href="/faculty/interventions">
                <Button variant="ghost" size="sm" className="text-red-700 hover:text-red-800 text-xs">
                  Review All ({data.urgent_signals.length}) →
                </Button>
              </Link>
            </div>
            <CardDescription className="text-xs text-red-700">
              These learners exhibit multiple verifiable academic difficulties (repeated assessment failures, overdue reviews, or prerequisite deficits).
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0 space-y-2">
            {data.urgent_signals.slice(0, 3).map((sig) => (
              <div
                key={sig.id}
                className="flex items-center justify-between p-3 rounded-lg bg-white border border-red-100 text-xs shadow-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900">{sig.student_name || "Enrolled Student"}</span>
                    <Badge variant="outline" className="text-red-700 border-red-200 bg-red-50 text-[10px] uppercase">
                      {sig.severity}
                    </Badge>
                    <span className="text-slate-400 font-mono text-[11px]">{sig.enrollment_number}</span>
                  </div>
                  <p className="text-slate-600 mt-1">{sig.title}</p>
                </div>
                <Link href={`/faculty/interventions?id=${sig.id}`}>
                  <Button size="sm" variant="outline" className="text-xs h-7">
                    Take Action
                  </Button>
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Assigned Course Offerings List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Assigned Course Offerings</h2>
          <p className="text-xs text-slate-500">Click an offering to view lesson mastery, concept DAG, and question analytics.</p>
        </div>

        {data.offerings.length === 0 ? (
          <Card className="border-slate-200 p-8 text-center">
            <p className="text-sm text-slate-500 font-medium">No active course offerings currently assigned.</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {data.offerings.map((off) => (
              <Card key={off.offering_id} className="border-slate-200 hover:border-indigo-300 transition-all flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="font-mono text-xs">
                      {off.course_code}
                    </Badge>
                    <Badge variant="secondary" className="text-xs">
                      Section {off.section_name}
                    </Badge>
                  </div>
                  <CardTitle className="text-base text-slate-900 mt-2">{off.course_title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="space-y-2 border-t border-slate-100 pt-3 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Enrolled Students</span>
                      <span className="font-semibold text-slate-900">{off.enrolled_count}</span>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Cohort Completion</span>
                      <span className="font-semibold text-emerald-600">{(off.completion_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Pending Evaluations</span>
                      <span className={off.pending_grading_count > 0 ? "font-semibold text-amber-600" : "text-slate-400"}>
                        {off.pending_grading_count}
                      </span>
                    </div>
                  </div>

                  <div className="pt-2">
                    <Link href={`/faculty/courses/${off.offering_id}`}>
                      <Button className="w-full text-xs h-8 gap-2 bg-slate-900 hover:bg-slate-800 text-white">
                        <span>Course Analytics Drill-down</span>
                        <ArrowRight className="h-3 w-3" />
                      </Button>
                    </Link>
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
