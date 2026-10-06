"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  fetchQuestionBanks,
  fetchQuestions,
  createAssessment,
  publishAssessment,
} from "@/lib/api";
import type {
  QuestionBank,
  Question,
  AssessmentType,
  Assessment,
} from "@/lib/types";
import {
  ClipboardList,
  CheckCircle2,
  Clock,
  Award,
  ChevronRight,
  ChevronLeft,
  AlertCircle,
  FileCheck2,
} from "lucide-react";

interface AssessmentBuilderProps {
  courseOfferingId: string;
  onSuccess?: (assessment: Assessment) => void;
  onCancel?: () => void;
}

export function AssessmentBuilder({
  courseOfferingId,
  onSuccess,
  onCancel,
}: AssessmentBuilderProps) {
  const [step, setStep] = React.useState<number>(1);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  // Step 1: Info
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [instructions, setInstructions] = React.useState("");
  const [assessmentType, setAssessmentType] = React.useState<AssessmentType>("quiz");

  // Step 2: Questions Selection
  const [banks, setBanks] = React.useState<QuestionBank[]>([]);
  const [selectedBankId, setSelectedBankId] = React.useState<string>("");
  const [bankQuestions, setBankQuestions] = React.useState<Question[]>([]);
  const [selectedQuestionVersionIds, setSelectedQuestionVersionIds] = React.useState<string[]>([]);
  const [selectedQuestionsMap, setSelectedQuestionsMap] = React.useState<Map<string, Question>>(new Map());

  // Step 3: Timing & Scoring
  const [durationMinutes, setDurationMinutes] = React.useState<number>(30);
  const [passingMarks, setPassingMarks] = React.useState<number>(10);
  const [attemptsAllowed, setAttemptsAllowed] = React.useState<number>(1);

  // Step 4: Feedback
  const [feedbackPolicy, setFeedbackPolicy] = React.useState<string>("after_submission");

  // Load Banks
  React.useEffect(() => {
    const loadBanks = async () => {
      try {
        const data = await fetchQuestionBanks();
        setBanks(data);
        if (data.length > 0) {
          setSelectedBankId(data[0].id);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load banks");
      }
    };
    loadBanks();
  }, []);

  // Load Questions when Bank Changes
  React.useEffect(() => {
    if (!selectedBankId) return;
    const loadQ = async () => {
      try {
        const qList = await fetchQuestions(selectedBankId);
        setBankQuestions(qList);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load questions");
      }
    };
    loadQ();
  }, [selectedBankId]);

  // Total Marks derived from selected questions
  const totalMarks = React.useMemo(() => {
    let sum = 0;
    selectedQuestionsMap.forEach((q) => {
      if (q.current_version) {
        sum += Number(q.current_version.points || 0);
      }
    });
    return sum;
  }, [selectedQuestionsMap]);

  const toggleQuestion = (q: Question) => {
    const verId = q.current_version_id;
    if (!verId) return;

    const newSet = new Set(selectedQuestionVersionIds);
    const newMap = new Map(selectedQuestionsMap);

    if (newSet.has(verId)) {
      newSet.delete(verId);
      newMap.delete(verId);
    } else {
      newSet.add(verId);
      newMap.set(verId, q);
    }

    setSelectedQuestionVersionIds(Array.from(newSet));
    setSelectedQuestionsMap(newMap);
  };

  const handlePublish = async () => {
    try {
      setLoading(true);
      setError(null);

      if (selectedQuestionVersionIds.length === 0) {
        throw new Error("Please select at least one question before publishing.");
      }

      // 1. Create Assessment
      const createdAssessment = await createAssessment({
        course_offering_id: courseOfferingId,
        title: title.trim(),
        description: description.trim() || undefined,
        instructions: instructions.trim() || undefined,
        assessment_type: assessmentType,
        duration_minutes: Number(durationMinutes),
        total_marks: Number(totalMarks),
        passing_marks: Number(passingMarks),
        attempts_allowed: Number(attemptsAllowed),
        feedback_policy: feedbackPolicy,
      });

      // 2. Publish Assessment with Version Snapshot
      await publishAssessment(createdAssessment.id, {
        question_version_ids: selectedQuestionVersionIds,
        duration_minutes: Number(durationMinutes),
        total_marks: Number(totalMarks),
        passing_marks: Number(passingMarks),
      });

      if (onSuccess) {
        onSuccess(createdAssessment);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to publish assessment");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full border-border shadow-md">
      <CardHeader className="border-b bg-card">
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-xl flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-primary" />
              Assessment Authoring Studio
            </CardTitle>
            <CardDescription>
              Step {step} of 5 — Multi-step authoring with immutable version freeze.
            </CardDescription>
          </div>
          {/* Progress Indicator */}
          <div className="flex items-center gap-1.5">
            {[1, 2, 3, 4, 5].map((s) => (
              <div
                key={s}
                className={`h-2 rounded-full transition-all ${
                  s === step
                    ? "w-8 bg-primary"
                    : s < step
                    ? "w-2 bg-primary/60"
                    : "w-2 bg-muted"
                }`}
              />
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Validation Alert</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Step 1: Basic Information */}
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">
              Step 1: Assessment Identity
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold">Assessment Title *</label>
                <Input
                  placeholder="e.g. Midterm Algorithmic Evaluation"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold">Assessment Type *</label>
                <select
                  value={assessmentType}
                  onChange={(e) => setAssessmentType(e.target.value as AssessmentType)}
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                >
                  <option value="quiz">Quiz</option>
                  <option value="practice">Practice Test</option>
                  <option value="assignment">Assignment</option>
                  <option value="internal">Internal Assessment</option>
                  <option value="midterm">Midterm Examination</option>
                  <option value="end_semester">End Semester Examination</option>
                  <option value="diagnostic">Diagnostic Assessment</option>
                  <option value="skill_assessment">Skill Assessment</option>
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold">Description</label>
              <textarea
                rows={2}
                placeholder="Brief summary of the topics covered..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold">Student Instructions</label>
              <textarea
                rows={3}
                placeholder="Instructions on navigation, timing, negative marking, and submission..."
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
          </div>
        )}

        {/* Step 2: Question Selection */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">
                  Step 2: Select Questions from Question Bank
                </h3>
                <p className="text-xs text-muted-foreground">
                  Selected: {selectedQuestionVersionIds.length} question(s) | Total Points: {totalMarks} pts
                </p>
              </div>
              {banks.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Bank:</span>
                  <select
                    value={selectedBankId}
                    onChange={(e) => setSelectedBankId(e.target.value)}
                    className="text-xs h-8 px-2 rounded-md border border-input bg-background"
                  >
                    {banks.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.title}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {bankQuestions.length === 0 ? (
                <div className="text-center p-8 border border-dashed rounded-lg text-sm text-muted-foreground">
                  No questions found in this bank. Author questions in the Question Bank first.
                </div>
              ) : (
                bankQuestions.map((q) => {
                  const ver = q.current_version;
                  const isSelected = ver ? selectedQuestionVersionIds.includes(ver.id) : false;
                  return (
                    <div
                      key={q.id}
                      onClick={() => toggleQuestion(q)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all flex items-start gap-3 ${
                        isSelected
                          ? "border-primary bg-primary/5 shadow-sm"
                          : "border-border hover:border-border/80"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}} // Handled by div onClick
                        className="mt-1"
                      />
                      <div className="flex-1 space-y-1">
                        <div className="flex justify-between items-start">
                          <p className="text-sm font-semibold text-foreground">{q.title}</p>
                          <div className="flex items-center gap-1.5">
                            <Badge variant="outline" className="text-xs capitalize">
                              {q.question_type.replace("_", " ")}
                            </Badge>
                            {ver && (
                              <Badge variant="secondary" className="text-xs">
                                {ver.points} pts
                              </Badge>
                            )}
                          </div>
                        </div>
                        {ver && (
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {ver.prompt}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* Step 3: Timing & Scoring */}
        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">
              Step 3: Timing &amp; Passing Constraints
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-primary" /> Duration (Minutes) *
                </label>
                <Input
                  type="number"
                  min={5}
                  max={300}
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                />
                <p className="text-[11px] text-muted-foreground">Server-calculated expiry window.</p>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold flex items-center gap-1">
                  <Award className="h-3.5 w-3.5 text-primary" /> Total Marks
                </label>
                <Input type="number" readOnly value={totalMarks} className="bg-muted/50 font-semibold" />
                <p className="text-[11px] text-muted-foreground">Summed from selected questions.</p>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold">Passing Marks *</label>
                <Input
                  type="number"
                  min={0}
                  max={totalMarks || 100}
                  value={passingMarks}
                  onChange={(e) => setPassingMarks(Number(e.target.value))}
                />
                <p className="text-[11px] text-muted-foreground">Deterministic threshold for pass/fail.</p>
              </div>
            </div>

            <div className="space-y-1 sm:w-1/3">
              <label className="text-xs font-semibold">Allowed Attempts</label>
              <Input
                type="number"
                min={1}
                max={10}
                value={attemptsAllowed}
                onChange={(e) => setAttemptsAllowed(Number(e.target.value))}
              />
            </div>
          </div>
        )}

        {/* Step 4: Feedback Policy */}
        {step === 4 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">
              Step 4: Answer Key &amp; Feedback Policy
            </h3>
            <p className="text-xs text-muted-foreground">
              Controls when students are allowed to view answer explanations and question-level breakdowns. Correct answer keys are NEVER exposed during active attempts.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                {
                  id: "after_submission",
                  title: "After Submission",
                  desc: "Detailed explanations released immediately once the student submits.",
                },
                {
                  id: "after_release",
                  title: "After Official Release",
                  desc: "Results and explanations withheld until instructor explicitly publishes grades.",
                },
                {
                  id: "immediate_feedback",
                  title: "Immediate Practice Feedback",
                  desc: "Ideal for low-stakes drills; shows immediate hints upon answer submission.",
                },
                {
                  id: "never",
                  title: "Score Only (Never)",
                  desc: "Exposes only final score and grade. Answer keys remain confidential.",
                },
              ].map((policy) => (
                <div
                  key={policy.id}
                  onClick={() => setFeedbackPolicy(policy.id)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    feedbackPolicy === policy.id
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-border hover:border-border/80"
                  }`}
                >
                  <p className="font-semibold text-sm">{policy.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{policy.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 5: Review & Publish */}
        {step === 5 && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground flex items-center gap-2">
              <FileCheck2 className="h-4 w-4 text-green-600" />
              Step 5: Review &amp; Immutable Version Freeze
            </h3>
            <Card className="bg-muted/20 border-border p-4 space-y-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-muted-foreground">Title:</span>
                  <p className="font-semibold text-foreground">{title || "Untitled"}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Type:</span>
                  <p className="font-semibold capitalize text-foreground">{assessmentType}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Duration:</span>
                  <p className="font-semibold text-foreground">{durationMinutes} mins</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Questions:</span>
                  <p className="font-semibold text-foreground">{selectedQuestionVersionIds.length} items</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Total Marks:</span>
                  <p className="font-semibold text-foreground">{totalMarks} pts</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Passing Marks:</span>
                  <p className="font-semibold text-foreground">{passingMarks} pts</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Attempts:</span>
                  <p className="font-semibold text-foreground">{attemptsAllowed}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Feedback Policy:</span>
                  <p className="font-semibold capitalize text-foreground">{feedbackPolicy.replace("_", " ")}</p>
                </div>
              </div>

              <div className="border-t pt-2 text-xs text-muted-foreground">
                <p className="font-medium text-foreground mb-1">
                  Architectural Principle Enforcement:
                </p>
                <ul className="list-disc list-inside space-y-0.5">
                  <li>Publishing creates an immutable <code>AssessmentVersion</code> snapshot.</li>
                  <li>Historical student attempts will permanently reference this exact snapshot.</li>
                  <li>Authoritative scoring will be deterministically calculated by the backend engine.</li>
                </ul>
              </div>
            </Card>
          </div>
        )}
      </CardContent>

      <CardFooter className="border-t bg-muted/10 p-4 flex justify-between">
        <div>
          {onCancel && (
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          {step > 1 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setStep((s) => s - 1)}
              className="gap-1"
            >
              <ChevronLeft className="h-4 w-4" /> Back
            </Button>
          )}
          {step < 5 ? (
            <Button
              size="sm"
              onClick={() => {
                if (step === 1 && !title.trim()) {
                  setError("Assessment title is required.");
                  return;
                }
                if (step === 2 && selectedQuestionVersionIds.length === 0) {
                  setError("Select at least one question to proceed.");
                  return;
                }
                setError(null);
                setStep((s) => s + 1);
              }}
              className="gap-1"
            >
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handlePublish}
              disabled={loading}
              className="gap-1 bg-green-600 hover:bg-green-700 text-white"
            >
              <CheckCircle2 className="h-4 w-4" />
              {loading ? "Publishing..." : "Publish Assessment"}
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}
