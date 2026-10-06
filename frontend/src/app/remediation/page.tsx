"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchMyRemediationPlans } from "@/lib/api";
import { RemediationPlan } from "@/lib/types";
import { AlertCircle, ArrowRight, CheckCircle2, Clock, PlayCircle, RefreshCw } from "lucide-react";

export default function StudentRemediationPlansPage() {
  const [plans, setPlans] = useState<RemediationPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPlans() {
      try {
        setLoading(true);
        const data = await fetchMyRemediationPlans();
        setPlans(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load learning recovery plans");
      } finally {
        setLoading(false);
      }
    }
    loadPlans();
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-emerald-400 text-xs font-medium mb-3">
            <RefreshCw className="w-3.5 h-3.5 animate-spin-slow" />
            Deterministic Adaptive Remediation
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-100">Your Learning Recovery Plans</h1>
          <p className="text-neutral-400 mt-2 text-sm leading-relaxed max-w-2xl">
            Tailored, scaffolded learning pathways designed to help you strengthen foundational concepts and master core curriculum objectives at your own pace.
          </p>
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div className="p-12 text-center bg-neutral-900/40 rounded-xl border border-neutral-800/60 animate-pulse">
            <Clock className="w-8 h-8 mx-auto text-neutral-500 mb-3" />
            <p className="text-neutral-400 text-sm">Evaluating learning recovery plans...</p>
          </div>
        )}

        {error && (
          <div className="p-6 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <p className="font-medium text-rose-200">Unable to load plans</p>
              <p className="mt-1 opacity-90">{error}</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && plans.length === 0 && (
          <div className="p-12 text-center bg-neutral-900/30 rounded-2xl border border-neutral-800">
            <CheckCircle2 className="w-12 h-12 mx-auto text-emerald-400 mb-4" />
            <h2 className="text-lg font-semibold text-neutral-200">No Active Remediation Plans</h2>
            <p className="text-neutral-400 text-sm mt-1 max-w-md mx-auto">
              Your concept mastery and assessment records are fully on target. No prerequisite deficits detected.
            </p>
          </div>
        )}

        {/* Plans List */}
        {!loading && !error && plans.length > 0 && (
          <div className="grid gap-6">
            {plans.map((plan) => {
              const completedSteps = plan.steps.filter((s) => s.completion_status === "completed").length;
              const totalSteps = plan.steps.length;
              const progressPct = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

              return (
                <div
                  key={plan.id}
                  className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6 transition-all hover:border-neutral-700 hover:bg-neutral-900"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-indigo-950 text-indigo-400 border border-indigo-800">
                          {plan.diagnosis_type.replace(/_/g, " ")}
                        </span>
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                            plan.status === "completed" || plan.status === "closed"
                              ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                              : plan.status === "in_progress"
                              ? "bg-blue-950 text-blue-400 border border-blue-800"
                              : "bg-amber-950 text-amber-400 border border-amber-800"
                          }`}
                        >
                          {plan.status.replace(/_/g, " ")}
                        </span>
                      </div>
                      <h2 className="text-xl font-bold text-neutral-100">
                        Focus: {plan.target_concept_name || "Target Concept"}
                      </h2>
                      <p className="text-neutral-400 text-sm max-w-xl">
                        {plan.diagnosis_reason}
                      </p>
                    </div>

                    <div className="flex flex-col md:items-end justify-between gap-4 shrink-0">
                      <div className="text-left md:text-right">
                        <div className="text-xs text-neutral-400">Scaffolded Progress</div>
                        <div className="text-sm font-semibold text-neutral-200 mt-0.5">
                          {completedSteps} of {totalSteps} steps completed ({progressPct}%)
                        </div>
                        <div className="w-36 h-2 bg-neutral-800 rounded-full mt-1.5 overflow-hidden">
                          <div
                            className="h-full bg-emerald-500 rounded-full transition-all"
                            style={{ width: `${progressPct}%` }}
                          />
                        </div>
                      </div>

                      <Link
                        href={`/remediation/${plan.id}`}
                        className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-neutral-100 hover:bg-white text-neutral-950 text-sm font-medium rounded-xl transition-all shadow-sm"
                      >
                        {plan.status === "in_progress" ? (
                          <>
                            Continue Recovery
                            <PlayCircle className="w-4 h-4 text-neutral-900" />
                          </>
                        ) : (
                          <>
                            View Recovery Plan
                            <ArrowRight className="w-4 h-4 text-neutral-900" />
                          </>
                        )}
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
