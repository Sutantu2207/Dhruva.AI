"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { fetchRemediationPlan, startRemediationPlan, completeRemediationStep } from "@/lib/api";
import { RemediationPlan } from "@/lib/types";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Layers,
  Play,
  TrendingUp,
} from "lucide-react";

export default function StudentRemediationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [plan, setPlan] = useState<RemediationPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completingStepId, setCompletingStepId] = useState<string | null>(null);

  useEffect(() => {
    async function loadPlan() {
      try {
        setLoading(true);
        const data = await fetchRemediationPlan(id);
        setPlan(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load recovery plan details");
      } finally {
        setLoading(false);
      }
    }
    loadPlan();
  }, [id]);

  const handleStart = async () => {
    if (!plan) return;
    try {
      const updated = await startRemediationPlan(plan.id);
      setPlan(updated);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error starting plan");
    }
  };

  const handleCompleteStep = async (stepId: string) => {
    if (!plan) return;
    try {
      setCompletingStepId(stepId);
      await completeRemediationStep(plan.id, stepId, {
        score: 85,
        completion_percentage: 100,
      });
      // Refresh plan state
      const reloaded = await fetchRemediationPlan(plan.id);
      setPlan(reloaded);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error completing step");
    } finally {
      setCompletingStepId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center p-6">
        <div className="text-center space-y-3">
          <Clock className="w-8 h-8 mx-auto text-neutral-500 animate-spin" />
          <p className="text-neutral-400 text-sm">Loading recovery pathway...</p>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 flex items-center justify-center">
        <div className="max-w-md w-full p-6 bg-neutral-900 border border-neutral-800 rounded-2xl text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
          <h2 className="text-lg font-bold">Could not load remediation plan</h2>
          <p className="text-neutral-400 text-sm">{error || "Plan not found"}</p>
          <Link
            href="/remediation"
            className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-sm font-medium rounded-xl"
          >
            <ArrowLeft className="w-4 h-4" /> Back to My Plans
          </Link>
        </div>
      </div>
    );
  }

  const diagnosis = plan.diagnoses[0];
  const outcome = plan.outcomes[0];

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Navigation */}
        <Link
          href="/remediation"
          className="inline-flex items-center gap-2 text-sm text-neutral-400 hover:text-neutral-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> All Recovery Plans
        </Link>

        {/* Plan Header */}
        <div className="bg-neutral-900/60 border border-neutral-800 rounded-3xl p-8 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-indigo-950/80 text-indigo-400 border border-indigo-800">
                {plan.diagnosis_type.replace(/_/g, " ")}
              </span>
              <h1 className="text-3xl font-extrabold text-neutral-100 mt-2">
                Learning Recovery: {plan.target_concept_name || "Target Concept"}
              </h1>
            </div>

            {plan.status === "recommended" && (
              <button
                onClick={handleStart}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-semibold text-sm rounded-xl transition-all shadow-lg shadow-emerald-950/40"
              >
                <Play className="w-4 h-4 fill-current" /> Start Learning Recovery
              </button>
            )}
          </div>

          {/* Explainable Why Banner */}
          <div className="bg-neutral-950/80 border border-neutral-800/80 rounded-2xl p-5 space-y-2">
            <h2 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Why this was recommended</h2>
            <p className="text-neutral-300 text-sm leading-relaxed">{plan.diagnosis_reason}</p>
            {diagnosis && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-3 border-t border-neutral-800/60 text-xs">
                <div>
                  <span className="text-neutral-500 block">Baseline Mastery:</span>
                  <span className="font-semibold text-neutral-300">
                    {diagnosis.mastery_before !== null ? `${Math.round(Number(diagnosis.mastery_before) * 100)}%` : "Unassessed"}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-500 block">Memory Retention:</span>
                  <span className="font-semibold text-neutral-300">
                    {Math.round(Number(diagnosis.retention_before) * 100)}%
                  </span>
                </div>
                <div>
                  <span className="text-neutral-500 block">Prerequisite Gaps:</span>
                  <span className="font-semibold text-neutral-300">
                    {diagnosis.explanation_payload.prerequisite_blocking_count} detected
                  </span>
                </div>
                <div>
                  <span className="text-neutral-500 block">Assessment Failures:</span>
                  <span className="font-semibold text-neutral-300">{diagnosis.failure_count} logged</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Scaffolded Progression Steps */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold text-neutral-100">Scaffolded Recovery Steps</h2>
          </div>

          <div className="space-y-3">
            {plan.steps.map((step, idx) => {
              const isCompleted = step.completion_status === "completed";
              const isPending = step.completion_status === "pending";

              return (
                <div
                  key={step.id}
                  className={`border rounded-2xl p-5 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                    isCompleted
                      ? "bg-neutral-900/30 border-neutral-800/60 opacity-80"
                      : "bg-neutral-900/80 border-neutral-700/80 shadow-md"
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 ${
                        isCompleted
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : "bg-neutral-800 text-neutral-300"
                      }`}
                    >
                      {isCompleted ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : idx + 1}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-neutral-800 text-neutral-400">
                          Level {step.scaffold_level} • {step.step_type.replace(/_/g, " ")}
                        </span>
                        {step.required && (
                          <span className="text-[10px] text-amber-400 font-medium bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-900/40">
                            Required
                          </span>
                        )}
                      </div>
                      <h3 className="text-base font-semibold text-neutral-100 mt-1">{step.title}</h3>
                      {step.description && (
                        <p className="text-xs text-neutral-400 mt-1 leading-relaxed max-w-xl">
                          {step.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="shrink-0 flex items-center gap-3">
                    {isCompleted ? (
                      <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4" /> Completed
                      </span>
                    ) : (
                      <button
                        onClick={() => handleCompleteStep(step.id)}
                        disabled={completingStepId === step.id || plan.status === "recommended"}
                        className="px-4 py-2 bg-neutral-100 hover:bg-white text-neutral-950 text-xs font-bold rounded-xl transition-all disabled:opacity-50"
                      >
                        {completingStepId === step.id
                          ? "Recording..."
                          : isPending
                          ? "Complete Step"
                          : "In Progress"}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Closed Loop Outcome (if evaluated) */}
        {outcome && (
          <div className="bg-emerald-950/30 border border-emerald-800/60 rounded-3xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-emerald-400">
              <TrendingUp className="w-5 h-5" />
              <h2 className="text-lg font-bold">Closed-Loop Measured Outcome</h2>
            </div>
            <p className="text-xs text-neutral-300 leading-relaxed">{outcome.closure_reason}</p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-neutral-900/60 rounded-2xl border border-neutral-800/60 text-xs">
              <div>
                <span className="text-neutral-500 block">Outcome Classification:</span>
                <span className="font-bold text-emerald-300 uppercase tracking-wide">
                  {outcome.outcome_status.replace(/_/g, " ")}
                </span>
              </div>
              <div>
                <span className="text-neutral-500 block">Observed Delta:</span>
                <span className="font-bold text-emerald-300">
                  {Number(outcome.improvement_delta) >= 0 ? `+${outcome.improvement_delta}` : outcome.improvement_delta}
                </span>
              </div>
              <div>
                <span className="text-neutral-500 block">Post-Remediation Mastery:</span>
                <span className="font-bold text-neutral-200">
                  {outcome.mastery_after !== null ? `${Math.round(Number(outcome.mastery_after) * 100)}%` : "N/A"}
                </span>
              </div>
              <div>
                <span className="text-neutral-500 block">Closure Decision:</span>
                <span className="font-bold text-neutral-200">{outcome.closure_decision}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
