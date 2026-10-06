"use client";

import * as React from "react";
import Link from "next/link";
import {
  Brain,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  RotateCw,
  Clock,
  ArrowRight,
  Search,
  Calendar,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  fetchMyKnowledgeSummary,
  fetchMyConceptStates,
  fetchMyWeakConcepts,
  fetchMyAtRiskConcepts,
  fetchMyDailyMission,
  triggerKnowledgeRebuild,
} from "@/lib/api";
import type {
  StudentKnowledgeSummary,
  ConceptKnowledgeState,
  DailyMission,
} from "@/lib/types";

export function KnowledgeDashboard() {
  const [summary, setSummary] = React.useState<StudentKnowledgeSummary | null>(null);
  const [concepts, setConcepts] = React.useState<ConceptKnowledgeState[]>([]);
  const [weakConcepts, setWeakConcepts] = React.useState<ConceptKnowledgeState[]>([]);
  const [atRiskConcepts, setAtRiskConcepts] = React.useState<ConceptKnowledgeState[]>([]);
  const [dailyMission, setDailyMission] = React.useState<DailyMission | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [rebuilding, setRebuilding] = React.useState<boolean>(false);
  const [searchQuery, setSearchQuery] = React.useState<string>("");
  const [stateFilter, setStateFilter] = React.useState<string>("all");
  const [statusMessage, setStatusMessage] = React.useState<string | null>(null);

  const refreshData = React.useCallback(async () => {
    try {
      const [sumRes, concRes, weakRes, atRiskRes, missionRes] = await Promise.all([
        fetchMyKnowledgeSummary().catch(() => null),
        fetchMyConceptStates({ limit: 100 }).catch(() => []),
        fetchMyWeakConcepts().catch(() => []),
        fetchMyAtRiskConcepts().catch(() => []),
        fetchMyDailyMission().catch(() => null),
      ]);
      setSummary(sumRes);
      setConcepts(concRes);
      setWeakConcepts(weakRes);
      setAtRiskConcepts(atRiskRes);
      setDailyMission(missionRes);
    } catch {
      setStatusMessage("Failed to load knowledge state data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const [sumRes, concRes, weakRes, atRiskRes, missionRes] = await Promise.all([
          fetchMyKnowledgeSummary().catch(() => null),
          fetchMyConceptStates({ limit: 100 }).catch(() => []),
          fetchMyWeakConcepts().catch(() => []),
          fetchMyAtRiskConcepts().catch(() => []),
          fetchMyDailyMission().catch(() => null),
        ]);
        if (!ignore) {
          setSummary(sumRes);
          setConcepts(concRes);
          setWeakConcepts(weakRes);
          setAtRiskConcepts(atRiskRes);
          setDailyMission(missionRes);
        }
      } catch {
        if (!ignore) {
          setStatusMessage("Failed to load knowledge state data. Please try again.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadInitial();
    return () => {
      ignore = true;
    };
  }, []);

  const handleRebuild = async () => {
    try {
      setRebuilding(true);
      setStatusMessage(null);
      const res = await triggerKnowledgeRebuild();
      setStatusMessage(`Knowledge profile recalculated: ${res.rebuilt_concept_states} concepts re-evaluated from evidence.`);
      await refreshData();
    } catch {
      setStatusMessage("Failed to rebuild knowledge state. Try again shortly.");
    } finally {
      setRebuilding(false);
    }
  };

  const filteredConcepts = React.useMemo(() => {
    return concepts.filter((c) => {
      const matchesSearch =
        !searchQuery ||
        (c.concept_name && c.concept_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (c.concept_slug && c.concept_slug.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesState = stateFilter === "all" || c.state === stateFilter;
      return matchesSearch && matchesState;
    });
  }, [concepts, searchQuery, stateFilter]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <RotateCw className="h-8 w-8 animate-spin text-indigo-600" />
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
            Synthesizing deterministic knowledge states...
          </p>
        </div>
      </div>
    );
  }

  const isBrandNewStudent = !summary || summary.total_observed_concepts === 0;

  return (
    <div className="space-y-8 pb-12">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-6 dark:border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <Brain className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Knowledge State & Concept Mastery
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Authoritative, evidence-derived state of what you know, retention decay, and active spaced repetition schedules.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link href="/review">
            <Button className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm flex items-center space-x-2">
              <Clock className="h-4 w-4" />
              <span>Review Center</span>
              {summary && (summary.due_reviews_count > 0 || summary.overdue_reviews_count > 0) && (
                <span className="ml-1 rounded-full bg-rose-500 px-2 py-0.5 text-xs text-white">
                  {summary.due_reviews_count + summary.overdue_reviews_count}
                </span>
              )}
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRebuild}
            disabled={rebuilding}
            className="flex items-center space-x-1.5"
          >
            <RotateCw className={`h-4 w-4 ${rebuilding ? "animate-spin text-indigo-600" : ""}`} />
            <span>{rebuilding ? "Recalculating..." : "Recompute Knowledge"}</span>
          </Button>
        </div>
      </div>

      {statusMessage && (
        <Alert className="border-indigo-200 bg-indigo-50 dark:border-indigo-900/50 dark:bg-indigo-950/20">
          <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
          <AlertTitle className="text-indigo-900 dark:text-indigo-200">System Notification</AlertTitle>
          <AlertDescription className="text-indigo-800 dark:text-indigo-300">{statusMessage}</AlertDescription>
        </Alert>
      )}

      {/* Brand New Student Honest Empty State */}
      {isBrandNewStudent ? (
        <Card className="border-dashed border-2 border-slate-300 dark:border-slate-800 p-8 text-center bg-slate-50/50 dark:bg-slate-900/50">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 mb-4">
            <Brain className="h-8 w-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
            Your knowledge profile is still being established
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-slate-500 dark:text-slate-400">
            Dhruva.AI computes concept mastery strictly from deterministic assessment and practice evidence.
            No evidence has been recorded for your profile yet.
          </p>
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/assessments">
              <Button className="bg-indigo-600 hover:bg-indigo-700 text-white">
                Take Baseline Assessment
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="outline">Explore Assigned Courses</Button>
            </Link>
          </div>
        </Card>
      ) : (
        <>
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="p-4 pb-2">
                <CardDescription className="text-xs uppercase font-semibold tracking-wider">
                  Concepts Observed
                </CardDescription>
                <CardTitle className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {summary?.total_observed_concepts ?? 0}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <div className="flex items-center space-x-2 text-xs text-slate-500">
                  <span className="font-medium text-emerald-600">{summary?.mastered_count ?? 0} Mastered</span>
                  <span>•</span>
                  <span className="font-medium text-blue-600">{summary?.proficient_count ?? 0} Proficient</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="p-4 pb-2">
                <CardDescription className="text-xs uppercase font-semibold tracking-wider">
                  Average Mastery
                </CardDescription>
                <CardTitle className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {summary?.average_mastery !== null && summary?.average_mastery !== undefined
                    ? `${Math.round(summary.average_mastery * 100)}%`
                    : "Establishing"}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <Progress
                  value={summary?.average_mastery ? Math.round(summary.average_mastery * 100) : 0}
                  className="h-2 bg-slate-100 dark:bg-slate-800"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="p-4 pb-2">
                <CardDescription className="text-xs uppercase font-semibold tracking-wider">
                  Average Retention
                </CardDescription>
                <CardTitle className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                  {summary ? `${Math.round(summary.average_retention * 100)}%` : "0%"}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <p className="text-xs text-slate-500">
                  Decaying via Ebbinghaus model based on elapsed time since recall.
                </p>
              </CardContent>
            </Card>

            <Card className={summary && (summary.due_reviews_count > 0 || summary.overdue_reviews_count > 0) ? "border-amber-300 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-950/10" : ""}>
              <CardHeader className="p-4 pb-2">
                <CardDescription className="text-xs uppercase font-semibold tracking-wider">
                  Pending Reviews
                </CardDescription>
                <CardTitle className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center justify-between">
                  <span>{(summary?.due_reviews_count ?? 0) + (summary?.overdue_reviews_count ?? 0)}</span>
                  {summary && summary.overdue_reviews_count > 0 && (
                    <Badge variant="destructive" className="text-xs">
                      {summary.overdue_reviews_count} Overdue
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <Link href="/review" className="text-xs font-medium text-indigo-600 hover:underline flex items-center">
                  <span>Open SM-2 Review Center</span>
                  <ArrowRight className="h-3 w-3 ml-1" />
                </Link>
              </CardContent>
            </Card>
          </div>

          {/* Daily Mission Section */}
          {dailyMission && dailyMission.tasks.length > 0 && (
            <Card className="border-indigo-100 bg-gradient-to-br from-white to-indigo-50/30 dark:border-indigo-900/30 dark:from-slate-900 dark:to-indigo-950/20 shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                    <CardTitle className="text-lg font-bold">Today&apos;s Adaptive Learning Mission</CardTitle>
                  </div>
                  <Badge variant="secondary" className="font-mono text-xs">
                    Est. {dailyMission.total_estimated_minutes} mins
                  </Badge>
                </div>
                <CardDescription>
                  Deterministic priority queue: addresses retention decay, prerequisite weaknesses, and mastery gaps.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {dailyMission.tasks.map((task) => (
                    <div
                      key={task.task_id}
                      className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-slate-900"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <Badge
                            variant={
                              task.task_type === "review"
                                ? "destructive"
                                : task.task_type === "lesson"
                                ? "default"
                                : "secondary"
                            }
                            className="uppercase text-[10px]"
                          >
                            {task.task_type}
                          </Badge>
                          <span className="text-xs text-slate-400">{task.estimated_minutes}m</span>
                        </div>
                        <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">{task.title}</h4>
                        <p className="text-xs text-slate-500 mt-1">Concept: {task.concept_name}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {task.reason_codes.slice(0, 2).map((r) => (
                            <Badge key={r} variant="outline" className="text-[9px] py-0 px-1 font-mono">
                              {r}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="mt-4 pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                        {task.task_type === "review" ? (
                          <Link href="/review">
                            <Button size="sm" variant="ghost" className="h-8 text-xs text-indigo-600 font-medium">
                              Review Now →
                            </Button>
                          </Link>
                        ) : (
                          <Link href={`/knowledge/concepts/${task.concept_id}`}>
                            <Button size="sm" variant="ghost" className="h-8 text-xs text-indigo-600 font-medium">
                              Inspect Concept →
                            </Button>
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Weak & At-Risk Concepts Watchlist */}
          {(weakConcepts.length > 0 || atRiskConcepts.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* At-Risk Concepts */}
              <Card className="border-rose-200 dark:border-rose-900/50">
                <CardHeader className="pb-3">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="h-5 w-5 text-rose-600 dark:text-rose-400" />
                    <CardTitle className="text-base font-bold text-rose-900 dark:text-rose-200">
                      At-Risk Concepts ({atRiskConcepts.length})
                    </CardTitle>
                  </div>
                  <CardDescription className="text-xs">
                    High retention decay or deteriorating recent performance.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {atRiskConcepts.length === 0 ? (
                    <p className="text-xs text-slate-500">No concepts currently flagged as at-risk.</p>
                  ) : (
                    atRiskConcepts.slice(0, 5).map((c) => (
                      <div
                        key={c.id}
                        className="flex items-center justify-between p-2.5 rounded-md bg-rose-50/50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30"
                      >
                        <div>
                          <Link
                            href={`/knowledge/concepts/${c.concept_id}`}
                            className="font-medium text-sm text-slate-900 dark:text-slate-100 hover:text-indigo-600"
                          >
                            {c.concept_name || c.concept_slug}
                          </Link>
                          <div className="flex items-center space-x-2 mt-0.5 text-xs text-slate-500">
                            <span>Retention: {Math.round(c.retention_estimate * 100)}%</span>
                            <span>•</span>
                            <span className="capitalize">{c.trend.replace("_", " ")}</span>
                          </div>
                        </div>
                        <Link href={`/knowledge/concepts/${c.concept_id}`}>
                          <Button size="sm" variant="ghost" className="h-7 text-xs">
                            View
                          </Button>
                        </Link>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              {/* Developing / Weak Concepts */}
              <Card className="border-amber-200 dark:border-amber-900/50">
                <CardHeader className="pb-3">
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                    <CardTitle className="text-base font-bold text-amber-900 dark:text-amber-200">
                      Developing Concepts ({weakConcepts.length})
                    </CardTitle>
                  </div>
                  <CardDescription className="text-xs">
                    Concepts requiring additional structured practice to reach proficiency.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {weakConcepts.length === 0 ? (
                    <p className="text-xs text-slate-500">No concepts currently in developing state.</p>
                  ) : (
                    weakConcepts.slice(0, 5).map((c) => (
                      <div
                        key={c.id}
                        className="flex items-center justify-between p-2.5 rounded-md bg-amber-50/50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30"
                      >
                        <div>
                          <Link
                            href={`/knowledge/concepts/${c.concept_id}`}
                            className="font-medium text-sm text-slate-900 dark:text-slate-100 hover:text-indigo-600"
                          >
                            {c.concept_name || c.concept_slug}
                          </Link>
                          <div className="flex items-center space-x-2 mt-0.5 text-xs text-slate-500">
                            <span>
                              Mastery:{" "}
                              {c.current_mastery !== null && c.current_mastery !== undefined
                                ? `${Math.round(c.current_mastery * 100)}%`
                                : "N/A"}
                            </span>
                            <span>•</span>
                            <span>Evidence: {c.evidence_count}</span>
                          </div>
                        </div>
                        <Link href={`/knowledge/concepts/${c.concept_id}`}>
                          <Button size="sm" variant="ghost" className="h-7 text-xs">
                            View
                          </Button>
                        </Link>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Concept Mastery Inventory Table */}
          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle className="text-lg font-bold">Concept Knowledge Registry</CardTitle>
                  <CardDescription className="text-xs">
                    Authoritative student knowledge states computed deterministically from Domain 5 evidence.
                  </CardDescription>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search concepts..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="h-9 w-48 rounded-md border border-slate-300 pl-8 pr-3 text-xs focus:border-indigo-500 focus:outline-hidden dark:border-slate-700 dark:bg-slate-800"
                    />
                  </div>

                  <select
                    value={stateFilter}
                    onChange={(e) => setStateFilter(e.target.value)}
                    className="h-9 rounded-md border border-slate-300 px-3 text-xs focus:border-indigo-500 focus:outline-hidden dark:border-slate-700 dark:bg-slate-800"
                  >
                    <option value="all">All States</option>
                    <option value="mastered">Mastered</option>
                    <option value="proficient">Proficient</option>
                    <option value="developing">Developing</option>
                    <option value="at_risk">At Risk</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {filteredConcepts.length === 0 ? (
                <div className="py-8 text-center text-sm text-slate-500">
                  No concepts match the selected filter criteria.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-200 bg-slate-50/50 text-slate-600 dark:border-slate-800 dark:bg-slate-900/50">
                      <tr>
                        <th className="px-4 py-3 font-semibold">Concept</th>
                        <th className="px-4 py-3 font-semibold">Mastery</th>
                        <th className="px-4 py-3 font-semibold">Confidence</th>
                        <th className="px-4 py-3 font-semibold">Retention</th>
                        <th className="px-4 py-3 font-semibold">State</th>
                        <th className="px-4 py-3 font-semibold">Trend</th>
                        <th className="px-4 py-3 font-semibold">Prereqs</th>
                        <th className="px-4 py-3 font-semibold text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {filteredConcepts.map((item) => {
                        const masteryPct =
                          item.current_mastery !== null && item.current_mastery !== undefined
                            ? Math.round(item.current_mastery * 100)
                            : null;
                        const retentionPct = Math.round(item.retention_estimate * 100);
                        const confidencePct = Math.round(item.confidence * 100);

                        return (
                          <tr key={item.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                            <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                              <Link
                                href={`/knowledge/concepts/${item.concept_id}`}
                                className="hover:text-indigo-600 font-semibold"
                              >
                                {item.concept_name || item.concept_slug}
                              </Link>
                              <div className="text-[10px] text-slate-400">
                                {item.evidence_count} evidence records
                              </div>
                            </td>

                            <td className="px-4 py-3">
                              {masteryPct !== null ? (
                                <div className="space-y-1 w-24">
                                  <div className="flex justify-between text-[11px] font-medium">
                                    <span>{masteryPct}%</span>
                                  </div>
                                  <Progress value={masteryPct} className="h-1.5" />
                                </div>
                              ) : (
                                <span className="text-slate-400 italic">Insufficient</span>
                              )}
                            </td>

                            <td className="px-4 py-3">
                              <span className="font-mono text-slate-600 dark:text-slate-400">
                                {confidencePct}%
                              </span>
                            </td>

                            <td className="px-4 py-3">
                              <div className="flex items-center space-x-1.5">
                                <span
                                  className={`font-semibold ${
                                    retentionPct < 50
                                      ? "text-rose-600 dark:text-rose-400"
                                      : retentionPct < 70
                                      ? "text-amber-600 dark:text-amber-400"
                                      : "text-emerald-600 dark:text-emerald-400"
                                  }`}
                                >
                                  {retentionPct}%
                                </span>
                              </div>
                            </td>

                            <td className="px-4 py-3">
                              <Badge
                                variant={
                                  item.state === "mastered"
                                    ? "success"
                                    : item.state === "proficient"
                                    ? "default"
                                    : item.state === "at_risk"
                                    ? "destructive"
                                    : item.state === "developing"
                                    ? "warning"
                                    : "secondary"
                                }
                                className="uppercase text-[9px] font-mono"
                              >
                                {item.state.replace("_", " ")}
                              </Badge>
                            </td>

                            <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-400">
                              {item.trend.replace("_", " ")}
                            </td>

                            <td className="px-4 py-3">
                              <Badge
                                variant={
                                  item.prerequisite_health === "healthy"
                                    ? "success"
                                    : item.prerequisite_health === "weak"
                                    ? "destructive"
                                    : "secondary"
                                }
                                className="text-[9px]"
                              >
                                {item.prerequisite_health}
                              </Badge>
                            </td>

                            <td className="px-4 py-3 text-right">
                              <Link href={`/knowledge/concepts/${item.concept_id}`}>
                                <Button size="sm" variant="ghost" className="h-7 text-xs text-indigo-600">
                                  Inspect
                                </Button>
                              </Link>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
