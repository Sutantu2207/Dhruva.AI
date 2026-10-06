"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  UserCheck,
  RefreshCw,
  Search,
  Check,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  fetchFacultyDashboardAnalytics,
  scanInterventionSignals,
  acknowledgeInterventionSignal,
  dismissInterventionSignal,
  convertSignalToIntervention,
} from "@/lib/api";
import type { AcademicInterventionSignal } from "@/lib/types";

export default function FacultyInterventionsPage() {
  const [signals, setSignals] = React.useState<AcademicInterventionSignal[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [scanning, setScanning] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [search, setSearch] = React.useState("");

  // Dismiss modal state
  const [dismissSignalId, setDismissSignalId] = React.useState<string | null>(null);
  const [dismissReason, setDismissReason] = React.useState("");
  const [actionSuccess, setActionSuccess] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    fetchFacultyDashboardAnalytics()
      .then((res) => {
        if (active) {
          setSignals(res.urgent_signals || []);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load signals.");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const refreshSignals = () => {
    setLoading(true);
    fetchFacultyDashboardAnalytics()
      .then((res) => {
        setSignals(res.urgent_signals || []);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load signals.");
        setLoading(false);
      });
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await scanInterventionSignals();
      setActionSuccess(`Scanned cohort: ${res.signals_generated_count} new academic distress signals recorded.`);
      refreshSignals();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Signal scan failed.");
    } finally {
      setScanning(false);
    }
  };

  const handleAcknowledge = async (signalId: string) => {
    try {
      await acknowledgeInterventionSignal(signalId, { notes: "Acknowledged by faculty instructor" });
      setActionSuccess("Signal acknowledged.");
      refreshSignals();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to acknowledge.");
    }
  };

  const handleDismiss = async () => {
    if (!dismissSignalId || !dismissReason) return;
    try {
      await dismissInterventionSignal(dismissSignalId, { reason: dismissReason });
      setActionSuccess("Signal dismissed with audited justification.");
      setDismissSignalId(null);
      setDismissReason("");
      refreshSignals();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to dismiss.");
    }
  };

  const handleConvert = async (signalId: string) => {
    try {
      await convertSignalToIntervention(signalId, {
        category: "academic_support",
        priority: "high",
        action_plan: "Schedule 1-on-1 concept remediation review.",
      });
      setActionSuccess("Elevated to formal Student Intervention Plan.");
      refreshSignals();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to elevate.");
    }
  };

  const filteredSignals = signals.filter(
    (s) =>
      (s.student_name || "").toLowerCase().includes(search.toLowerCase()) ||
      s.title.toLowerCase().includes(search.toLowerCase()) ||
      (s.course_code || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <Link href="/faculty" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 mb-2">
            <ArrowLeft className="h-3 w-3" />
            Back to Faculty Dashboard
          </Link>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-amber-700 border-amber-200 bg-amber-50 text-xs">
              Deterministic Early Intervention Engine
            </Badge>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Academic Support & Early Intervention Hub
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Pure observable distress facts without psychological speculation or unsupported predictions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={handleScan}
            disabled={scanning}
            className="bg-amber-600 hover:bg-amber-700 text-white gap-2 text-xs h-9"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${scanning ? "animate-spin" : ""}`} />
            {scanning ? "Scanning Roster..." : "Run Deterministic Scan"}
          </Button>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Search Bar */}
      <div className="flex items-center gap-2 max-w-md">
        <div className="relative w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search signals by student or course..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-9 text-xs"
          />
        </div>
      </div>

      {/* Signals List */}
      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-amber-600 border-t-transparent" />
        </div>
      ) : error ? (
        <Card className="border-red-200 bg-red-50 p-6 text-center text-xs text-red-700 font-medium">
          {error}
        </Card>
      ) : filteredSignals.length === 0 ? (
        <Card className="border-slate-200 p-12 text-center space-y-2">
          <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
          <p className="text-sm font-semibold text-slate-800">Zero Active Distress Signals</p>
          <p className="text-xs text-slate-500">
            No students currently exhibit repeated assessment failures, low concept mastery, or overdue learning reviews.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSignals.map((sig) => (
            <Card key={sig.id} className="border-slate-200 shadow-sm flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <Badge
                    variant="outline"
                    className={`text-[10px] uppercase font-bold ${
                      sig.severity === "urgent"
                        ? "border-red-300 bg-red-50 text-red-700"
                        : sig.severity === "high"
                        ? "border-amber-300 bg-amber-50 text-amber-700"
                        : "border-slate-200 text-slate-600"
                    }`}
                  >
                    {sig.severity} Severity
                  </Badge>
                  <span className="text-[11px] font-mono text-slate-400">
                    {new Date(sig.detected_at).toLocaleDateString()}
                  </span>
                </div>
                <CardTitle className="text-base text-slate-900 mt-2">{sig.title}</CardTitle>
                <CardDescription className="text-xs">
                  Student: <strong className="text-slate-800">{sig.student_name}</strong> ({sig.enrollment_number})
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-0">
                {/* Observable Evidence */}
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs space-y-1">
                  <p className="font-semibold text-slate-700 text-[11px] uppercase tracking-wider">Observable Facts:</p>
                  {Object.entries(sig.evidence_data || {}).map(([key, val]) => (
                    <div key={key} className="flex justify-between text-slate-600">
                      <span className="capitalize">{key.replace(/_/g, " ")}:</span>
                      <span className="font-mono font-medium text-slate-900">{String(val)}</span>
                    </div>
                  ))}
                  <p className="text-[11px] text-indigo-700 font-medium pt-1 mt-1 border-t border-slate-200/60">
                    Recommended: {sig.recommended_action}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
                  {sig.status === "detected" && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs h-7 gap-1 border-blue-200 text-blue-700 hover:bg-blue-50"
                      onClick={() => handleAcknowledge(sig.id)}
                    >
                      <Check className="h-3 w-3" />
                      Acknowledge
                    </Button>
                  )}
                  <Button
                    size="sm"
                    className="text-xs h-7 gap-1 bg-indigo-600 hover:bg-indigo-700 text-white"
                    onClick={() => handleConvert(sig.id)}
                  >
                    <UserCheck className="h-3 w-3" />
                    Formal Intervention
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-xs h-7 text-slate-400 hover:text-slate-700"
                    onClick={() => setDismissSignalId(sig.id)}
                  >
                    Dismiss
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Dismiss Dialog */}
      {dismissSignalId && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-md border-slate-200 shadow-xl bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Dismiss Intervention Signal</CardTitle>
              <CardDescription className="text-xs">
                Audited action. Provide a verifiable reason for dismissing this academic distress signal.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <textarea
                rows={3}
                className="w-full text-xs p-2 border border-slate-200 rounded-lg focus:outline-indigo-500"
                placeholder="e.g. Student provided valid medical waiver for missed assessments..."
                value={dismissReason}
                onChange={(e) => setDismissReason(e.target.value)}
              />
              <div className="flex justify-end gap-2">
                <Button size="sm" variant="outline" onClick={() => setDismissSignalId(null)}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="bg-red-600 hover:bg-red-700 text-white"
                  onClick={handleDismiss}
                  disabled={!dismissReason.trim()}
                >
                  Confirm Dismissal
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
