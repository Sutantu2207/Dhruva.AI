"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Filter,
  RotateCcw,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  fetchGradingQueue,
  submitManualQuestionGrade,
  regradeManualQuestion,
} from "@/lib/api";
import type { GradingQueueItem, GradingQueueType, GradingQueuePriority } from "@/lib/types";

export default function FacultyGradingQueuePage() {
  const [items, setItems] = React.useState<GradingQueueItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const [selectedType, setSelectedType] = React.useState<GradingQueueType | "all">("all");
  const [selectedPriority, setSelectedPriority] = React.useState<GradingQueuePriority | "all">("all");

  // Active evaluation modal state
  const [activeItem, setActiveItem] = React.useState<GradingQueueItem | null>(null);
  const [marksAwarded, setMarksAwarded] = React.useState<number>(0);
  const [feedback, setFeedback] = React.useState<string>("");
  const [submitting, setSubmitting] = React.useState(false);
  const [actionSuccess, setActionSuccess] = React.useState<string | null>(null);

  // Regrade state
  const [isRegradeMode, setIsRegradeMode] = React.useState(false);
  const [regradeReason, setRegradeReason] = React.useState("");

  React.useEffect(() => {
    let active = true;
    fetchGradingQueue({
      itemType: selectedType === "all" ? undefined : selectedType,
      priority: selectedPriority === "all" ? undefined : selectedPriority,
    })
      .then((res) => {
        if (active) {
          setItems(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load grading queue.");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [selectedType, selectedPriority]);

  const refreshQueue = () => {
    setLoading(true);
    fetchGradingQueue({
      itemType: selectedType === "all" ? undefined : selectedType,
      priority: selectedPriority === "all" ? undefined : selectedPriority,
    })
      .then((res) => {
        setItems(res);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load grading queue.");
        setLoading(false);
      });
  };

  const handleSubmitEvaluation = async () => {
    if (!activeItem) return;
    setSubmitting(true);
    try {
      if (isRegradeMode) {
        if (!regradeReason || regradeReason.length < 5) {
          alert("A detailed audit reason is required for regrades.");
          setSubmitting(false);
          return;
        }
        await regradeManualQuestion(activeItem.item_id, {
          new_marks: marksAwarded,
          reason: regradeReason,
        });
        setActionSuccess(`Regrade finalized for ${activeItem.student_name}.`);
      } else {
        await submitManualQuestionGrade(activeItem.item_id, {
          marks_awarded: marksAwarded,
          feedback: feedback,
        });
        setActionSuccess(`Graded and released to ${activeItem.student_name}.`);
      }
      setActiveItem(null);
      setIsRegradeMode(false);
      setRegradeReason("");
      refreshQueue();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Evaluation failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <Link href="/faculty" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 mb-2">
            <ArrowLeft className="h-3 w-3" />
            Back to Faculty Dashboard
          </Link>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900">
            Faculty Grading & Evidence Review Queue
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manual rubric evaluations, student technical artifacts, and immutable regrades.
          </p>
        </div>

        {actionSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-xl border border-slate-200">
        <Filter className="h-4 w-4 text-slate-400" />
        <span className="text-xs font-semibold text-slate-700">Filters:</span>

        <select
          className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 text-slate-700"
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value as GradingQueueType | "all")}
        >
          <option value="all">All Item Types</option>
          <option value="manual_question">Subjective Assessments</option>
          <option value="project_review">Project Rubric Reviews</option>
          <option value="evidence_verification">Technical Evidence Items</option>
        </select>

        <select
          className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 text-slate-700"
          value={selectedPriority}
          onChange={(e) => setSelectedPriority(e.target.value as GradingQueuePriority | "all")}
        >
          <option value="all">All Priorities</option>
          <option value="high">High Priority (&gt;7 days old)</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>

        <span className="ml-auto text-xs text-slate-400 font-mono">
          {items.length} items waiting in queue
        </span>
      </div>

      {/* Main List */}
      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
        </div>
      ) : error ? (
        <Card className="border-red-200 bg-red-50 p-6 text-center text-xs text-red-700 font-medium">
          {error}
        </Card>
      ) : items.length === 0 ? (
        <Card className="border-slate-200 p-12 text-center space-y-2">
          <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto" />
          <p className="text-sm font-semibold text-slate-800">Grading Queue is Completely Cleared!</p>
          <p className="text-xs text-slate-500">There are no pending subjective answers or unverified project evidence items in your authorized scope.</p>
        </Card>
      ) : (
        <div className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
          {items.map((item) => (
            <div
              key={item.item_id}
              className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 hover:bg-slate-50/70 transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={`text-[10px] uppercase font-bold ${
                      item.priority === "high"
                        ? "border-red-200 bg-red-50 text-red-700"
                        : "border-slate-200 text-slate-600"
                    }`}
                  >
                    {item.priority}
                  </Badge>
                  <Badge variant="secondary" className="text-[10px]">
                    {item.item_type.replace("_", " ")}
                  </Badge>
                  {item.course_code && (
                    <span className="font-mono text-xs text-slate-500">
                      {item.course_code}
                    </span>
                  )}
                </div>
                <p className="text-sm font-bold text-slate-900">{item.title}</p>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="font-medium text-slate-700">{item.student_name}</span>
                  <span>•</span>
                  <span className="font-mono text-[11px]">{item.enrollment_number}</span>
                  <span>•</span>
                  <span>Submitted: {new Date(item.submitted_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Button
                  size="sm"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs h-8 gap-1.5"
                  onClick={() => {
                    setActiveItem(item);
                    setIsRegradeMode(false);
                    setMarksAwarded(0);
                    setFeedback("");
                  }}
                >
                  <span>Evaluate</span>
                  <ChevronRight className="h-3 w-3" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs h-8 gap-1 text-slate-600 hover:text-slate-900"
                  onClick={() => {
                    setActiveItem(item);
                    setIsRegradeMode(true);
                    setMarksAwarded(0);
                    setRegradeReason("");
                  }}
                >
                  <RotateCcw className="h-3 w-3" />
                  <span>Regrade</span>
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Evaluation Modal Drawer */}
      {activeItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <Card className="w-full max-w-lg border-slate-200 shadow-2xl bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <Badge variant="outline" className="text-xs uppercase font-mono">
                  {isRegradeMode ? "Immutable Regrade Audit" : "Manual Rubric Evaluation"}
                </Badge>
                <button
                  className="text-slate-400 hover:text-slate-600 text-sm font-bold"
                  onClick={() => setActiveItem(null)}
                >
                  ✕
                </button>
              </div>
              <CardTitle className="text-base text-slate-900 mt-1">{activeItem.title}</CardTitle>
              <CardDescription className="text-xs">
                Candidate: {activeItem.student_name} ({activeItem.enrollment_number})
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Marks Awarded:
                </label>
                <Input
                  type="number"
                  step="0.5"
                  value={marksAwarded}
                  onChange={(e) => setMarksAwarded(parseFloat(e.target.value) || 0)}
                  className="h-9 text-sm"
                  placeholder="e.g. 8.5"
                />
              </div>

              {isRegradeMode ? (
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Formal Regrade Justification (Audited):
                  </label>
                  <textarea
                    rows={3}
                    className="w-full text-xs p-2 border border-slate-200 rounded-lg focus:outline-indigo-500"
                    placeholder="Provide verifiable reason (e.g., student submitted missed appendix during review period)..."
                    value={regradeReason}
                    onChange={(e) => setRegradeReason(e.target.value)}
                  />
                  <p className="text-[10px] text-amber-600 mt-1">
                    * Every regrade action creates an immutable EvaluationRegradeAudit log entry.
                  </p>
                </div>
              ) : (
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Feedback / Rubric Notes:
                  </label>
                  <textarea
                    rows={3}
                    className="w-full text-xs p-2 border border-slate-200 rounded-lg focus:outline-indigo-500"
                    placeholder="Constructive technical feedback explaining score..."
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                  />
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setActiveItem(null)}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                  onClick={handleSubmitEvaluation}
                  disabled={submitting}
                >
                  {submitting ? "Submitting..." : isRegradeMode ? "Record Regrade" : "Finalize Score"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
