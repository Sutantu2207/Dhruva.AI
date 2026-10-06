"use client";

import React, { useEffect, useState } from "react";
import { fetchInstitutionalRemediationAnalytics } from "@/lib/api";
import { InstitutionalRemediationAnalytics } from "@/lib/types";
import {
  AlertTriangle,
  Award,
  Clock,
  Layers,
  TrendingUp,
} from "lucide-react";

export default function HodRemediationAnalyticsPage() {
  const [analytics, setAnalytics] = useState<InstitutionalRemediationAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await fetchInstitutionalRemediationAnalytics();
        setAnalytics(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load departmental remediation metrics");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-3">
            <Layers className="w-3.5 h-3.5" />
            Departmental Intelligence • Domain 10
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-neutral-100">
            Remediation & Slow-Learner Analytics
          </h1>
          <p className="text-neutral-400 text-sm mt-1 max-w-2xl leading-relaxed">
            Monitor department-wide remediation demand, student recovery closure velocity, and deterministic concept mastery gains.
          </p>
        </div>

        {loading && (
          <div className="p-12 text-center bg-neutral-900/40 rounded-2xl border border-neutral-800">
            <Clock className="w-8 h-8 mx-auto text-neutral-500 animate-spin mb-3" />
            <p className="text-neutral-400 text-sm">Aggregating departmental recovery outcomes...</p>
          </div>
        )}

        {error && (
          <div className="p-6 bg-rose-950/40 border border-rose-800 rounded-2xl text-rose-300 text-sm flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <p className="font-semibold text-rose-200">Unable to load metrics</p>
              <p className="mt-1 opacity-90">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && analytics && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-1">
                <span className="text-xs text-neutral-400 font-medium">Remediation Plans</span>
                <div className="text-2xl font-bold text-neutral-100">{analytics.plans_created}</div>
                <span className="text-[11px] text-neutral-500 block">Total generated interventions</span>
              </div>

              <div className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-1">
                <span className="text-xs text-neutral-400 font-medium">Completion Rate</span>
                <div className="text-2xl font-bold text-emerald-400">
                  {Math.round(Number(analytics.completion_rate) * 100)}%
                </div>
                <span className="text-[11px] text-neutral-500 block">
                  {analytics.plans_completed} of {analytics.plans_created} completed
                </span>
              </div>

              <div className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-1">
                <span className="text-xs text-neutral-400 font-medium">Improvement Rate</span>
                <div className="text-2xl font-bold text-blue-400">
                  {Math.round(Number(analytics.improvement_rate) * 100)}%
                </div>
                <span className="text-[11px] text-neutral-500 block">Demonstrated post-retest delta</span>
              </div>

              <div className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-1">
                <span className="text-xs text-neutral-400 font-medium">Avg Mastery Gain</span>
                <div className="text-2xl font-bold text-purple-400">
                  +{Number(analytics.average_mastery_improvement).toFixed(2)}
                </div>
                <span className="text-[11px] text-neutral-500 block">Domain 6 knowledge state gain</span>
              </div>
            </div>

            {/* Distribution Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  <h2 className="text-base font-bold text-neutral-100">Outcome Classification Distribution</h2>
                </div>
                <div className="space-y-3 text-xs">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-neutral-400">Improved</span>
                      <span className="font-semibold text-neutral-200">
                        {Math.round(Number(analytics.improvement_rate) * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${Math.round(Number(analytics.improvement_rate) * 100)}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-neutral-400">Partially Improved</span>
                      <span className="font-semibold text-neutral-200">
                        {Math.round(Number(analytics.partial_improvement_rate) * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.round(Number(analytics.partial_improvement_rate) * 100)}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-neutral-400">No Significant Change</span>
                      <span className="font-semibold text-neutral-200">
                        {Math.round(Number(analytics.no_significant_change_rate) * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full"
                        style={{ width: `${Math.round(Number(analytics.no_significant_change_rate) * 100)}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-neutral-400">Regressed</span>
                      <span className="font-semibold text-neutral-200">
                        {Math.round(Number(analytics.regression_rate) * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-rose-500 rounded-full"
                        style={{ width: `${Math.round(Number(analytics.regression_rate) * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Highest Demand Weak Concepts */}
              <div className="p-6 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-4">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-indigo-400" />
                  <h2 className="text-base font-bold text-neutral-100">Concepts with Highest Remediation Demand</h2>
                </div>
                {analytics.concepts_highest_demand.length === 0 ? (
                  <p className="text-xs text-neutral-500 py-6 text-center">No concept bottlenecks recorded</p>
                ) : (
                  <div className="space-y-2">
                    {analytics.concepts_highest_demand.map((c, i) => (
                      <div
                        key={i}
                        className="p-3 bg-neutral-950/80 rounded-xl border border-neutral-800/60 flex items-center justify-between text-xs"
                      >
                        <span className="font-medium text-neutral-200">{c.name}</span>
                        <span className="px-2 py-0.5 bg-neutral-800 text-neutral-300 rounded font-semibold">
                          {c.count} plans
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Content Availability Status */}
            <div className="p-4 bg-neutral-900/30 border border-neutral-800/80 rounded-2xl flex items-center justify-between text-xs">
              <span className="text-neutral-400">Institutional Content Availability Gaps:</span>
              <span
                className={`font-bold px-2 py-0.5 rounded ${
                  analytics.content_availability_gaps > 0
                    ? "bg-amber-950 text-amber-400 border border-amber-800"
                    : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                }`}
              >
                {analytics.content_availability_gaps} unresolved gaps
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
