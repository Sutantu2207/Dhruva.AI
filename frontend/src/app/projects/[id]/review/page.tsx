"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Award,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchProjectDetail, submitProjectReview } from "@/lib/api";
import type { StudentProjectDetail } from "@/lib/types";

interface RubricDimension {
  key: string;
  label: string;
  description: string;
  weight: string;
}

const RUBRIC_CRITERIA: RubricDimension[] = [
  { key: "technical_depth", label: "Technical Depth", description: "Complexity of algorithms, concurrency, system scale, and technologies leveraged.", weight: "15%" },
  { key: "problem_solving", label: "Problem Solving", description: "Analytical depth, domain challenge comprehension, and edge case handling.", weight: "10%" },
  { key: "code_quality", label: "Code Quality & Idioms", description: "Modularity, maintainability, linting conformance, and type safety.", weight: "10%" },
  { key: "architecture_quality", label: "Architecture & Systems Design", description: "Component decoupling, data schemas, API contracts, and scalability.", weight: "15%" },
  { key: "documentation_quality", label: "Documentation & Specifications", description: "README clarity, architecture diagrams, API specs, and setup instructions.", weight: "10%" },
  { key: "testing_quality", label: "Testing & Reliability", description: "Unit tests, integration pipelines, automated coverage, and validation rigor.", weight: "10%" },
  { key: "practical_application", label: "Practical Application", description: "Viability in production, real-world utility, and deployment execution.", weight: "10%" },
  { key: "originality", label: "Originality & Innovation", description: "Independent problem framing vs boilerplate code reproduction.", weight: "5%" },
  { key: "student_contribution_score", label: "Student Individual Contribution", description: "Demonstrable execution of specific personal modules in team scope.", weight: "10%" },
  { key: "professional_presentation", label: "Professional Presentation", description: "Polished UI/UX, video walkthrough clarity, and professional readiness.", weight: "5%" },
];

export default function ProjectReviewPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = React.useState<StudentProjectDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Rubric Scores (default 75 each)
  const [scores, setScores] = React.useState<Record<string, number>>({
    technical_depth: 80,
    problem_solving: 75,
    code_quality: 80,
    architecture_quality: 80,
    documentation_quality: 75,
    testing_quality: 70,
    practical_application: 80,
    originality: 75,
    student_contribution_score: 85,
    professional_presentation: 75,
  });

  const [decision, setDecision] = React.useState<"approved" | "rejected" | "revisions_requested">("approved");
  const [feedback, setFeedback] = React.useState("");

  React.useEffect(() => {
    if (!projectId) return;
    let active = true;
    fetchProjectDetail(projectId)
      .then((data) => {
        if (active) {
          setProject(data);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load project");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  const handleScoreChange = (key: string, val: number) => {
    setScores((prev) => ({ ...prev, [key]: val }));
  };

  const calculatedAverage = Math.round(
    Object.values(scores).reduce((a, b) => a + b, 0) / RUBRIC_CRITERIA.length
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await submitProjectReview(projectId, {
        review_type: "faculty",
        technical_depth: scores.technical_depth,
        problem_solving: scores.problem_solving,
        code_quality: scores.code_quality,
        architecture_quality: scores.architecture_quality,
        documentation_quality: scores.documentation_quality,
        testing_quality: scores.testing_quality,
        practical_application: scores.practical_application,
        originality: scores.originality,
        student_contribution_score: scores.student_contribution_score,
        professional_presentation: scores.professional_presentation,
        decision,
        feedback: feedback.trim() || undefined,
      });

      router.push(`/projects/${projectId}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Review submission failed");
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex items-center justify-center font-mono text-sm text-slate-400">
        Loading project review interface...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-6 space-y-2">
        <Link
          href={`/projects/${projectId}`}
          className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to {project?.title || "Project"}
        </Link>
        <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs tracking-wider uppercase">
          <Award className="w-4 h-4" /> Faculty Rubric Review Engine
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">
          Evaluate Project: {project?.title}
        </h1>
        <p className="text-sm text-slate-400">
          Faculty and mentor evaluations are immutable and directly feed verified practical evidence into the student&apos;s
          Domain 7 Skill Intelligence state.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-900 text-rose-300 text-sm font-mono flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Evaluation Form */}
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Rubric Criteria List */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle className="text-base font-bold text-slate-200">
                10-Criterion Structured Rubric
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Score each dimension from 0 to 100 based on verifiable evidence.
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-indigo-400 font-mono">
                {calculatedAverage}/100
              </div>
              <div className="text-[10px] font-mono text-slate-500 uppercase">Composite Average</div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 pt-2">
            {RUBRIC_CRITERIA.map((criterion) => {
              const currentScore = scores[criterion.key] || 0;
              return (
                <div
                  key={criterion.key}
                  className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2.5"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div>
                      <div className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                        {criterion.label}
                        <Badge variant="outline" className="text-[10px] font-mono border-slate-700 text-slate-400">
                          Weight: {criterion.weight}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{criterion.description}</p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={currentScore}
                        onChange={(e) => handleScoreChange(criterion.key, parseInt(e.target.value))}
                        className="w-32 md:w-44 accent-indigo-500"
                      />
                      <span className="font-mono font-bold text-sm w-12 text-right text-indigo-300">
                        {currentScore}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Decision & Written Qualitative Feedback */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-200">
              Evaluation Decision & Qualitative Critique
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-2">
                Official Review Decision
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => setDecision("approved")}
                  className={`p-3 rounded-xl border text-left transition flex items-center gap-2.5 ${
                    decision === "approved"
                      ? "bg-emerald-950/60 border-emerald-600 text-emerald-200"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <div>
                    <div className="font-bold text-xs uppercase font-mono">Approve & Verify</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">Marks project as faculty verified</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setDecision("revisions_requested")}
                  className={`p-3 rounded-xl border text-left transition flex items-center gap-2.5 ${
                    decision === "revisions_requested"
                      ? "bg-amber-950/60 border-amber-600 text-amber-200"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                  <div>
                    <div className="font-bold text-xs uppercase font-mono">Request Revisions</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">Leaves project under review</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setDecision("rejected")}
                  className={`p-3 rounded-xl border text-left transition flex items-center gap-2.5 ${
                    decision === "rejected"
                      ? "bg-rose-950/60 border-rose-600 text-rose-200"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <div>
                    <div className="font-bold text-xs uppercase font-mono">Reject</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">Fails verification standards</div>
                  </div>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                Detailed Faculty Feedback
              </label>
              <textarea
                rows={4}
                placeholder="Provide constructive technical critique highlighting architecture strengths, testing gaps, and career trajectory relevance..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm p-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <Link href={`/projects/${projectId}`}>
            <Button variant="outline" type="button" className="border-slate-700 text-slate-300">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={submitting}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-6 shadow-lg shadow-indigo-600/20"
          >
            <Save className="w-4 h-4 mr-2" />
            {submitting ? "Finalizing Review..." : "Finalize Rubric Review"}
          </Button>
        </div>
      </form>
    </div>
  );
}
