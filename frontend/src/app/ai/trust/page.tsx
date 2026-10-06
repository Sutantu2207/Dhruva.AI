"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAITrustManifest } from "@/lib/api";
import { AITrustManifest } from "@/lib/types";
import {
  ShieldCheck,
  Lock,
  Database,
  Cpu,
  ArrowLeft,
  CheckCircle2,
  EyeOff,
  Activity,
} from "lucide-react";

export default function AITrustCenterPage() {
  const [manifest, setManifest] = useState<AITrustManifest | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchAITrustManifest();
        setManifest(data);
      } catch (e) {
        console.error("Failed to load trust manifest:", e);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Navigation & Header */}
        <div>
          <Link
            href="/ai"
            className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-emerald-400 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to AI Mentor
          </Link>

          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-800 text-emerald-400 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-100">
                Dhruva AI Trust & Transparency Manifest
              </h1>
              <p className="text-xs text-neutral-400 mt-0.5">
                Constitutional boundaries, privacy guarantees, and deterministic source-of-truth invariants.
              </p>
            </div>
          </div>
        </div>

        {/* Core Product Principle Banner */}
        <div className="p-5 rounded-xl bg-gradient-to-r from-emerald-950/40 via-neutral-900 to-neutral-900 border border-emerald-800/60 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4" />
            Core Architectural Invariant
          </div>
          <p className="text-xs text-neutral-300 leading-relaxed">
            {manifest?.product_principle ||
              "Dhruva.AI is a real production-oriented academic operating system. AI is strictly an interface, explainer, tutor, and assistive copilot. The deterministic engines remain the sole source of academic truth."}
          </p>
        </div>

        {/* Authority Boundaries: What AI Can and Cannot Do */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-3">
            <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs uppercase tracking-wider">
              <Lock className="w-4 h-4" />
              What AI Cannot Do (Forbidden Authority)
            </div>
            <ul className="text-xs text-neutral-400 space-y-2 leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                Cannot calculate or alter concept mastery scores.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                Cannot assign, modify, or curve student grades.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                Cannot verify portfolio project evidence independently.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                Cannot calculate career readiness or placement eligibility.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                Cannot publish course curriculum or assessment questions directly.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-rose-400 font-bold">✕</span>
                Cannot query raw database tables or bypass RBAC authorization.
              </li>
            </ul>
          </div>

          <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs uppercase tracking-wider">
              <Cpu className="w-4 h-4" />
              What AI Can Do (Grounded Assistance)
            </div>
            <ul className="text-xs text-neutral-400 space-y-2 leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">✓</span>
                Explain concepts using verified course lessons and syllabus.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">✓</span>
                Explain why a student is struggling based on deterministic prerequisite checks.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">✓</span>
                Walk students through assigned remediation recovery pathways.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">✓</span>
                Conduct guided Socratic questioning and practice drills.
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">✓</span>
                Assist faculty with drafting questions, rubrics, and lesson outlines (marked AI DRAFT).
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold">✓</span>
                Provide citations linked directly to verified Dhruva curriculum chunks.
              </li>
            </ul>
          </div>
        </div>

        {/* Deterministic Foundations (Domain 1 - 10) */}
        <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-4">
          <div className="flex items-center gap-2 text-neutral-200 font-semibold text-xs uppercase tracking-wider">
            <Database className="w-4 h-4 text-emerald-400" />
            Deterministic Sources of Truth
          </div>
          <p className="text-xs text-neutral-400">
            Whenever Gemini is invoked, trusted backend resolvers consult these mathematical engines before inference:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2.5 text-xs">
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 1</div>
              <div className="text-[11px] text-neutral-400">Identity, JWT & RBAC</div>
            </div>
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 2 & 2.5</div>
              <div className="text-[11px] text-neutral-400">National Academic Catalog</div>
            </div>
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 4</div>
              <div className="text-[11px] text-neutral-400">Curriculum & Versioned Lessons</div>
            </div>
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 5</div>
              <div className="text-[11px] text-neutral-400">Assessments & Deterministic Scoring</div>
            </div>
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 6</div>
              <div className="text-[11px] text-neutral-400">Bayesian Mastery & SM-2 Scheduling</div>
            </div>
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 7 & 8</div>
              <div className="text-[11px] text-neutral-400">Skill Graph & Verified Evidence</div>
            </div>
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 9</div>
              <div className="text-[11px] text-neutral-400">Institutional & HOD Analytics</div>
            </div>
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 10</div>
              <div className="text-[11px] text-neutral-400">Closed-Loop Adaptive Remediation</div>
            </div>
            <div className="p-2.5 rounded bg-neutral-950/60 border border-neutral-800">
              <div className="font-semibold text-neutral-200">Domain 11</div>
              <div className="text-[11px] text-emerald-400">Controlled Intelligence Layer</div>
            </div>
          </div>
        </div>

        {/* Privacy & Prompt Injection Protection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-3">
            <div className="flex items-center gap-2 text-neutral-200 font-semibold text-xs uppercase tracking-wider">
              <EyeOff className="w-4 h-4 text-emerald-400" />
              PII Redaction & Data Minimization
            </div>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Dhruva.AI scrubs email addresses, phone numbers, roll numbers, authentication tokens, and internal database keys before sending any payload to model providers. Gemini never sees raw database tables.
            </p>
          </div>

          <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-3">
            <div className="flex items-center gap-2 text-neutral-200 font-semibold text-xs uppercase tracking-wider">
              <Activity className="w-4 h-4 text-emerald-400" />
              Prompt Injection Defense
            </div>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Every message is screened before generation for instruction overrides, system prompt extraction, and credential exfiltration. Attempts are immediately blocked, audited, and logged.
            </p>
          </div>
        </div>

        {/* System Version Footer */}
        <div className="p-4 rounded-lg bg-neutral-900/30 border border-neutral-800 text-[11px] text-neutral-400 flex items-center justify-between font-mono">
          <span>ALGORITHM VERSION: {manifest?.algorithm_version || "ai-orchestration-v1.0.0"}</span>
          <span>POSTGRESQL 16 & PGVECTOR READY</span>
        </div>
      </div>
    </div>
  );
}
