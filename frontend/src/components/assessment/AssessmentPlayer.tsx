"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  fetchAttemptDelivery,
  autosaveResponse,
  submitAssessmentAttempt,
} from "@/lib/api";
import type {
  AttemptDelivery,
  AttemptDeliveryQuestion,
  AssessmentResult,
} from "@/lib/types";
import {
  Clock,
  Award,
  Flag,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Send,
  AlertTriangle,
  Code2,
} from "lucide-react";

interface AssessmentPlayerProps {
  attemptId: string;
  onSubmitted: (result: AssessmentResult) => void;
  onCancel?: () => void;
}

export function AssessmentPlayer({
  attemptId,
  onSubmitted,
  onCancel,
}: AssessmentPlayerProps) {
  const [delivery, setDelivery] = React.useState<AttemptDelivery | null>(null);
  const [currentIndex, setCurrentIndex] = React.useState<number>(0);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  // Student Responses: question_version_id -> response_payload
  const [answers, setAnswers] = React.useState<Record<string, Record<string, unknown>>>({});
  // Flagged questions
  const [flagged, setFlagged] = React.useState<Set<string>>(new Set());

  // Autosave status
  const [saveStatus, setSaveStatus] = React.useState<"saved" | "saving" | "unsaved">("saved");

  // Timer: seconds remaining calculated from expires_at
  const [timeLeftSeconds, setTimeLeftSeconds] = React.useState<number | null>(null);

  // Submit modal
  const [showSubmitModal, setShowSubmitModal] = React.useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = React.useState<boolean>(false);

  // Load Delivery Data
  React.useEffect(() => {
    const loadDelivery = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await fetchAttemptDelivery(attemptId);
        setDelivery(data);

        // Calculate initial remaining seconds from server expires_at
        const expiresAtMs = new Date(data.expires_at).getTime();
        const nowMs = Date.now();
        const diffSec = Math.max(0, Math.floor((expiresAtMs - nowMs) / 1000));
        setTimeLeftSeconds(diffSec);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load assessment delivery");
      } finally {
        setLoading(false);
      }
    };
    loadDelivery();
  }, [attemptId]);

  // Countdown timer tick
  React.useEffect(() => {
    if (timeLeftSeconds === null || timeLeftSeconds <= 0) return;

    const timer = setInterval(() => {
      setTimeLeftSeconds((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeftSeconds]);

  // Debounced autosave
  const activeQuestion: AttemptDeliveryQuestion | undefined =
    delivery?.questions[currentIndex];

  const handleAnswerChange = React.useCallback(
    async (qVerId: string, payload: Record<string, unknown>) => {
      setAnswers((prev) => ({ ...prev, [qVerId]: payload }));
      setSaveStatus("saving");

      try {
        await autosaveResponse(attemptId, qVerId, payload);
        setSaveStatus("saved");
      } catch {
        setSaveStatus("unsaved");
      }
    },
    [attemptId]
  );

  const toggleFlag = (qVerId: string) => {
    setFlagged((prev) => {
      const next = new Set(prev);
      if (next.has(qVerId)) {
        next.delete(qVerId);
      } else {
        next.add(qVerId);
      }
      return next;
    });
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      setError(null);
      const result = await submitAssessmentAttempt(attemptId);
      onSubmitted(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Submission failed");
      setIsSubmitting(false);
    }
  };

  const formatTimer = (totalSeconds: number | null) => {
    if (totalSeconds === null) return "--:--";
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-muted-foreground flex flex-col items-center justify-center space-y-3">
        <Clock className="h-8 w-8 animate-spin text-primary" />
        <p>Loading secure assessment environment...</p>
      </div>
    );
  }

  if (error && !delivery) {
    return (
      <Alert variant="destructive" className="m-6">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Assessment Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!delivery || delivery.questions.length === 0) {
    return (
      <Card className="m-6 p-8 text-center text-muted-foreground">
        No questions found for this assessment attempt.
      </Card>
    );
  }

  const answeredCount = Object.keys(answers).length;
  const totalQuestions = delivery.questions.length;
  const unansweredCount = totalQuestions - answeredCount;
  const flaggedCount = flagged.size;

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      {/* Authoritative Server-Clock Header */}
      <Card className="border-border shadow-sm bg-card sticky top-2 z-10">
        <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
              {delivery.assessment_title}
              <Badge variant="outline" className="text-xs uppercase">
                {delivery.assessment_type}
              </Badge>
            </h2>
            <p className="text-xs text-muted-foreground">
              Question {currentIndex + 1} of {totalQuestions} | {answeredCount} Answered
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Autosave status indicator */}
            <div className="text-xs flex items-center gap-1.5 text-muted-foreground">
              {saveStatus === "saving" && (
                <span className="text-amber-500 animate-pulse">● Saving...</span>
              )}
              {saveStatus === "saved" && (
                <span className="text-green-600 dark:text-green-400 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> Saved
                </span>
              )}
              {saveStatus === "unsaved" && (
                <span className="text-destructive">● Unsaved</span>
              )}
            </div>

            {/* Authoritative Timer Display */}
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border font-mono font-bold text-sm ${
                timeLeftSeconds !== null && timeLeftSeconds < 300
                  ? "bg-destructive/10 text-destructive border-destructive/30 animate-pulse"
                  : "bg-muted text-foreground border-border"
              }`}
            >
              <Clock className="h-4 w-4" />
              <span>{formatTimer(timeLeftSeconds)}</span>
            </div>

            {onCancel && (
              <Button
                variant="outline"
                size="sm"
                onClick={onCancel}
                className="text-xs"
              >
                Exit
              </Button>
            )}

            <Button
              variant="default"
              size="sm"
              onClick={() => setShowSubmitModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white gap-1.5"
            >
              <Send className="h-3.5 w-3.5" /> Submit Attempt
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Assessment Body: Left Question Content, Right Question Navigator */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Active Question Box */}
        <div className="lg:col-span-3 space-y-4">
          {activeQuestion && (
            <Card className="border-border shadow-md">
              <CardHeader className="p-5 border-b bg-muted/10">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <span className="text-xs font-semibold text-muted-foreground uppercase">
                      Question {currentIndex + 1}
                    </span>
                    <CardTitle className="text-base font-semibold">{activeQuestion.title}</CardTitle>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs flex items-center gap-1">
                      <Award className="h-3 w-3" /> {activeQuestion.points} pts
                    </Badge>
                    {activeQuestion.negative_marks > 0 && (
                      <Badge variant="outline" className="text-xs text-destructive border-destructive/20">
                        -{activeQuestion.negative_marks} neg
                      </Badge>
                    )}
                    <Button
                      variant={flagged.has(activeQuestion.question_version_id) ? "default" : "outline"}
                      size="sm"
                      onClick={() => toggleFlag(activeQuestion.question_version_id)}
                      className="h-7 text-xs gap-1"
                    >
                      <Flag className="h-3 w-3" />
                      {flagged.has(activeQuestion.question_version_id) ? "Flagged" : "Flag"}
                    </Button>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="p-6 space-y-6">
                {/* Prompt */}
                <div className="text-base text-foreground font-medium leading-relaxed bg-muted/20 p-4 rounded-lg border border-border/50">
                  {activeQuestion.prompt}
                </div>

                {activeQuestion.instructions && (
                  <p className="text-xs text-muted-foreground italic">
                    Note: {activeQuestion.instructions}
                  </p>
                )}

                {/* Input Area based on Question Type */}
                {/* 1. Single Choice */}
                {activeQuestion.question_type === "single_choice" && (
                  <div className="space-y-2">
                    {activeQuestion.options.map((opt) => {
                      const currentSelected = answers[activeQuestion.question_version_id]?.selected_option_id;
                      const isChecked = currentSelected === opt.id;
                      return (
                        <label
                          key={opt.id}
                          className={`flex items-center gap-3 p-3.5 rounded-lg border cursor-pointer transition-all ${
                            isChecked
                              ? "border-primary bg-primary/5 shadow-sm"
                              : "border-border hover:border-border/80"
                          }`}
                        >
                          <input
                            type="radio"
                            name={`q_${activeQuestion.question_version_id}`}
                            checked={isChecked}
                            onChange={() => {
                              handleAnswerChange(activeQuestion.question_version_id, {
                                selected_option_id: opt.id,
                              });
                            }}
                            className="h-4 w-4 text-primary"
                          />
                          <span className="text-sm text-foreground">{opt.option_text}</span>
                        </label>
                      );
                    })}
                  </div>
                )}

                {/* 2. Multiple Choice */}
                {activeQuestion.question_type === "multiple_choice" && (
                  <div className="space-y-2">
                    {activeQuestion.options.map((opt) => {
                      const currentSelected = (answers[activeQuestion.question_version_id]?.selected_option_ids as string[]) || [];
                      const isChecked = currentSelected.includes(opt.id);
                      return (
                        <label
                          key={opt.id}
                          className={`flex items-center gap-3 p-3.5 rounded-lg border cursor-pointer transition-all ${
                            isChecked
                              ? "border-primary bg-primary/5 shadow-sm"
                              : "border-border hover:border-border/80"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={(e) => {
                              let next: string[];
                              if (e.target.checked) {
                                next = [...currentSelected, opt.id];
                              } else {
                                next = currentSelected.filter((id) => id !== opt.id);
                              }
                              handleAnswerChange(activeQuestion.question_version_id, {
                                selected_option_ids: next,
                              });
                            }}
                            className="h-4 w-4 text-primary rounded"
                          />
                          <span className="text-sm text-foreground">{opt.option_text}</span>
                        </label>
                      );
                    })}
                  </div>
                )}

                {/* 3. True / False */}
                {activeQuestion.question_type === "true_false" && (
                  <div className="grid grid-cols-2 gap-4">
                    {["True", "False"].map((choice) => {
                      const currentVal = answers[activeQuestion.question_version_id]?.value;
                      const isChecked = currentVal === choice;
                      return (
                        <button
                          key={choice}
                          type="button"
                          onClick={() =>
                            handleAnswerChange(activeQuestion.question_version_id, {
                              value: choice,
                            })
                          }
                          className={`p-4 rounded-lg border font-semibold text-center transition-all ${
                            isChecked
                              ? "border-primary bg-primary/10 text-primary"
                              : "border-border hover:border-border/80 text-foreground"
                          }`}
                        >
                          {choice}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* 4. Numeric Input */}
                {activeQuestion.question_type === "numeric" && (
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">
                      Numerical Value:
                    </label>
                    <Input
                      type="number"
                      step="any"
                      placeholder="Enter exact numerical answer..."
                      value={(answers[activeQuestion.question_version_id]?.value as string) || ""}
                      onChange={(e) =>
                        handleAnswerChange(activeQuestion.question_version_id, {
                          value: e.target.value,
                        })
                      }
                      className="max-w-xs font-mono"
                    />
                  </div>
                )}

                {/* 5. Fill in the Blank */}
                {activeQuestion.question_type === "fill_blank" && (
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">
                      Blank Value:
                    </label>
                    <Input
                      placeholder="Type the exact missing term..."
                      value={(answers[activeQuestion.question_version_id]?.value as string) || ""}
                      onChange={(e) =>
                        handleAnswerChange(activeQuestion.question_version_id, {
                          value: e.target.value,
                        })
                      }
                      className="max-w-md font-mono"
                    />
                  </div>
                )}

                {/* 6. Short / Long Answer */}
                {(activeQuestion.question_type === "short_answer" ||
                  activeQuestion.question_type === "long_answer") && (
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-muted-foreground">
                      Written Response:
                    </label>
                    <textarea
                      rows={activeQuestion.question_type === "long_answer" ? 8 : 4}
                      placeholder="Provide your reasoned institutional response..."
                      value={(answers[activeQuestion.question_version_id]?.text as string) || ""}
                      onChange={(e) =>
                        handleAnswerChange(activeQuestion.question_version_id, {
                          text: e.target.value,
                        })
                      }
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed"
                    />
                  </div>
                )}

                {/* 7. Coding Assessment */}
                {activeQuestion.question_type === "coding" && (
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                        <Code2 className="h-4 w-4 text-primary" /> Source Code Implementation
                      </label>
                      <Badge variant="outline" className="text-xs">
                        Sandbox Verified
                      </Badge>
                    </div>
                    <textarea
                      rows={12}
                      placeholder="// Write your solution function here..."
                      value={(answers[activeQuestion.question_version_id]?.code as string) || ""}
                      onChange={(e) =>
                        handleAnswerChange(activeQuestion.question_version_id, {
                          code: e.target.value,
                        })
                      }
                      className="w-full rounded-md border border-input bg-slate-950 text-slate-100 font-mono text-xs p-3 leading-relaxed"
                    />
                  </div>
                )}
              </CardContent>

              <CardFooter className="p-4 border-t bg-muted/10 flex justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentIndex === 0}
                  onClick={() => setCurrentIndex((i) => i - 1)}
                  className="gap-1"
                >
                  <ChevronLeft className="h-4 w-4" /> Previous
                </Button>

                <Button
                  size="sm"
                  disabled={currentIndex === totalQuestions - 1}
                  onClick={() => setCurrentIndex((i) => i + 1)}
                  className="gap-1"
                >
                  Next <ChevronRight className="h-4 w-4" />
                </Button>
              </CardFooter>
            </Card>
          )}
        </div>

        {/* Sidebar Question Navigation Grid */}
        <div className="space-y-4">
          <Card className="border-border shadow-sm">
            <CardHeader className="p-4 border-b">
              <CardTitle className="text-sm font-semibold">Question Navigator</CardTitle>
              <CardDescription className="text-xs">
                Jump to any question. Autosave is active.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid grid-cols-4 sm:grid-cols-5 gap-2">
                {delivery.questions.map((q, idx) => {
                  const isAnswered = Boolean(answers[q.question_version_id]);
                  const isFlagged = flagged.has(q.question_version_id);
                  const isCurrent = idx === currentIndex;

                  return (
                    <button
                      key={q.question_version_id}
                      type="button"
                      onClick={() => setCurrentIndex(idx)}
                      className={`h-9 w-full rounded-md text-xs font-semibold flex items-center justify-center relative transition-all border ${
                        isCurrent
                          ? "ring-2 ring-primary border-primary bg-primary/20 text-primary"
                          : isAnswered
                          ? "bg-green-600/15 border-green-600/40 text-green-700 dark:text-green-300"
                          : "bg-muted/50 border-border text-foreground hover:bg-muted"
                      }`}
                    >
                      {idx + 1}
                      {isFlagged && (
                        <span className="absolute -top-1 -right-1 h-2.5 w-2.5 bg-amber-500 rounded-full ring-2 ring-background" />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Legend */}
              <div className="mt-4 pt-4 border-t space-y-1.5 text-[11px] text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-green-600/20 border border-green-600/40 inline-block" />
                  <span>Answered ({answeredCount})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-muted/50 border border-border inline-block" />
                  <span>Unanswered ({unansweredCount})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500 inline-block" />
                  <span>Flagged ({flaggedCount})</span>
                </div>
              </div>
            </CardContent>
            <CardFooter className="p-4 border-t bg-muted/5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSubmitModal(true)}
                className="w-full text-xs font-semibold"
              >
                Review &amp; Submit
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <Card className="w-full max-w-md shadow-2xl">
            <CardHeader>
              <CardTitle className="text-lg">Submit Assessment Attempt?</CardTitle>
              <CardDescription>
                Once submitted, responses are immutably frozen and evaluated.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                  <p className="text-xl font-bold text-green-600 dark:text-green-400">
                    {answeredCount}
                  </p>
                  <p className="text-[11px] text-muted-foreground">Answered</p>
                </div>
                <div className="p-3 bg-muted/30 rounded-lg border border-border">
                  <p className="text-xl font-bold text-foreground">{unansweredCount}</p>
                  <p className="text-[11px] text-muted-foreground">Unanswered</p>
                </div>
                <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                  <p className="text-xl font-bold text-amber-600">{flaggedCount}</p>
                  <p className="text-[11px] text-muted-foreground">Flagged</p>
                </div>
              </div>

              {unansweredCount > 0 && (
                <Alert variant="destructive" className="py-2">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    You have {unansweredCount} unanswered questions.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
            <CardFooter className="flex justify-end gap-2 bg-muted/10 p-4 border-t">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSubmitModal(false)}
                disabled={isSubmitting}
              >
                Continue Assessment
              </Button>
              <Button
                size="sm"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                {isSubmitting ? "Scoring..." : "Confirm Final Submission"}
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  );
}
