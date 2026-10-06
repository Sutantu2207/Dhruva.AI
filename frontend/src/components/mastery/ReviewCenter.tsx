"use client";

import * as React from "react";
import Link from "next/link";
import {
  Clock,
  CheckCircle2,
  RotateCw,
  ArrowRight,
  Brain,
  Zap,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { fetchDueReviews, fetchUpcomingReviews, completeConceptReview } from "@/lib/api";
import type { ConceptReviewState } from "@/lib/types";

export function ReviewCenter() {
  const [dueReviews, setDueReviews] = React.useState<ConceptReviewState[]>([]);
  const [upcomingReviews, setUpcomingReviews] = React.useState<ConceptReviewState[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [activeReview, setActiveReview] = React.useState<ConceptReviewState | null>(null);
  const [submittingQuality, setSubmittingQuality] = React.useState<boolean>(false);
  const [completionFeedback, setCompletionFeedback] = React.useState<{
    conceptName: string;
    newIntervalDays: number;
    newEaseFactor: number;
    nextReviewAt: string;
  } | null>(null);

  React.useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const [due, upcoming] = await Promise.all([
          fetchDueReviews().catch(() => []),
          fetchUpcomingReviews(30).catch(() => []),
        ]);
        if (!ignore) {
          setDueReviews(due);
          setUpcomingReviews(upcoming);
          if (due.length > 0) {
            setActiveReview(due[0]);
          }
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

  const handleCompleteReview = async (quality: number) => {
    if (!activeReview) return;
    try {
      setSubmittingQuality(true);
      const res = await completeConceptReview(activeReview.concept_id, {
        quality,
        duration_seconds: 45,
        trigger: "review_center_session",
      });

      setCompletionFeedback({
        conceptName: activeReview.concept_name || "Concept",
        newIntervalDays: res.interval_days,
        newEaseFactor: res.ease_factor,
        nextReviewAt: res.next_review_at,
      });

      // Remove from due list and select next
      const remaining = dueReviews.filter((r) => r.concept_id !== activeReview.concept_id);
      setDueReviews(remaining);
      setActiveReview(remaining.length > 0 ? remaining[0] : null);

      // Refresh upcoming list
      const upcoming = await fetchUpcomingReviews(30).catch(() => []);
      setUpcomingReviews(upcoming);
    } catch {
      // Handled gracefully
    } finally {
      setSubmittingQuality(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <RotateCw className="h-8 w-8 animate-spin text-indigo-600" />
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
            Loading spaced repetition schedules...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-6 dark:border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <Clock className="h-7 w-7 text-indigo-600 dark:text-indigo-400" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Spaced Repetition Review Center
            </h1>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Deterministic SuperMemo SM-2 memory consolidation engine. Strengthen retention at the optimal decay point.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link href="/knowledge">
            <Button variant="outline" size="sm" className="flex items-center space-x-1.5">
              <Brain className="h-4 w-4 text-indigo-600" />
              <span>Knowledge Dashboard</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Completion feedback banner */}
      {completionFeedback && (
        <Alert className="border-emerald-200 bg-emerald-50 dark:border-emerald-900/50 dark:bg-emerald-950/20">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <AlertTitle className="text-emerald-900 dark:text-emerald-200">
            Review Completed: {completionFeedback.conceptName}
          </AlertTitle>
          <AlertDescription className="text-emerald-800 dark:text-emerald-300">
            SM-2 interval scheduled:{" "}
            <strong>{completionFeedback.newIntervalDays} days</strong> (Ease Factor:{" "}
            {completionFeedback.newEaseFactor.toFixed(2)}). Next review date:{" "}
            {new Date(completionFeedback.nextReviewAt).toLocaleDateString()}.
          </AlertDescription>
        </Alert>
      )}

      {/* Active Trial or Caught Up Card */}
      {activeReview ? (
        <Card className="border-indigo-200 shadow-md dark:border-indigo-900/60 bg-gradient-to-b from-white to-slate-50/50 dark:from-slate-900 dark:to-slate-950">
          <CardHeader className="border-b border-slate-100 pb-4 dark:border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Zap className="h-5 w-5 text-amber-500" />
                <Badge variant="outline" className="font-mono text-xs uppercase tracking-wider">
                  Active Spaced Review Trial
                </Badge>
              </div>
              <Badge
                variant={activeReview.review_status === "overdue" ? "destructive" : "warning"}
                className="text-xs uppercase font-mono"
              >
                {activeReview.review_status}
              </Badge>
            </div>
            <CardTitle className="text-2xl font-bold mt-2 text-slate-900 dark:text-slate-100">
              {activeReview.concept_name || "Concept Review"}
            </CardTitle>
            <CardDescription>
              Streak repetition: {activeReview.repetition} • Current interval: {activeReview.interval_days} days • Ease factor: {activeReview.ease_factor.toFixed(2)}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            <div className="p-4 rounded-lg bg-indigo-50/60 border border-indigo-100 dark:bg-indigo-950/30 dark:border-indigo-900/40">
              <h4 className="font-semibold text-sm text-indigo-950 dark:text-indigo-200 mb-1">
                Active Recall Prompt
              </h4>
              <p className="text-sm text-slate-700 dark:text-slate-300">
                Without looking at documentation or code solutions, explain the core invariant, time complexity, and primary operations of{" "}
                <span className="font-bold">{activeReview.concept_name}</span>.
              </p>
            </div>

            {/* Quality Rating Form */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                Rate Recall Quality (Deterministic SM-2 Scale: 0 to 5)
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {[
                  { q: 0, label: "0 - Blackout", desc: "Complete failure to recall", color: "hover:border-rose-500" },
                  { q: 1, label: "1 - Incorrect", desc: "Wrong recall on key ideas", color: "hover:border-rose-400" },
                  { q: 2, label: "2 - Severe", desc: "Recalled with heavy cues", color: "hover:border-amber-400" },
                  { q: 3, label: "3 - Effortful", desc: "Correct after difficulty", color: "hover:border-blue-400" },
                  { q: 4, label: "4 - Good", desc: "Correct after slight pause", color: "hover:border-emerald-400" },
                  { q: 5, label: "5 - Perfect", desc: "Instant, effortless recall", color: "hover:border-emerald-500" },
                ].map((item) => (
                  <button
                    key={item.q}
                    type="button"
                    disabled={submittingQuality}
                    onClick={() => handleCompleteReview(item.q)}
                    className={`flex flex-col text-left p-3 rounded-lg border border-slate-200 bg-white transition-all shadow-2xs hover:shadow-sm dark:border-slate-800 dark:bg-slate-900 cursor-pointer disabled:opacity-50 ${item.color}`}
                  >
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100">{item.label}</span>
                    <span className="text-[11px] text-slate-500 mt-1 leading-snug">{item.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center text-xs text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
              <span>{dueReviews.length} concept(s) due today</span>
              <Link
                href={`/knowledge/concepts/${activeReview.concept_id}`}
                className="text-indigo-600 hover:underline flex items-center"
              >
                Inspect concept details <ArrowRight className="h-3 w-3 ml-1" />
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="p-8 text-center bg-slate-50/50 dark:bg-slate-900/50 border-dashed border-2">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400 mb-3">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            All Reviews Complete for Today
          </h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
            You have no pending due or overdue reviews right now. Spaced repetition intervals have protected your active retention.
          </p>
          <div className="mt-5">
            <Link href="/knowledge">
              <Button variant="outline" size="sm">
                Return to Knowledge Dashboard
              </Button>
            </Link>
          </div>
        </Card>
      )}

      {/* Tabs for Queues */}
      <Tabs defaultValue="due">
        <TabsList className="mb-4">
          <TabsTrigger value="due" className="flex items-center space-x-2">
            <span>Due & Overdue</span>
            <Badge variant="secondary" className="text-xs">
              {dueReviews.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="upcoming" className="flex items-center space-x-2">
            <span>Upcoming Schedules</span>
            <Badge variant="secondary" className="text-xs">
              {upcomingReviews.length}
            </Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="due">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-bold">Due Reviews Queue</CardTitle>
              <CardDescription className="text-xs">
                Concepts whose scheduled review timestamp is at or before the current server clock.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {dueReviews.length === 0 ? (
                <p className="text-sm text-slate-500 py-4">No reviews currently due.</p>
              ) : (
                <div className="space-y-2">
                  {dueReviews.map((r) => (
                    <div
                      key={r.id}
                      className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-800/30"
                    >
                      <div>
                        <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                          {r.concept_name || "Concept"}
                        </h4>
                        <div className="flex items-center space-x-3 text-xs text-slate-500 mt-1">
                          <span>Interval: {r.interval_days}d</span>
                          <span>•</span>
                          <span>Repetition: #{r.repetition}</span>
                          <span>•</span>
                          <span>Ease: {r.ease_factor.toFixed(2)}</span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Badge
                          variant={r.review_status === "overdue" ? "destructive" : "warning"}
                          className="text-[10px] uppercase font-mono"
                        >
                          {r.review_status}
                        </Badge>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setActiveReview(r)}
                          className="h-8 text-xs text-indigo-600 font-medium"
                        >
                          Practice Now
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="upcoming">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-bold">Upcoming Scheduled Reviews</CardTitle>
              <CardDescription className="text-xs">
                Future spaced repetition trials computed by SuperMemo SM-2.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {upcomingReviews.length === 0 ? (
                <p className="text-sm text-slate-500 py-4">No upcoming reviews scheduled yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-200 bg-slate-50/50 text-slate-600 dark:border-slate-800 dark:bg-slate-900/50">
                      <tr>
                        <th className="px-4 py-3 font-semibold">Concept</th>
                        <th className="px-4 py-3 font-semibold">Scheduled Date</th>
                        <th className="px-4 py-3 font-semibold">Current Interval</th>
                        <th className="px-4 py-3 font-semibold">Repetition Streak</th>
                        <th className="px-4 py-3 font-semibold">Ease Factor</th>
                        <th className="px-4 py-3 font-semibold text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {upcomingReviews.map((r) => (
                        <tr key={r.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                          <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                            {r.concept_name || "Concept"}
                          </td>
                          <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                            {new Date(r.next_review_at).toLocaleDateString()}
                          </td>
                          <td className="px-4 py-3">{r.interval_days} days</td>
                          <td className="px-4 py-3">#{r.repetition}</td>
                          <td className="px-4 py-3 font-mono">{r.ease_factor.toFixed(2)}</td>
                          <td className="px-4 py-3 text-right">
                            <Link href={`/knowledge/concepts/${r.concept_id}`}>
                              <Button size="sm" variant="ghost" className="h-7 text-xs text-indigo-600">
                                Details
                              </Button>
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
