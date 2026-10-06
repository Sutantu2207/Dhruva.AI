"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AssessmentResult } from "@/lib/types";
import {
  CheckCircle2,
  XCircle,
  Layers,
  Sparkles,
  ShieldCheck,
  FileText,
  Clock,
} from "lucide-react";

interface AssessmentResultViewProps {
  result: AssessmentResult;
  onBack?: () => void;
}

export function AssessmentResultView({ result, onBack }: AssessmentResultViewProps) {
  const isPassed = result.passed;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Banner: Score & Grade Card */}
      <Card className="border-border shadow-lg overflow-hidden">
        <div
          className={`h-2.5 ${
            isPassed ? "bg-green-500" : "bg-destructive"
          }`}
        />
        <CardHeader className="p-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Badge
                  variant={isPassed ? "default" : "destructive"}
                  className="capitalize gap-1 text-xs"
                >
                  {isPassed ? (
                    <CheckCircle2 className="h-3 w-3" />
                  ) : (
                    <XCircle className="h-3 w-3" />
                  )}
                  {isPassed ? "Passed" : "Needs Remediation"}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {result.release_status}
                </Badge>
              </div>
              <CardTitle className="text-2xl font-bold">Assessment Evaluation Result</CardTitle>
              <CardDescription className="flex items-center gap-1.5 text-xs mt-1">
                <Clock className="h-3.5 w-3.5" /> Evaluated:{" "}
                {new Date(result.evaluated_at).toLocaleString()}
              </CardDescription>
            </div>

            {/* Score pill */}
            <div className="flex items-baseline gap-3 bg-muted/40 p-3.5 rounded-xl border border-border">
              <div className="text-right">
                <p className="text-xs text-muted-foreground uppercase font-semibold">Earned Marks</p>
                <p className="text-3xl font-extrabold text-foreground">
                  {result.raw_marks}{" "}
                  <span className="text-sm font-normal text-muted-foreground">
                    / {result.maximum_marks}
                  </span>
                </p>
              </div>
              {result.grade && (
                <div className="border-l pl-3 text-center">
                  <p className="text-xs text-muted-foreground uppercase font-semibold">Grade</p>
                  <p className="text-3xl font-black text-primary">{result.grade}</p>
                </div>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="px-6 pb-6 pt-0">
          <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
            <div
              className={`h-full transition-all ${
                isPassed ? "bg-green-500" : "bg-amber-500"
              }`}
              style={{ width: `${Math.min(100, Math.max(0, result.percentage))}%` }}
            />
          </div>
          <div className="flex justify-between items-center text-xs text-muted-foreground mt-2">
            <span>Score Percentage: {result.percentage}%</span>
            <span>Threshold Met: {result.passed ? "Yes" : "No"}</span>
          </div>
        </CardContent>
      </Card>

      {/* Question Breakdown List */}
      {result.question_breakdown && result.question_breakdown.length > 0 && (
        <Card className="border-border shadow-sm">
          <CardHeader className="p-5 border-b">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              Question Performance Breakdown
            </CardTitle>
            <CardDescription className="text-xs">
              Authoritative scoring details evaluated via deterministic rules or certified faculty rubrics.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 space-y-3">
            {result.question_breakdown.map((item, idx) => {
              const isFull = item.earned_marks === item.maximum_marks;
              const isZero = item.earned_marks <= 0;
              return (
                <div
                  key={idx}
                  className="p-4 rounded-lg border border-border bg-card hover:border-border/80 space-y-2"
                >
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground">
                        Item #{idx + 1}
                      </p>
                      <p className="text-sm font-medium text-foreground">
                        {item.question_title || "Evaluated Assessment Question"}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge
                        variant={isFull ? "default" : isZero ? "destructive" : "secondary"}
                        className="text-xs"
                      >
                        {item.earned_marks} / {item.maximum_marks} pts
                      </Badge>
                      <p className="text-[10px] text-muted-foreground mt-1 capitalize">
                        {item.evaluator_type.replace("_", " ")}
                      </p>
                    </div>
                  </div>

                  {item.explanation && (
                    <div className="p-2.5 rounded bg-muted/30 border border-border/50 text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground">Rationale: </span>
                      {item.explanation}
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Deterministic Evidence Records: Concept & Skill */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Concept Evidence */}
        <Card className="border-border shadow-sm">
          <CardHeader className="p-4 border-b">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" />
              Generated Concept Evidence ({result.concept_evidence?.length || 0})
            </CardTitle>
            <CardDescription className="text-xs">
              Immutable provenance records for Domain 6 Knowledge State tracking.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-2">
            {!result.concept_evidence || result.concept_evidence.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">No concept evidence generated.</p>
            ) : (
              result.concept_evidence.map((c) => (
                <div
                  key={c.id}
                  className="flex justify-between items-center p-2 rounded bg-muted/20 border border-border/50 text-xs"
                >
                  <span className="font-mono text-[11px] truncate max-w-[200px]">
                    Concept: {c.concept_id.slice(0, 8)}...
                  </span>
                  <Badge variant="outline" className="font-mono text-xs">
                    Score: {c.score}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Skill Evidence */}
        <Card className="border-border shadow-sm">
          <CardHeader className="p-4 border-b">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-500" />
              Generated Skill Evidence ({result.skill_evidence?.length || 0})
            </CardTitle>
            <CardDescription className="text-xs">
              Authoritative skill evidence mapped to National SkillCatalog.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-2">
            {!result.skill_evidence || result.skill_evidence.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">No skill evidence generated.</p>
            ) : (
              result.skill_evidence.map((s) => (
                <div
                  key={s.id}
                  className="flex justify-between items-center p-2 rounded bg-muted/20 border border-border/50 text-xs"
                >
                  <span className="font-mono text-[11px] truncate max-w-[200px]">
                    Skill: {s.skill_id.slice(0, 8)}...
                  </span>
                  <Badge variant="outline" className="font-mono text-xs">
                    Score: {s.score}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Provenance & Deterministic Integrity Footer */}
      <Card className="border-border/60 bg-muted/10 p-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-4 w-4 text-green-600 shrink-0" />
          <span>
            Scoring Integrity Guarantee: All marks are authoritative, deterministic, and immutably
            recorded. AI does not possess authority to modify student scores or pass/fail thresholds.
          </span>
        </div>
      </Card>

      {onBack && (
        <div className="flex justify-start">
          <Button variant="outline" size="sm" onClick={onBack}>
            ← Back to Assessments
          </Button>
        </div>
      )}
    </div>
  );
}
