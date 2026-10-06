"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useAuth } from "@/lib/auth-context";
import {
  fetchAssessments,
  startAssessmentAttempt,
  fetchMyAssessmentResults,
  fetchMyConceptEvidence,
  fetchMySkillEvidence,
  fetchMyEnrollments,
} from "@/lib/api";
import type {
  Assessment,
  AssessmentResult,
  ConceptEvidence,
  SkillEvidence,
  StudentEnrollment,
} from "@/lib/types";
import { QuestionBankView } from "./QuestionBankView";
import { AssessmentBuilder } from "./AssessmentBuilder";
import { AssessmentPlayer } from "./AssessmentPlayer";
import { AssessmentResultView } from "./AssessmentResultView";
import {
  ClipboardCheck,
  BookOpen,
  Award,
  Play,
  Clock,
  Layers,
  Sparkles,
  Plus,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

export function AssessmentHub() {
  const { user } = useAuth();
  const isFaculty = user?.role === "teacher" || user?.role === "hod" || user?.role === "institution_admin" || user?.role === "super_admin";

  const [activeTab, setActiveTab] = React.useState<string>(isFaculty ? "assessments" : "my-tests");
  const [assessments, setAssessments] = React.useState<Assessment[]>([]);
  const [enrollments, setEnrollments] = React.useState<StudentEnrollment[]>([]);
  const [results, setResults] = React.useState<AssessmentResult[]>([]);
  const [conceptEvidence, setConceptEvidence] = React.useState<ConceptEvidence[]>([]);
  const [skillEvidence, setSkillEvidence] = React.useState<SkillEvidence[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  // Active Flow State
  const [isBuilding, setIsBuilding] = React.useState<boolean>(false);
  const [activeAttemptId, setActiveAttemptId] = React.useState<string | null>(null);
  const [activeResult, setActiveResult] = React.useState<AssessmentResult | null>(null);

  const refreshData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      if (isFaculty) {
        const asstList = await fetchAssessments();
        setAssessments(asstList);
      } else {
        const [asstList, enrollList, resList, cEv, sEv] = await Promise.all([
          fetchAssessments().catch(() => []),
          fetchMyEnrollments().catch(() => []),
          fetchMyAssessmentResults().catch(() => []),
          fetchMyConceptEvidence().catch(() => []),
          fetchMySkillEvidence().catch(() => []),
        ]);
        setAssessments(asstList);
        setEnrollments(enrollList);
        setResults(resList);
        setConceptEvidence(cEv);
        setSkillEvidence(sEv);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load assessment data");
    } finally {
      setLoading(false);
    }
  }, [isFaculty]);

  React.useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        if (isFaculty) {
          const asstList = await fetchAssessments();
          if (!ignore) setAssessments(asstList);
        } else {
          const [asstList, enrollList, resList, cEv, sEv] = await Promise.all([
            fetchAssessments().catch(() => []),
            fetchMyEnrollments().catch(() => []),
            fetchMyAssessmentResults().catch(() => []),
            fetchMyConceptEvidence().catch(() => []),
            fetchMySkillEvidence().catch(() => []),
          ]);
          if (!ignore) {
            setAssessments(asstList);
            setEnrollments(enrollList);
            setResults(resList);
            setConceptEvidence(cEv);
            setSkillEvidence(sEv);
          }
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load assessment data");
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    loadInitial();
    return () => {
      ignore = true;
    };
  }, [isFaculty]);

  const handleStartAssessment = async (assessmentId: string) => {
    try {
      setLoading(true);
      setError(null);
      const attempt = await startAssessmentAttempt(assessmentId);
      setActiveAttemptId(attempt.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to start assessment attempt");
    } finally {
      setLoading(false);
    }
  };

  // If in an active assessment attempt
  if (activeAttemptId) {
    return (
      <AssessmentPlayer
        attemptId={activeAttemptId}
        onSubmitted={(res) => {
          setActiveAttemptId(null);
          setActiveResult(res);
          refreshData();
        }}
        onCancel={() => setActiveAttemptId(null)}
      />
    );
  }

  // If viewing a single assessment result
  if (activeResult) {
    return (
      <AssessmentResultView
        result={activeResult}
        onBack={() => setActiveResult(null)}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ClipboardCheck className="h-6 w-6 text-primary" />
            Assessment &amp; Evaluation Engine
          </h1>
          <p className="text-sm text-muted-foreground">
            Authoritative, deterministic assessment execution with immutable version freeze and canonical evidence.
          </p>
          {loading && (
            <p className="text-xs text-muted-foreground animate-pulse mt-1">
              Synchronizing authoritative records...
            </p>
          )}
        </div>

        {isFaculty && !isBuilding && (
          <Button onClick={() => setIsBuilding(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            Create Assessment
          </Button>
        )}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Assessment Alert</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Assessment Builder View */}
      {isBuilding ? (
        <div className="space-y-4">
          <AssessmentBuilder
            courseOfferingId={enrollments[0]?.course_offering_id || "default-offering"}
            onSuccess={() => {
              setIsBuilding(false);
              refreshData();
            }}
            onCancel={() => setIsBuilding(false)}
          />
        </div>
      ) : (
        <Tabs defaultValue={isFaculty ? "assessments" : "my-tests"} value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="bg-muted p-1">
            {isFaculty ? (
              <>
                <TabsTrigger value="assessments" className="gap-1.5 text-xs sm:text-sm">
                  <ClipboardCheck className="h-4 w-4" /> Institutional Assessments
                </TabsTrigger>
                <TabsTrigger value="question-banks" className="gap-1.5 text-xs sm:text-sm">
                  <BookOpen className="h-4 w-4" /> Question Banks
                </TabsTrigger>
              </>
            ) : (
              <>
                <TabsTrigger value="my-tests" className="gap-1.5 text-xs sm:text-sm">
                  <Play className="h-4 w-4" /> Available Assessments
                </TabsTrigger>
                <TabsTrigger value="my-results" className="gap-1.5 text-xs sm:text-sm">
                  <Award className="h-4 w-4" /> Graded Results
                </TabsTrigger>
                <TabsTrigger value="my-evidence" className="gap-1.5 text-xs sm:text-sm">
                  <Layers className="h-4 w-4" /> Concept &amp; Skill Evidence
                </TabsTrigger>
              </>
            )}
          </TabsList>

          {/* FACULTY: Assessments List */}
          {isFaculty && (
            <TabsContent value="assessments" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {assessments.length === 0 ? (
                  <Card className="col-span-full p-8 text-center text-muted-foreground">
                    No assessments published yet. Click &quot;Create Assessment&quot; to author one.
                  </Card>
                ) : (
                  assessments.map((asst) => (
                    <Card key={asst.id} className="hover:border-primary/50 transition-all flex flex-col justify-between">
                      <CardHeader className="p-4 pb-2">
                        <div className="flex justify-between items-start gap-2">
                          <Badge variant="outline" className="text-xs uppercase">
                            {asst.assessment_type}
                          </Badge>
                          <Badge
                            variant={
                              asst.status === "open"
                                ? "default"
                                : asst.status === "closed"
                                ? "destructive"
                                : "secondary"
                            }
                            className="text-xs capitalize"
                          >
                            {asst.status}
                          </Badge>
                        </div>
                        <CardTitle className="text-base font-semibold mt-2">{asst.title}</CardTitle>
                        {asst.description && (
                          <CardDescription className="text-xs line-clamp-2">
                            {asst.description}
                          </CardDescription>
                        )}
                      </CardHeader>

                      <CardContent className="p-4 pt-2 text-xs space-y-2 text-muted-foreground">
                        <div className="grid grid-cols-2 gap-2 bg-muted/20 p-2.5 rounded border border-border/50">
                          <div>
                            <span className="text-[11px] block">Duration:</span>
                            <span className="font-semibold text-foreground">{asst.duration_minutes} mins</span>
                          </div>
                          <div>
                            <span className="text-[11px] block">Total Marks:</span>
                            <span className="font-semibold text-foreground">{asst.total_marks} pts</span>
                          </div>
                          <div>
                            <span className="text-[11px] block">Passing:</span>
                            <span className="font-semibold text-foreground">{asst.passing_marks} pts</span>
                          </div>
                          <div>
                            <span className="text-[11px] block">Attempts:</span>
                            <span className="font-semibold text-foreground">{asst.attempts_allowed} max</span>
                          </div>
                        </div>
                      </CardContent>

                      <CardFooter className="p-4 pt-0 border-t bg-muted/5 flex justify-between items-center text-xs">
                        <span className="text-muted-foreground">
                          Policy: {asst.feedback_policy.replace("_", " ")}
                        </span>
                        <Badge variant="outline" className="text-[10px]">
                          v{asst.active_version ? asst.active_version.version_number : 1} Frozen
                        </Badge>
                      </CardFooter>
                    </Card>
                  ))
                )}
              </div>
            </TabsContent>
          )}

          {/* FACULTY: Question Banks Tab */}
          {isFaculty && (
            <TabsContent value="question-banks">
              <QuestionBankView />
            </TabsContent>
          )}

          {/* STUDENT: Available Assessments */}
          {!isFaculty && (
            <TabsContent value="my-tests" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {assessments.length === 0 ? (
                  <Card className="col-span-full p-8 text-center text-muted-foreground">
                    No active assessments available for your enrolled offerings at this time.
                  </Card>
                ) : (
                  assessments.map((asst) => (
                    <Card key={asst.id} className="hover:border-primary/50 transition-all flex flex-col justify-between">
                      <CardHeader className="p-4 pb-2">
                        <div className="flex justify-between items-start gap-2">
                          <Badge variant="outline" className="text-xs uppercase">
                            {asst.assessment_type}
                          </Badge>
                          <Badge
                            variant={asst.status === "open" ? "default" : "secondary"}
                            className="text-xs capitalize"
                          >
                            {asst.status}
                          </Badge>
                        </div>
                        <CardTitle className="text-base font-semibold mt-2">{asst.title}</CardTitle>
                        {asst.description && (
                          <CardDescription className="text-xs line-clamp-2">
                            {asst.description}
                          </CardDescription>
                        )}
                      </CardHeader>

                      <CardContent className="p-4 pt-2 text-xs space-y-2">
                        <div className="flex items-center gap-4 text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3.5 w-3.5 text-primary" /> {asst.duration_minutes} mins
                          </span>
                          <span className="flex items-center gap-1">
                            <Award className="h-3.5 w-3.5 text-primary" /> {asst.total_marks} pts
                          </span>
                        </div>
                        {asst.instructions && (
                          <p className="text-[11px] text-muted-foreground italic line-clamp-2 bg-muted/20 p-2 rounded">
                            {asst.instructions}
                          </p>
                        )}
                      </CardContent>

                      <CardFooter className="p-4 pt-0 border-t bg-muted/5 flex justify-between items-center">
                        <span className="text-xs text-muted-foreground">
                          Passing: {asst.passing_marks} pts
                        </span>
                        <Button
                          size="sm"
                          disabled={asst.status === "closed" || asst.status === "archived"}
                          onClick={() => handleStartAssessment(asst.id)}
                          className="gap-1.5 text-xs"
                        >
                          <Play className="h-3.5 w-3.5" /> Start Attempt
                        </Button>
                      </CardFooter>
                    </Card>
                  ))
                )}
              </div>
            </TabsContent>
          )}

          {/* STUDENT: My Results Tab */}
          {!isFaculty && (
            <TabsContent value="my-results" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.length === 0 ? (
                  <Card className="col-span-full p-8 text-center text-muted-foreground">
                    No graded assessment results released yet. Complete an assessment to receive authoritative evaluations.
                  </Card>
                ) : (
                  results.map((res) => (
                    <Card
                      key={res.id}
                      onClick={() => setActiveResult(res)}
                      className="cursor-pointer hover:border-primary transition-all p-4 space-y-3"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <Badge
                            variant={res.passed ? "default" : "destructive"}
                            className="text-xs gap-1 mb-1"
                          >
                            {res.passed ? <CheckCircle2 className="h-3 w-3" /> : null}
                            {res.passed ? "Passed" : "Needs Review"}
                          </Badge>
                          <h4 className="font-semibold text-sm text-foreground">
                            Assessment Evaluation
                          </h4>
                          <span className="text-xs text-muted-foreground">
                            Evaluated: {new Date(res.evaluated_at).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="text-right">
                          <p className="text-xl font-extrabold text-foreground">
                            {res.raw_marks} / {res.maximum_marks}
                          </p>
                          {res.grade && (
                            <Badge variant="outline" className="font-bold">
                              Grade {res.grade}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="text-xs text-primary font-medium flex justify-end">
                        View Detailed Breakdown →
                      </div>
                    </Card>
                  ))
                )}
              </div>
            </TabsContent>
          )}

          {/* STUDENT: Concept & Skill Evidence Tab */}
          {!isFaculty && (
            <TabsContent value="my-evidence" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Concept Evidence Cards */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                    <Layers className="h-4 w-4 text-primary" />
                    Concept Evidence Records ({conceptEvidence.length})
                  </h3>
                  {conceptEvidence.length === 0 ? (
                    <Card className="p-6 text-center text-xs text-muted-foreground">
                      No concept evidence generated yet.
                    </Card>
                  ) : (
                    conceptEvidence.map((ev) => (
                      <Card key={ev.id} className="p-3 text-xs space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-mono text-muted-foreground truncate max-w-[200px]">
                            Concept: {ev.concept_id.slice(0, 8)}...
                          </span>
                          <Badge variant="outline">Score: {ev.score}</Badge>
                        </div>
                        <p className="text-[11px] text-muted-foreground">
                          Recorded: {new Date(ev.recorded_at).toLocaleString()}
                        </p>
                      </Card>
                    ))
                  )}
                </div>

                {/* Skill Evidence Cards */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-amber-500" />
                    Skill Evidence Records ({skillEvidence.length})
                  </h3>
                  {skillEvidence.length === 0 ? (
                    <Card className="p-6 text-center text-xs text-muted-foreground">
                      No skill evidence generated yet.
                    </Card>
                  ) : (
                    skillEvidence.map((ev) => (
                      <Card key={ev.id} className="p-3 text-xs space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-mono text-muted-foreground truncate max-w-[200px]">
                            Skill: {ev.skill_id.slice(0, 8)}...
                          </span>
                          <Badge variant="outline">Score: {ev.score}</Badge>
                        </div>
                        <p className="text-[11px] text-muted-foreground">
                          Recorded: {new Date(ev.recorded_at).toLocaleString()}
                        </p>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            </TabsContent>
          )}
        </Tabs>
      )}
    </div>
  );
}
