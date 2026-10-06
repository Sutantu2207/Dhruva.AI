"use client";

import React, { useEffect, useState } from "react";
import { fetchFacultyRemediationPlans, facultyOverrideRemediationPlan } from "@/lib/api";
import { RemediationPlan } from "@/lib/types";
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Pause,
  Play,
  ShieldCheck,
  UserCheck,
  XCircle,
} from "lucide-react";

export default function FacultyRemediationManagementPage() {
  const [plans, setPlans] = useState<RemediationPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      try {
        setLoading(true);
        const data = await fetchFacultyRemediationPlans();
        if (isMounted) setPlans(data);
      } catch (err: unknown) {
        if (isMounted) setError(err instanceof Error ? err.message : "Failed to load faculty remediation records");
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, []);

  const refreshPlans = async () => {
    try {
      setLoading(true);
      const data = await fetchFacultyRemediationPlans();
      setPlans(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load faculty remediation records");
    } finally {
      setLoading(false);
    }
  };

  const handleOverride = async (
    planId: string,
    action: "approve" | "pause" | "resume" | "close",
    defaultReason: string
  ) => {
    const reason = prompt("Enter override or approval rationale:", defaultReason);
    if (!reason) return;

    try {
      setActionLoading(`${planId}-${action}`);
      await facultyOverrideRemediationPlan(planId, action, reason);
      await refreshPlans();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error executing override");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-800 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-3">
            <UserCheck className="w-3.5 h-3.5" />
            Faculty Remediation Oversight
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-neutral-100">
            Student Learning Recovery Workflows
          </h1>
          <p className="text-neutral-400 text-sm mt-1 max-w-2xl leading-relaxed">
            Review deterministically generated remediation plans, evaluate prerequisite diagnostic profiles, and apply authorized faculty overrides.
          </p>
        </div>

        {/* State Banners */}
        {loading && (
          <div className="p-12 text-center bg-neutral-900/40 rounded-2xl border border-neutral-800">
            <Clock className="w-8 h-8 mx-auto text-neutral-500 animate-spin mb-3" />
            <p className="text-neutral-400 text-sm">Loading assigned remediation workflows...</p>
          </div>
        )}

        {error && (
          <div className="p-6 bg-rose-950/40 border border-rose-800 rounded-2xl text-rose-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <p className="font-semibold text-rose-200">Unable to load plans</p>
              <p className="mt-1 opacity-90">{error}</p>
            </div>
          </div>
        )}

        {/* Remediation Plans Table / Cards */}
        {!loading && !error && plans.length === 0 && (
          <div className="p-12 text-center bg-neutral-900/30 rounded-2xl border border-neutral-800">
            <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <h2 className="text-lg font-bold text-neutral-200">No Pending Remediation Workflows</h2>
            <p className="text-neutral-400 text-sm mt-1">
              All enrolled students in your teaching scope are meeting foundational mastery criteria.
            </p>
          </div>
        )}

        {!loading && !error && plans.length > 0 && (
          <div className="grid gap-6">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6 transition-all space-y-4"
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded bg-neutral-800 text-neutral-300">
                        {plan.diagnosis_type.replace(/_/g, " ")}
                      </span>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded font-medium ${
                          plan.status === "closed" || plan.status === "completed"
                            ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                            : plan.status === "paused"
                            ? "bg-amber-950 text-amber-400 border border-amber-800"
                            : "bg-blue-950 text-blue-400 border border-blue-800"
                        }`}
                      >
                        {plan.status.toUpperCase()}
                      </span>
                      <span className="text-xs text-neutral-500">
                        Priority: {Number(plan.priority_score).toFixed(2)}
                      </span>
                    </div>

                    <h2 className="text-xl font-bold text-neutral-100">
                      Target Concept: {plan.target_concept_name || "Concept"}
                    </h2>
                    <p className="text-neutral-400 text-xs leading-relaxed max-w-2xl">
                      {plan.diagnosis_reason}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    {plan.status === "recommended" && (
                      <button
                        onClick={() => handleOverride(plan.id, "approve", "Approved after instructor review")}
                        disabled={actionLoading === `${plan.id}-approve`}
                        className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow"
                      >
                        <CheckCircle className="w-3.5 h-3.5" /> Approve Plan
                      </button>
                    )}

                    {plan.status === "in_progress" && (
                      <button
                        onClick={() => handleOverride(plan.id, "pause", "Paused during exam interval")}
                        disabled={actionLoading === `${plan.id}-pause`}
                        className="px-3.5 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
                      >
                        <Pause className="w-3.5 h-3.5" /> Pause
                      </button>
                    )}

                    {plan.status === "paused" && (
                      <button
                        onClick={() => handleOverride(plan.id, "resume", "Resuming remediation")}
                        disabled={actionLoading === `${plan.id}-resume`}
                        className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
                      >
                        <Play className="w-3.5 h-3.5" /> Resume
                      </button>
                    )}

                    {plan.status !== "closed" && (
                      <button
                        onClick={() => handleOverride(plan.id, "close", "Closed upon satisfactory faculty evaluation")}
                        disabled={actionLoading === `${plan.id}-close`}
                        className="px-3.5 py-1.5 bg-rose-950/80 hover:bg-rose-900 border border-rose-800/80 text-rose-300 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all"
                      >
                        <XCircle className="w-3.5 h-3.5" /> Manual Close
                      </button>
                    )}
                  </div>
                </div>

                {/* Steps Overview */}
                <div className="border-t border-neutral-800/80 pt-3">
                  <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">
                    Scaffolded Pathway ({plan.steps.length} Steps)
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
                    {plan.steps.map((st, sIdx) => (
                      <div
                        key={st.id}
                        className="p-2.5 bg-neutral-950/60 rounded-xl border border-neutral-800/60 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-neutral-500 uppercase font-mono">
                            Step {sIdx + 1}
                          </span>
                          <span
                            className={`text-[10px] font-semibold ${
                              st.completion_status === "completed"
                                ? "text-emerald-400"
                                : "text-neutral-500"
                            }`}
                          >
                            {st.completion_status}
                          </span>
                        </div>
                        <p className="font-medium text-neutral-200 truncate">{st.title}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Overrides Log */}
                {plan.faculty_override_reason && (
                  <div className="p-3 bg-neutral-950/90 rounded-xl border border-neutral-800/60 text-xs text-neutral-400">
                    <span className="font-semibold text-neutral-300">Faculty Log: </span>
                    {plan.faculty_override_reason}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
