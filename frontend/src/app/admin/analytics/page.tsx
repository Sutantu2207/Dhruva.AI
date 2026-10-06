"use client";

import * as React from "react";
import {
  ShieldCheck,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchDepartmentComparisons } from "@/lib/api";
import type { DepartmentComparisonResponse } from "@/lib/types";

export default function AdminDepartmentAnalyticsPage() {
  const [data, setData] = React.useState<DepartmentComparisonResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    fetchDepartmentComparisons()
      .then((res) => {
        if (active) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Access restricted to Institution Leadership.");
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
            <p className="text-sm text-slate-500 font-medium">Aggregating cross-departmental intelligence...</p>
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
            <AlertCircle className="h-10 w-10 text-red-500 mx-auto" />
            <h2 className="text-base font-bold text-red-900">Institution Scope Restriction</h2>
            <p className="text-xs text-red-700 max-w-md mx-auto">
              {error || "Only Institutional Administrators and Super Admins may compare departments across the college."}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-indigo-600 border-indigo-200 bg-indigo-50 font-mono text-xs">
            Institutional Admin Intelligence
          </Badge>
          <Badge variant="outline" className="font-mono text-xs text-emerald-700 border-emerald-200 bg-emerald-50">
            Privacy Preserving
          </Badge>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 mt-2">
          Cross-Departmental Performance & Learning Benchmarks
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Comparative course completion, assessment rigor, and early intervention loads across academic departments.
        </p>
      </div>

      {/* Privacy Banner */}
      <Card className="border-indigo-100 bg-indigo-50/50">
        <CardContent className="p-4 flex items-center gap-3">
          <ShieldCheck className="h-5 w-5 text-indigo-600 shrink-0" />
          <div className="text-xs text-indigo-900">
            <span className="font-semibold">Deterministic Privacy Rule: </span>
            <span>{data.suppression_policy}</span>
          </div>
        </CardContent>
      </Card>

      {/* Comparative Department Table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Students</th>
                <th className="py-3 px-4">Course Completion</th>
                <th className="py-3 px-4">Avg Assessment</th>
                <th className="py-3 px-4">Concept Mastery</th>
                <th className="py-3 px-4">Career Readiness</th>
                <th className="py-3 px-4">Active Signals</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.departments.map((dept) => (
                <tr key={dept.department_id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3.5 px-4">
                    <span className="font-bold text-slate-900">{dept.department_name}</span>
                    <span className="block text-[11px] font-mono text-slate-400">{dept.department_code}</span>
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-slate-700">
                    {dept.student_count}
                  </td>
                  <td className="py-3.5 px-4">
                    {dept.is_suppressed ? (
                      <Badge variant="outline" className="text-[10px] text-slate-400 border-slate-200">
                        Suppressed (&lt;{data.minimum_cohort_size})
                      </Badge>
                    ) : dept.completion_rate != null ? (
                      <span className="font-semibold text-emerald-600">
                        {(dept.completion_rate * 100).toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-slate-400">N/A</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    {dept.is_suppressed ? (
                      <Badge variant="outline" className="text-[10px] text-slate-400 border-slate-200">
                        Suppressed
                      </Badge>
                    ) : dept.average_score != null ? (
                      <span className="font-semibold text-slate-800">{dept.average_score}%</span>
                    ) : (
                      <span className="text-slate-400">No attempts</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    {dept.is_suppressed ? (
                      <Badge variant="outline" className="text-[10px] text-slate-400 border-slate-200">
                        Suppressed
                      </Badge>
                    ) : dept.concept_mastery != null ? (
                      <span className="font-semibold text-indigo-600">
                        {(dept.concept_mastery * 100).toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-slate-400">Not assessed</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    {dept.is_suppressed ? (
                      <Badge variant="outline" className="text-[10px] text-slate-400 border-slate-200">
                        Suppressed
                      </Badge>
                    ) : dept.career_readiness != null ? (
                      <span className="font-semibold text-purple-600">
                        {(dept.career_readiness * 100).toFixed(1)}%
                      </span>
                    ) : (
                      <span className="text-slate-400">Not assessed</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    {dept.is_suppressed ? (
                      <span className="text-slate-400">—</span>
                    ) : (
                      <span className="font-bold text-amber-600">{dept.active_interventions || 0}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
