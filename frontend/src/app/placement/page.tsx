"use client";

import * as React from "react";
import {
  Briefcase,
  TrendingUp,
  Award,
  FolderGit2,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchPlacementAnalytics } from "@/lib/api";
import type { PlacementAnalytics } from "@/lib/types";

export default function PlacementAnalyticsPage() {
  const [data, setData] = React.useState<PlacementAnalytics | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    fetchPlacementAnalytics()
      .then((res) => {
        if (active) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Access restricted to Placement Officers & Leadership.");
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
            <p className="text-sm text-slate-500 font-medium">Aggregating institution-wide employability intelligence...</p>
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
            <h2 className="text-base font-bold text-red-900">Placement Scoping Restriction</h2>
            <p className="text-xs text-red-700 max-w-md mx-auto">
              {error || "Only authorized Placement Officers and Institutional Administrators may access placement metrics."}
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
            Institutional Employability Intelligence
          </Badge>
          <Badge variant="outline" className="font-mono text-xs text-slate-500">
            {data.algorithm_version}
          </Badge>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 mt-2">
          Placement Readiness & Industry Skill Diagnostics
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Honest readiness tiers, systemic curriculum gaps, and verified portfolio proof for {data.total_targetable_students} enrolled students.
        </p>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <Briefcase className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Targetable Learners</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{data.total_targetable_students}</p>
              <p className="text-xs text-blue-600 mt-0.5 font-medium">Eligible cohorts</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Mean Readiness</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {data.average_readiness_percentage !== null ? `${data.average_readiness_percentage}%` : "Not assessed"}
              </p>
              <p className="text-xs text-emerald-600 mt-0.5 font-medium">Weighted rubric score</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
              <FolderGit2 className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Verified Projects</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {(data.verified_project_coverage_rate * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-purple-600 mt-0.5 font-medium">Artifact proof coverage</p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
              <Award className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Portfolio Health</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">
                {data.portfolio_completeness_average != null ? `${(data.portfolio_completeness_average * 100).toFixed(0)}%` : "Not assessed"}
              </p>
              <p className="text-xs text-amber-600 mt-0.5 font-medium">Completeness average</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Readiness Tiers Breakdown */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-slate-900">Employability Readiness Tiers</CardTitle>
          <CardDescription className="text-xs">
            Deterministic categorization based on verified project evidence and evaluated assessment scores.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
            <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
              <span className="text-[11px] font-bold text-emerald-700 uppercase">Placement Ready (&ge;75%)</span>
              <p className="text-3xl font-extrabold text-emerald-900 mt-1">{data.career_readiness_tiers.ready}</p>
              <span className="text-[10px] text-emerald-600 font-medium">Targetable for campus visits</span>
            </div>
            <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl">
              <span className="text-[11px] font-bold text-blue-700 uppercase">Approaching (60-74%)</span>
              <p className="text-3xl font-extrabold text-blue-900 mt-1">{data.career_readiness_tiers.approaching}</p>
              <span className="text-[10px] text-blue-600 font-medium">Requires minor skill polish</span>
            </div>
            <div className="p-4 bg-amber-50 border border-amber-100 rounded-xl">
              <span className="text-[11px] font-bold text-amber-700 uppercase">Developing (&lt;60%)</span>
              <p className="text-3xl font-extrabold text-amber-900 mt-1">{data.career_readiness_tiers.developing}</p>
              <span className="text-[10px] text-amber-600 font-medium">Need project capstones</span>
            </div>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[11px] font-bold text-slate-600 uppercase">Not Assessed</span>
              <p className="text-3xl font-extrabold text-slate-900 mt-1">{data.career_readiness_tiers.not_assessed}</p>
              <span className="text-[10px] text-slate-400 font-medium">Insufficient evidence</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Systemic Skill Gaps Watchlist */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-slate-900">Systemic Institutional Skill Deficits</CardTitle>
          <CardDescription className="text-xs">
            Aggregated skill gaps blocking multiple learners from attaining target career role benchmarks.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          {data.systemic_skill_gaps.length === 0 ? (
            <p className="text-xs text-slate-400 py-4 text-center">No systemic skill gaps recorded across active cohorts.</p>
          ) : (
            <div className="divide-y divide-slate-100 text-xs">
              {data.systemic_skill_gaps.map((gap, idx) => (
                <div key={idx} className="py-2.5 flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-slate-900">{gap.skill_name}</span>
                    <p className="text-[11px] text-slate-500">
                      Affects <strong className="text-slate-700">{gap.gap_count}</strong> students aiming for this domain
                    </p>
                  </div>
                  <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-800 text-[11px] font-mono">
                    Severity: {(gap.average_gap_severity * 100).toFixed(0)}%
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
