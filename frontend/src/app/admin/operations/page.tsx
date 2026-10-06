"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchAdminOperationsOverview,
  fetchWorkerJobs,
} from "@/lib/api";
import {
  AdminOperationsOverview,
  BackgroundJobRecord,
} from "@/lib/types";
import {
  Server,
  Activity,
  Clock,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";

export default function AdminOperationsDashboardPage() {
  const [overview, setOverview] = useState<AdminOperationsOverview | null>(null);
  const [jobs, setJobs] = useState<BackgroundJobRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = React.useCallback(async () => {
    try {
      setLoading(true);
      const [ov, jb] = await Promise.all([
        fetchAdminOperationsOverview().catch(() => null),
        fetchWorkerJobs(15).catch(() => []),
      ]);
      setOverview(ov);
      setJobs(jb);
    } catch (err) {
      console.error("Operations fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-6 md:p-12 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-950/80 border border-amber-800 text-amber-400 flex items-center justify-center font-bold">
              Σ
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-100">
                Institutional Operations & Infrastructure
              </h1>
              <p className="text-xs text-neutral-400 mt-0.5">
                Live observability over background workers, maintenance schedulers, Redis coordination, and feature flags.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/status"
              className="px-3 py-1.5 rounded-lg border border-neutral-800 bg-neutral-900 text-xs text-neutral-300 hover:bg-neutral-800 transition-colors flex items-center gap-1.5"
            >
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              <span>Public Status</span>
            </Link>
            <button
              onClick={() => loadData()}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg border border-neutral-800 bg-neutral-900 text-xs text-neutral-300 hover:bg-neutral-800 transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Top KPI Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-1">
            <div className="text-[11px] uppercase font-bold text-neutral-400 tracking-wider">
              Environment
            </div>
            <div className="text-lg font-bold text-neutral-100 uppercase">
              {overview?.environment || "production"}
            </div>
            <div className="text-[10px] text-emerald-400 font-mono">Fail-fast secret checks active</div>
          </div>

          <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-1">
            <div className="text-[11px] uppercase font-bold text-neutral-400 tracking-wider">
              Background Worker
            </div>
            <div className="text-lg font-bold text-neutral-100">
              {overview?.worker_metrics?.is_running ? "ONLINE" : "STANDBY"}
            </div>
            <div className="text-[10px] text-neutral-400 font-mono">
              Queue depth: {overview?.worker_metrics?.queue_depth ?? 0} · Done: {overview?.worker_metrics?.completed ?? 0}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-1">
            <div className="text-[11px] uppercase font-bold text-neutral-400 tracking-wider">
              Maintenance Scheduler
            </div>
            <div className="text-lg font-bold text-neutral-100">
              {overview?.scheduler_status?.is_running ? "ACTIVE" : "STANDBY"}
            </div>
            <div className="text-[10px] text-neutral-400 font-mono">
              Cadence: Asia/Kolkata
            </div>
          </div>

          <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-1">
            <div className="text-[11px] uppercase font-bold text-neutral-400 tracking-wider">
              Redis Coordinator
            </div>
            <div className="text-lg font-bold text-neutral-100">
              {overview?.redis_status?.connected ? "CONNECTED" : "IN-MEMORY FALLBACK"}
            </div>
            <div className="text-[10px] text-neutral-400 font-mono">
              Abuse rate limiter: Active
            </div>
          </div>
        </div>

        {/* Server-Authoritative Feature Flags */}
        <div className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-300">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Server-Authoritative Feature Flags</span>
            </div>
            <span className="text-[10px] text-neutral-400 font-mono">Immutable from Client</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-2.5 text-xs">
            {overview?.feature_flags &&
              Object.entries(overview.feature_flags).map(([key, val]) => (
                <div
                  key={key}
                  className="p-3 rounded-lg bg-neutral-950/60 border border-neutral-800 flex items-center justify-between"
                >
                  <span className="font-mono text-neutral-300 text-[11px]">{key}</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      val
                        ? "bg-emerald-950 border border-emerald-800 text-emerald-400"
                        : "bg-neutral-900 border border-neutral-800 text-neutral-400"
                    }`}
                  >
                    {val ? "ENABLED" : "DISABLED"}
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Scheduled Maintenance Tasks */}
        <div className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-300">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Scheduled Academic Maintenance Cadences</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            {overview?.scheduler_status?.scheduled_tasks.map((task) => (
              <div key={task.name} className="p-3.5 rounded-xl bg-neutral-950/80 border border-neutral-800 space-y-1">
                <div className="font-semibold text-neutral-200">{task.name}</div>
                <div className="text-[11px] text-neutral-400 font-mono">Interval: {task.interval}</div>
                <div className="text-[10px] text-neutral-400 font-mono">
                  Last Run: {task.last_run ? new Date(task.last_run).toLocaleTimeString() : "Pending"}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Worker Jobs Table */}
        <div className="p-5 rounded-2xl bg-neutral-900/40 border border-neutral-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-300">
              <Server className="w-4 h-4 text-indigo-400" />
              <span>Background Job Execution Queue</span>
            </div>
            <span className="text-[10px] text-neutral-400 font-mono">Idempotent Worker Queue</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-neutral-800 text-neutral-400 font-mono text-[11px]">
                <tr>
                  <th className="pb-2">Job Type</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Attempts</th>
                  <th className="pb-2">Enqueued At</th>
                  <th className="pb-2">Completed At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800/60 text-neutral-300">
                {jobs.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-neutral-400">
                      No background jobs processed yet.
                    </td>
                  </tr>
                )}
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td className="py-2.5 font-medium">{job.name}</td>
                    <td className="py-2.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                          job.status === "COMPLETED"
                            ? "bg-emerald-950 border border-emerald-800 text-emerald-400"
                            : job.status === "FAILED"
                            ? "bg-rose-950 border border-rose-800 text-rose-400"
                            : "bg-cyan-950 border border-cyan-800 text-cyan-400"
                        }`}
                      >
                        {job.status}
                      </span>
                    </td>
                    <td className="py-2.5 font-mono">{job.attempts}</td>
                    <td className="py-2.5 text-neutral-400 text-[11px]">
                      {new Date(job.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 text-neutral-400 text-[11px]">
                      {job.completed_at ? new Date(job.completed_at).toLocaleTimeString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
