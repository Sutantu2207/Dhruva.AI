"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchSystemHealthStatus } from "@/lib/api";
import { SystemHealthStatus } from "@/lib/types";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Database,
  Cpu,
  RefreshCw,
  Server,
  Zap,
} from "lucide-react";

export default function PlatformStatusPage() {
  const [health, setHealth] = useState<SystemHealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchSystemHealthStatus();
      setHealth(data);
    } catch (err) {
      console.error("Health probe error:", err);
      setError("Unable to communicate with platform operational gateway.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const getStatusBadge = (status?: string) => {
    if (status === "healthy" || status === "alive") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-400 text-xs font-medium">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Operational
        </span>
      );
    }
    if (status === "degraded") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-950/80 border border-amber-800 text-amber-400 text-xs font-medium">
          <AlertTriangle className="w-3.5 h-3.5" />
          Degraded
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-950/80 border border-rose-800 text-rose-400 text-xs font-medium">
        <XCircle className="w-3.5 h-3.5" />
        Outage / Offline
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-800 text-emerald-400 flex items-center justify-center font-bold">
              Δ
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-100">
                Dhruva.AI System Status
              </h1>
              <p className="text-xs text-neutral-400 mt-0.5">
                Real-time operational health probes across deterministic core engines and infrastructure.
              </p>
            </div>
          </div>
          <button
            onClick={() => loadStatus()}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg border border-neutral-800 bg-neutral-900 text-xs text-neutral-300 hover:bg-neutral-800 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Global Overall Status Banner */}
        <div className="p-6 rounded-2xl bg-neutral-900/60 border border-neutral-800 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className={`w-4 h-4 rounded-full ${
                health?.status === "healthy"
                  ? "bg-emerald-400 animate-pulse"
                  : health?.status === "degraded"
                  ? "bg-amber-400 animate-pulse"
                  : "bg-rose-500"
              }`}
            />
            <div>
              <div className="text-sm font-semibold text-neutral-200">
                {health?.status === "healthy"
                  ? "All Core Academic Engines & Services Operational"
                  : health?.status === "degraded"
                  ? "Core Operational — Auxiliary Acceleration Degraded"
                  : "System Connectivity Error"}
              </div>
              <div className="text-xs text-neutral-400 mt-0.5">
                Environment: {health?.environment || "production"} · Build: v{health?.version || "0.1.0"}
              </div>
            </div>
          </div>
          <div>{getStatusBadge(health?.status)}</div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Sub-system Status Matrix */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* PostgreSQL 16 + pgvector */}
          <div className="p-5 rounded-xl bg-neutral-900/40 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-neutral-200 text-xs font-semibold">
                <Database className="w-4 h-4 text-emerald-400" />
                <span>Primary Academic Database</span>
              </div>
              {getStatusBadge(health?.database?.status)}
            </div>
            <p className="text-xs text-neutral-400 leading-relaxed">
              PostgreSQL 16 with pgvector extension. Authoritative source of academic truth, RBAC, curriculum, and knowledge states.
            </p>
            <div className="text-[11px] text-neutral-400 font-mono">
              Driver: asyncpg · Connection Pooling: Active
            </div>
          </div>

          {/* Redis Distributed Coordinator */}
          <div className="p-5 rounded-xl bg-neutral-900/40 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-neutral-200 text-xs font-semibold">
                <Zap className="w-4 h-4 text-amber-400" />
                <span>Distributed Coordination & Caching</span>
              </div>
              {getStatusBadge(health?.redis?.status)}
            </div>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Redis token bucket coordinator for distributed rate limiting and transient caching. Gracefully degrades to in-memory fallback.
            </p>
            <div className="text-[11px] text-neutral-400 font-mono">
              Mode: {health?.redis?.mode || "connected"}
            </div>
          </div>

          {/* Background Job Worker & Queue */}
          <div className="p-5 rounded-xl bg-neutral-900/40 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-neutral-200 text-xs font-semibold">
                <Server className="w-4 h-4 text-cyan-400" />
                <span>Background Worker & Scheduler</span>
              </div>
              {getStatusBadge(health?.workers?.is_running ? "healthy" : "degraded")}
            </div>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Asynchronous worker processing retention decay updates, periodic token cleanup, and notification dispatches.
            </p>
            <div className="text-[11px] text-neutral-400 font-mono flex justify-between">
              <span>Jobs Processed: {health?.workers?.completed ?? 0}</span>
              <span>Queue Depth: {health?.workers?.queue_depth ?? 0}</span>
            </div>
          </div>

          {/* AI Orchestration Gateway */}
          <div className="p-5 rounded-xl bg-neutral-900/40 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-neutral-200 text-xs font-semibold">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span>AI Orchestration Gateway</span>
              </div>
              {getStatusBadge(health?.ai_provider?.status)}
            </div>
            <p className="text-xs text-neutral-400 leading-relaxed">
              Google Gemini controlled natural language explainer. Strictly assistive; deterministic engines remain authoritative.
            </p>
            <div className="text-[11px] text-neutral-400 font-mono">
              Model: {health?.ai_provider?.model || "gemini-2.5-flash"} · Status: {health?.ai_provider?.status || "ready"}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 rounded-xl bg-neutral-900/20 border border-neutral-800 flex items-center justify-between text-xs text-neutral-400">
          <Link href="/ai/trust" className="hover:text-emerald-400 transition-colors">
            AI Trust & Transparency Manifest →
          </Link>
          <span>Probe Timestamp: {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : "—"}</span>
        </div>
      </div>
    </div>
  );
}
