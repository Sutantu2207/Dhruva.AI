"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { StatusPill } from "@/components/layout/status-pill";
import { fetchSystemHealth, fetchSystemArchitecture } from "@/lib/api";
import { SystemHealth, SystemArchitecture } from "@/lib/types";
import {
  CheckCircle2,
  Server,
  Layers,
  Users,
  Calculator,
  RefreshCw,
  Terminal,
} from "lucide-react";

export default function FoundationConsolePage() {
  const [health, setHealth] = React.useState<SystemHealth | null>(null);
  const [architecture, setArchitecture] = React.useState<SystemArchitecture | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Live Deterministic SM-2 Spaced Repetition Interactive Verification State
  const [grade, setGrade] = React.useState<number>(4);
  const [reps, setReps] = React.useState<number>(1);
  const [interval, setInterval] = React.useState<number>(1);
  const [ef, setEf] = React.useState<number>(2.5);

  const sm2Result = React.useMemo(() => {
    // Pure deterministic SM-2 computation
    const delta = 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02);
    const newEf = Math.round(Math.max(1.3, ef + delta) * 10000) / 10000;
    let newReps: number;
    let newInterval: number;

    if (grade < 3) {
      newReps = 0;
      newInterval = 1;
    } else {
      if (reps === 0) newInterval = 1;
      else if (reps === 1) newInterval = 6;
      else newInterval = Math.round(interval * newEf);
      newReps = reps + 1;
    }

    return {
      newInterval,
      newReps,
      newEf,
    };
  }, [grade, reps, interval, ef]);

  const loadStatus = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [h, a] = await Promise.all([fetchSystemHealth(), fetchSystemArchitecture()]);
      setHealth(h);
      setArchitecture(a);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Backend connection pending";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    let isCancelled = false;

    async function checkBackend() {
      try {
        const [h, a] = await Promise.all([fetchSystemHealth(), fetchSystemArchitecture()]);
        if (!isCancelled) {
          setHealth(h);
          setArchitecture(a);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          const msg = err instanceof Error ? err.message : "Backend connection pending";
          setError(msg);
        }
      }
    }

    checkBackend();

    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Platform Title & Real-Time Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-6 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Dhruva.AI System Foundation
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Production Architecture Control Plane & Verification Console
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <StatusPill isOnline={!!health} statusText={health ? `API v${health.version} Online` : undefined} />
          <Button
            variant="outline"
            size="sm"
            onClick={loadStatus}
            isLoading={isLoading}
            className="flex items-center space-x-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Verify Live API</span>
          </Button>
        </div>
      </div>

      {/* Backend Status Notice */}
      {error && (
        <Alert variant="warning">
          <AlertTitle>Backend Service Notice</AlertTitle>
          <AlertDescription>
            Could not connect to FastAPI backend at <code className="font-mono text-xs">http://localhost:8000/api/v1</code>.
            Start the backend server using{" "}
            <code className="bg-amber-100 dark:bg-amber-900/50 px-1 py-0.5 rounded font-mono text-xs">
              uvicorn app.main:app --app-dir backend --reload --port 8000
            </code>{" "}
            to establish live API connectivity.
          </AlertDescription>
        </Alert>
      )}

      {/* Hybrid Architecture Principle Banner */}
      <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-6 dark:border-indigo-900/40 dark:bg-indigo-950/20 space-y-3">
        <div className="flex items-center space-x-2">
          <Badge variant="default" className="font-mono text-xs">RESEARCH FOUNDATION</Badge>
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Deterministic-First Hybrid Model
          </span>
        </div>
        <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          In Dhruva.AI, <strong>deterministic application code is the single source of truth</strong> for assessment scores, career recommendations, mastery levels, SM-2 scheduling, and RBAC authorization. The Large Language Model (Gemini) is deployed strictly in an auxiliary, advisory, and tutoring capacity behind mandatory PII privacy scrubbing guardrails.
        </p>
      </div>

      {/* Tabs for Console Sections */}
      <Tabs defaultValue="architecture" className="w-full">
        <TabsList className="grid w-full grid-cols-4 max-w-xl">
          <TabsTrigger value="architecture" className="flex items-center space-x-1.5">
            <Layers className="h-3.5 w-3.5" />
            <span>Architecture</span>
          </TabsTrigger>
          <TabsTrigger value="sm2" className="flex items-center space-x-1.5">
            <Calculator className="h-3.5 w-3.5" />
            <span>SM-2 Engine</span>
          </TabsTrigger>
          <TabsTrigger value="rbac" className="flex items-center space-x-1.5">
            <Users className="h-3.5 w-3.5" />
            <span>RBAC Matrix</span>
          </TabsTrigger>
          <TabsTrigger value="runbook" className="flex items-center space-x-1.5">
            <Terminal className="h-3.5 w-3.5" />
            <span>Dev Runbook</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Architecture Overview */}
        <TabsContent value="architecture" className="space-y-6 pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Server className="h-4 w-4 text-emerald-600" />
                    <span>Deterministic Core Engines</span>
                  </CardTitle>
                  <Badge variant="success">Source of Truth</Badge>
                </div>
                <CardDescription>
                  Verified mathematical engines running in FastAPI backend
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2 text-sm">
                  {[
                    { name: "Assessment Engine", desc: "Rubric weighting, penalty rules, exact percentage scoring" },
                    { name: "Concept Mastery Graph", desc: "Exponential moving average & 4-tier mastery thresholds" },
                    { name: "SuperMemo SM-2", desc: "Exact recurrence relation for repetition and interval scheduling" },
                    { name: "Career Fit & Skill-Gap", desc: "Multi-dimensional skill gap differential & evidence confidence" },
                    { name: "Structured Audit Log", desc: "Immutable SHA-256 payload integrity hash trail" },
                  ].map((engine) => (
                    <div key={engine.name} className="flex items-start space-x-2 p-2 rounded-md bg-slate-50 dark:bg-slate-800/50">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <div className="font-medium text-slate-800 dark:text-slate-200">{engine.name}</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">{engine.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Layers className="h-4 w-4 text-indigo-600" />
                    <span>AI Orchestration Layer</span>
                  </CardTitle>
                  <Badge variant="default">Controlled Gateway</Badge>
                </div>
                <CardDescription>
                  Google Gemini integration with privacy isolation
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="rounded-md border border-slate-200 p-3 dark:border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500">Gateway:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {architecture ? `${architecture.ai_orchestration.gateway} (${architecture.ai_orchestration.model})` : "ControlledAIOrchestrator"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500">PII Redaction:</span>
                    <span className="text-emerald-600 font-semibold">Strict (Email, Phone, Roll ID)</span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500">Context Assembly:</span>
                    <span className="text-indigo-600 font-semibold">Authenticated & Scoped only</span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500">LLM Authority:</span>
                    <span className="text-rose-600 font-semibold">Zero business logic authority</span>
                  </div>
                </div>

                <div className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Student PII (name, email, institutional identification) is strictly stripped before prompt assembly. The LLM only receives anonymized academic context to produce explanations, tutoring, or content assistance.
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 2: Interactive SM-2 Spaced Repetition Engine Verification */}
        <TabsContent value="sm2" className="pt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <Calculator className="h-4 w-4 text-indigo-600" />
                    <span>Deterministic SM-2 Algorithm Workbench</span>
                  </CardTitle>
                  <CardDescription>
                    Interactive evaluation of the SuperMemo SM-2 recurrence relation
                  </CardDescription>
                </div>
                <Badge variant="outline" className="font-mono">Formula: EF&apos; = EF + (0.1 - (5 - q)(0.08 + (5 - q)0.02))</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
                    Grade <code className="text-indigo-600">(q: 0–5)</code>
                  </label>
                  <select
                    className="w-full h-9 rounded-md border border-slate-300 bg-white px-2 text-sm dark:border-slate-700 dark:bg-slate-900"
                    value={grade}
                    onChange={(e) => setGrade(Number(e.target.value))}
                  >
                    <option value={5}>5 - Perfect Recall</option>
                    <option value={4}>4 - Correct after hesitation</option>
                    <option value={3}>3 - Correct with serious difficulty</option>
                    <option value={2}>2 - Incorrect, familiar upon answer</option>
                    <option value={1}>1 - Incorrect, remembered upon answer</option>
                    <option value={0}>0 - Complete blackout</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
                    Previous Reps <code className="text-indigo-600">(n)</code>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={50}
                    className="w-full h-9 rounded-md border border-slate-300 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-900"
                    value={reps}
                    onChange={(e) => setReps(Math.max(0, Number(e.target.value)))}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
                    Previous Interval <code className="text-indigo-600">(days)</code>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={365}
                    className="w-full h-9 rounded-md border border-slate-300 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-900"
                    value={interval}
                    onChange={(e) => setInterval(Math.max(0, Number(e.target.value)))}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
                    Previous EF <code className="text-indigo-600">(≥ 1.3)</code>
                  </label>
                  <input
                    type="number"
                    step={0.1}
                    min={1.3}
                    max={5.0}
                    className="w-full h-9 rounded-md border border-slate-300 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-900"
                    value={ef}
                    onChange={(e) => setEf(Math.max(1.3, Number(e.target.value)))}
                  />
                </div>
              </div>

              {/* Output Display */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="rounded-lg border border-slate-200 p-4 bg-white dark:border-slate-800 dark:bg-slate-900">
                  <div className="text-xs text-slate-500">Calculated Next Interval</div>
                  <div className="text-2xl font-bold font-mono text-indigo-600 mt-1">
                    {sm2Result.newInterval} <span className="text-sm font-normal text-slate-500">days</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {grade < 3 ? "Reset to 1 day due to recall failure" : `Computed via I' = I * EF'`}
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 p-4 bg-white dark:border-slate-800 dark:bg-slate-900">
                  <div className="text-xs text-slate-500">Consecutive Repetitions</div>
                  <div className="text-2xl font-bold font-mono text-emerald-600 mt-1">
                    {sm2Result.newReps}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {grade < 3 ? "Streak reset to 0" : "Incremented from previous count"}
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 p-4 bg-white dark:border-slate-800 dark:bg-slate-900">
                  <div className="text-xs text-slate-500">Updated Easiness Factor (EF&apos;)</div>
                  <div className="text-2xl font-bold font-mono text-slate-800 dark:text-slate-200 mt-1">
                    {sm2Result.newEf.toFixed(4)}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Clamped to minimum floor of 1.3000
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: RBAC Role Matrix */}
        <TabsContent value="rbac" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-4 w-4 text-indigo-600" />
                <span>Role-Based Access Control (RBAC) Foundation</span>
              </CardTitle>
              <CardDescription>
                The 7 authorized platform roles in Dhruva.AI
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[
                  { role: "student", label: "Student", desc: "Adaptive learning, concept mastery, assessments, career path tracking" },
                  { role: "teacher", label: "Teacher / Faculty", desc: "Course delivery, assessment authoring, section-level student analytics" },
                  { role: "mentor", label: "Mentor", desc: "Assigned student cohort tracking, check-ins, early intervention alerts" },
                  { role: "hod", label: "Head of Department (HOD)", desc: "Departmental academic performance, faculty workload, curriculum health" },
                  { role: "placement_officer", label: "Placement Officer", desc: "Institutional skill-gap analysis, employability index, recruiter matching" },
                  { role: "institution_admin", label: "Institution Admin", desc: "Campus hierarchy, department config, institutional compliance & policy" },
                  { role: "super_admin", label: "Platform Super Admin", desc: "Multi-tenant orchestration, global security, system audit logs" },
                ].map((item) => (
                  <div key={item.role} className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{item.label}</span>
                      <Badge variant="secondary" className="font-mono text-[10px]">{item.role}</Badge>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">{item.desc}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Development Runbook */}
        <TabsContent value="runbook" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Terminal className="h-4 w-4 text-indigo-600" />
                <span>Development & Validation Runbook</span>
              </CardTitle>
              <CardDescription>
                Production CLI commands for operating and verifying Dhruva.AI
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 rounded-lg bg-slate-900 text-slate-100 dark:bg-black space-y-1">
                  <div className="text-slate-400"># Run automated backend test suite (15 passed unit tests)</div>
                  <div className="text-emerald-400">backend\.venv\Scripts\pytest -v backend/tests</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-900 text-slate-100 dark:bg-black space-y-1">
                  <div className="text-slate-400"># Start FastAPI backend server (Port 8000)</div>
                  <div className="text-emerald-400">backend\.venv\Scripts\uvicorn app.main:app --app-dir backend --reload --port 8000</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-900 text-slate-100 dark:bg-black space-y-1">
                  <div className="text-slate-400"># Build frontend production bundle & compile TypeScript</div>
                  <div className="text-emerald-400">cd frontend &amp;&amp; npm run build</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-900 text-slate-100 dark:bg-black space-y-1">
                  <div className="text-slate-400"># Start PostgreSQL with pgvector via Docker Compose</div>
                  <div className="text-emerald-400">docker compose up -d postgres</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  );
}
