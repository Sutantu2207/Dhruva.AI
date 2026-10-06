"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchInstitutionalRemediationAnalytics } from "@/lib/api";
import { InstitutionalRemediationAnalytics } from "@/lib/types";
import {
  AlertCircle,
  Building,
  Clock,
  FileCheck,
} from "lucide-react";

export default function AdminRemediationAnalyticsPage() {
  const [data, setData] = useState<InstitutionalRemediationAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const res = await fetchInstitutionalRemediationAnalytics();
        setData(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load institutional analytics");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-950/80 border border-purple-800 text-purple-400 text-xs font-semibold uppercase tracking-wider mb-3">
              <Building className="w-3.5 h-3.5" />
              Institutional Leadership • Domain 10
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-neutral-100">
              Institution-Wide Remediation Outcomes
            </h1>
            <p className="text-neutral-400 text-sm mt-1 max-w-2xl leading-relaxed">
              Holistic academic recovery intelligence, closure velocity, curriculum bottleneck indicators, and NAAC/NBA audit evidence mapping.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/admin/remediation/content-gaps"
              className="px-4 py-2 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs font-semibold rounded-xl transition-all"
            >
              Content Gaps ({data?.content_availability_gaps || 0})
            </Link>
            <Link
              href="/admin/accreditation"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md flex items-center gap-1.5"
            >
              <FileCheck className="w-3.5 h-3.5" /> Audit & Accreditation
            </Link>
          </div>
        </div>

        {loading && (
          <div className="p-12 text-center bg-neutral-900/40 rounded-2xl border border-neutral-800">
            <Clock className="w-8 h-8 mx-auto text-neutral-500 animate-spin mb-3" />
            <p className="text-neutral-400 text-sm">Synthesizing institutional metrics...</p>
          </div>
        )}

        {error && (
          <div className="p-6 bg-rose-950/40 border border-rose-800 rounded-2xl text-rose-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <p className="font-semibold text-rose-200">Unable to load institutional analytics</p>
              <p className="mt-1 opacity-90">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && data && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-1">
                <span className="text-xs text-neutral-400 font-medium">Total Generated Interventions</span>
                <div className="text-2xl font-bold text-neutral-100">{data.plans_created}</div>
                <span className="text-[11px] text-neutral-500 block">Across all academic programs</span>
              </div>

              <div className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-1">
                <span className="text-xs text-neutral-400 font-medium">Resolved & Closed</span>
                <div className="text-2xl font-bold text-emerald-400">{data.plans_completed}</div>
                <span className="text-[11px] text-neutral-500 block">
                  {Math.round(Number(data.completion_rate) * 100)}% overall completion rate
                </span>
              </div>

              <div className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-1">
                <span className="text-xs text-neutral-400 font-medium">Measured Learning Gains</span>
                <div className="text-2xl font-bold text-blue-400">
                  {Math.round(Number(data.improvement_rate) * 100)}%
                </div>
                <span className="text-[11px] text-neutral-500 block">Demonstrated post-retest improvement</span>
              </div>

              <div className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-1">
                <span className="text-xs text-neutral-400 font-medium">Avg Concept Mastery Delta</span>
                <div className="text-2xl font-bold text-purple-400">
                  +{Number(data.average_mastery_improvement).toFixed(2)}
                </div>
                <span className="text-[11px] text-neutral-500 block">Observable knowledge growth</span>
              </div>
            </div>

            <div className="p-6 bg-neutral-900/60 border border-neutral-800 rounded-2xl space-y-4">
              <h2 className="text-sm font-bold text-neutral-200 uppercase tracking-wider">
                Systemic Remediation Demand By Concept
              </h2>
              {data.concepts_highest_demand.length === 0 ? (
                <p className="text-xs text-neutral-500 py-4 text-center">No concept bottlenecks recorded</p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {data.concepts_highest_demand.map((c, i) => (
                    <div
                      key={i}
                      className="p-3 bg-neutral-950/80 rounded-xl border border-neutral-800/60 flex items-center justify-between text-xs"
                    >
                      <span className="font-medium text-neutral-200">{c.name}</span>
                      <span className="px-2 py-0.5 bg-neutral-800 text-neutral-300 rounded font-semibold">
                        {c.count} students
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
