"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchContentGaps } from "@/lib/api";
import { ContentGap } from "@/lib/types";
import { AlertCircle, ArrowLeft, CheckCircle2, Clock, FileWarning } from "lucide-react";

export default function AdminContentGapsPage() {
  const [gaps, setGaps] = useState<ContentGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await fetchContentGaps();
        setGaps(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load content gap records");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12">
      <div className="max-w-5xl mx-auto space-y-8">
        <div>
          <Link
            href="/admin/remediation"
            className="inline-flex items-center gap-2 text-xs text-neutral-400 hover:text-neutral-200 transition-colors mb-3"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Remediation Intelligence
          </Link>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/80 border border-amber-800 text-amber-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <FileWarning className="w-3.5 h-3.5" />
            Curriculum Deficiency Auditing
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-neutral-100">
            Institutional Content Availability Gaps
          </h1>
          <p className="text-neutral-400 text-sm mt-1 max-w-2xl leading-relaxed">
            Identifies concepts where students repeatedly require remediation but no approved micro-lesson or practice question exists in Domain 4 or Domain 5.
          </p>
        </div>

        {loading && (
          <div className="p-12 text-center bg-neutral-900/40 rounded-2xl border border-neutral-800">
            <Clock className="w-8 h-8 mx-auto text-neutral-500 animate-spin mb-3" />
            <p className="text-neutral-400 text-sm">Auditing curriculum coverage gaps...</p>
          </div>
        )}

        {error && (
          <div className="p-6 bg-rose-950/40 border border-rose-800 rounded-2xl text-rose-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <p className="font-semibold text-rose-200">Unable to load gaps</p>
              <p className="mt-1 opacity-90">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && gaps.length === 0 && (
          <div className="p-12 text-center bg-neutral-900/30 rounded-2xl border border-neutral-800">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <h2 className="text-lg font-bold text-neutral-200">Zero Content Gaps Detected</h2>
            <p className="text-neutral-400 text-sm mt-1 max-w-md mx-auto">
              All concepts with remediation demand have approved learning modules and valid assessment questions available.
            </p>
          </div>
        )}

        {!loading && !error && gaps.length > 0 && (
          <div className="grid gap-4">
            {gaps.map((gap) => (
              <div
                key={gap.id}
                className="p-5 bg-neutral-900/60 border border-neutral-800 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-950 text-rose-400 border border-rose-800">
                      {gap.gap_type.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs font-mono text-neutral-500">
                      Demand: {gap.demand_count} student{gap.demand_count > 1 ? "s" : ""}
                    </span>
                  </div>
                  <h2 className="text-base font-bold text-neutral-100">
                    Deficient Concept: {gap.concept_name}
                  </h2>
                  <p className="text-xs text-neutral-400">
                    Detected during automated remediation synthesis. Content creation needed in Domain 4.
                  </p>
                </div>

                <div className="shrink-0">
                  <span className="px-3 py-1 bg-amber-950/80 border border-amber-800/80 text-amber-300 text-xs font-semibold rounded-xl">
                    Unresolved Gap
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
