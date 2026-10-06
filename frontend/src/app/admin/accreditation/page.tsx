"use client";

import React, { useState } from "react";
import Link from "next/link";
import { generateAccreditationEvidence } from "@/lib/api";
import { AccreditationEvidence } from "@/lib/types";
import {
  AlertCircle,
  ArrowLeft,
  FileCheck,
  ShieldAlert,
} from "lucide-react";

export default function AdminAccreditationPage() {
  const [framework, setFramework] = useState("NAAC");
  const [criterion, setCriterion] = useState("2.2.1");
  const [evidence, setEvidence] = useState<AccreditationEvidence | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await generateAccreditationEvidence(framework, criterion);
      setEvidence(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to synthesize evidence snapshot");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <Link
            href="/admin/remediation"
            className="inline-flex items-center gap-2 text-xs text-neutral-400 hover:text-neutral-200 transition-colors mb-3"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Remediation Intelligence
          </Link>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-950/80 border border-blue-800 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <FileCheck className="w-3.5 h-3.5" />
            Accreditation & Audit Evidence Mapping
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-neutral-100">
            Institutional Audit Evidence Generator
          </h1>
          <p className="text-neutral-400 text-sm mt-1 max-w-2xl leading-relaxed">
            Extracts deterministic evidence snapshots mapped directly to national criteria (NAAC Criteria 2, NBA Criterion 3) demonstrating student learning outcomes and remedial support.
          </p>
        </div>

        {/* Disclaimer Banner */}
        <div className="p-4 bg-amber-950/40 border border-amber-800/80 rounded-2xl flex items-start gap-3 text-xs text-amber-300">
          <ShieldAlert className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
          <div>
            <span className="font-bold block text-amber-200">Audit Preparation Only</span>
            Dhruva.AI maps deterministic platform data to configured accreditation criteria for institutional review. This does NOT constitute an official accreditation award or certification claim.
          </div>
        </div>

        {/* Request Form */}
        <form
          onSubmit={handleGenerate}
          className="p-6 bg-neutral-900/60 border border-neutral-800 rounded-3xl space-y-4"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-neutral-300 uppercase tracking-wider block mb-1">
                Accreditation Framework
              </label>
              <select
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
                className="w-full bg-neutral-950 border border-neutral-700 text-neutral-100 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              >
                <option value="NAAC">NAAC (National Assessment and Accreditation Council)</option>
                <option value="NBA">NBA (National Board of Accreditation)</option>
                <option value="NIRF">NIRF (National Institutional Ranking Framework)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-neutral-300 uppercase tracking-wider block mb-1">
                Criterion Code
              </label>
              <input
                type="text"
                value={criterion}
                onChange={(e) => setCriterion(e.target.value)}
                placeholder="e.g. 2.2.1 or CO-PO Attainment"
                className="w-full bg-neutral-950 border border-neutral-700 text-neutral-100 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-semibold text-xs rounded-xl transition-all shadow-md flex items-center justify-center gap-2"
          >
            {loading ? "Synthesizing Evidence..." : "Generate Audit Evidence Snapshot"}
          </button>
        </form>

        {error && (
          <div className="p-6 bg-rose-950/40 border border-rose-800 rounded-2xl text-rose-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-400" />
            <div>
              <p className="font-semibold text-rose-200">Evidence generation failed</p>
              <p className="mt-1 opacity-90">{error}</p>
            </div>
          </div>
        )}

        {/* Generated Snapshot Display */}
        {evidence && (
          <div className="p-6 bg-neutral-900/80 border border-neutral-700 rounded-3xl space-y-6">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
              <div>
                <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">
                  {evidence.framework} • Criterion {evidence.criterion}
                </span>
                <h2 className="text-lg font-bold text-neutral-100 mt-0.5">
                  {evidence.metric_payload.metric_title}
                </h2>
              </div>
              <span className="px-3 py-1 bg-neutral-800 text-neutral-300 rounded-xl text-xs font-mono font-bold">
                {evidence.metric_code}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800">
                <span className="text-neutral-500 block">Total Interventions:</span>
                <span className="text-base font-bold text-neutral-100">
                  {evidence.metric_payload.evidence_indicators.total_remediation_interventions}
                </span>
              </div>

              <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800">
                <span className="text-neutral-500 block">Completed Interventions:</span>
                <span className="text-base font-bold text-emerald-400">
                  {evidence.metric_payload.evidence_indicators.successfully_completed_interventions}
                </span>
              </div>

              <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800">
                <span className="text-neutral-500 block">Completion Rate:</span>
                <span className="text-base font-bold text-neutral-100">
                  {Math.round(evidence.metric_payload.evidence_indicators.completion_rate * 100)}%
                </span>
              </div>

              <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800">
                <span className="text-neutral-500 block">Demonstrated Gains:</span>
                <span className="text-base font-bold text-blue-400">
                  {evidence.metric_payload.evidence_indicators.documented_learning_improvements}
                </span>
              </div>

              <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800">
                <span className="text-neutral-500 block">Gain Success Rate:</span>
                <span className="text-base font-bold text-neutral-100">
                  {Math.round(evidence.metric_payload.evidence_indicators.improvement_success_rate * 100)}%
                </span>
              </div>

              <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800">
                <span className="text-neutral-500 block">Average Mastery Gain:</span>
                <span className="text-base font-bold text-purple-400">
                  +{evidence.metric_payload.evidence_indicators.average_mastery_gain.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="p-4 bg-neutral-950 rounded-2xl border border-neutral-800/80 text-xs text-neutral-400 space-y-1">
              <span className="font-semibold text-neutral-300 block">Formal Compliance Claim:</span>
              <p className="italic">{evidence.metric_payload.compliance_claim}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
