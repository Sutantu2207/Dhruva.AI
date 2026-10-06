"use client";

import * as React from "react";
import Link from "next/link";
import {
  GraduationCap,
  TrendingUp,
  BookOpen,
  Briefcase,
  ShieldAlert,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchDepartmentAnalytics, fetchFacultyDashboardAnalytics } from "@/lib/api";
import type { DepartmentAnalytics } from "@/lib/types";

export default function HodDashboardPage() {
  const [data, setData] = React.useState<DepartmentAnalytics | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    // Discover department from user context or faculty dashboard
    fetchFacultyDashboardAnalytics()
      .then(async (facDash) => {
        if (!active) return;
        const rawDash = facDash as unknown as Record<string, unknown>;
        const firstOffering = facDash.offerings[0] as unknown as Record<string, unknown> | undefined;
        const deptId = (typeof rawDash.department_id === "string" ? rawDash.department_id : null) || 
          (firstOffering && typeof firstOffering.department_id === "string" ? firstOffering.department_id : "current");
        try {
          const res = await fetchDepartmentAnalytics(deptId);
          if (active) {
            setData(res);
            setLoading(false);
          }
        } catch (deptErr: unknown) {
          if (active) {
            setError(deptErr instanceof Error ? deptErr.message : "Access restricted to authorized Department HOD.");
            setLoading(false);
          }
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load departmental intelligence.");
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
            <p className="text-sm text-slate-500 font-medium">Loading departmental academic intelligence...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container mx-auto max-w-7xl px-4 py-8">
        <Card className="border-red-200 bg-red-50/50">
          <CardContent className="p-8 text-center space-y-3">
            <ShieldAlert className="h-10 w-10 text-red-500 mx-auto" />
            <h2 className="text-base font-bold text-red-900">Department Scope Restriction</h2>
            <p className="text-xs text-red-700 max-w-md mx-auto">
              {error || "Only authorized Head of Department (HOD) accounts may inspect department-level metrics."}
            </p>
            <div className="pt-2">
              <Link href="/faculty">
                <Button size="sm" variant="outline">Go to Faculty View</Button>
              </Link>
            </div>
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
              HOD Intelligence
            </Badge>
            <Badge variant="outline" className="font-mono text-xs">
              {data.department_code}
            </Badge>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 mt-2">
            Department of {data.department_name}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Department-scoped student counts, faculty allocations, course mastery, and employability signals.
          </p>
        </div>
      </div>

      {/* Top Counts */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4 text-center">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Students</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">{data.total_students}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4 text-center">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Faculty</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">{data.total_faculty}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4 text-center">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Programs</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">{data.total_programs}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4 text-center">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Courses</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">{data.total_courses}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4 text-center">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Offerings</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">{data.total_offerings}</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4 text-center">
            <p className="text-[11px] font-semibold text-slate-400 uppercase">Signals</p>
            <p className="text-xl font-bold text-amber-600 mt-0.5">{data.active_intervention_signals_count}</p>
          </CardContent>
        </Card>
      </div>

      {/* Primary Analytics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Course Completion</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {(data.average_course_completion * 100).toFixed(1)}%
              </p>
              <p className="text-[11px] text-emerald-600 font-medium">Department-wide average</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <GraduationCap className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Assessment Score</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {data.average_assessment_score !== null ? `${data.average_assessment_score}%` : "No released scores"}
              </p>
              <p className="text-[11px] text-slate-500">Evaluated attempts</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <BookOpen className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Concept Mastery</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {data.concept_mastery_average != null ? `${(data.concept_mastery_average * 100).toFixed(1)}%` : "Not assessed"}
              </p>
              <p className="text-[11px] text-indigo-600 font-medium">Knowledge State DAG</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
              <Briefcase className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Career Readiness</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {data.career_readiness_average != null ? `${(data.career_readiness_average * 100).toFixed(1)}%` : "Not assessed"}
              </p>
              <p className="text-[11px] text-purple-600 font-medium">{data.verified_projects_count} verified projects</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Intervention Signals Distribution */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-slate-900">Academic Intervention Signals by Severity</CardTitle>
          <CardDescription className="text-xs">
            Verifiable distribution of students flagged for academic support within this department.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-4 gap-3 text-center text-xs">
            <div className="p-3 bg-red-50 border border-red-100 rounded-xl">
              <p className="text-[11px] font-bold text-red-600 uppercase">Urgent</p>
              <p className="text-2xl font-bold text-red-900 mt-1">{data.interventions_by_severity.urgent}</p>
            </div>
            <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
              <p className="text-[11px] font-bold text-amber-600 uppercase">High</p>
              <p className="text-2xl font-bold text-amber-900 mt-1">{data.interventions_by_severity.high}</p>
            </div>
            <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl">
              <p className="text-[11px] font-bold text-blue-600 uppercase">Medium</p>
              <p className="text-2xl font-bold text-blue-900 mt-1">{data.interventions_by_severity.medium}</p>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <p className="text-[11px] font-bold text-slate-600 uppercase">Low</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{data.interventions_by_severity.low}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
