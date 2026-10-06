"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Compass, CheckCircle2, Clock, Lock, AlertCircle, RefreshCw, BookOpen, Layers, FileCheck2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchMyCareerTrajectory } from "@/lib/api";
import type { CareerTrajectory, CareerTrajectoryStep, TrajectoryStepStatus } from "@/lib/types";

export default function CareerTrajectoryPage() {
  const [trajectory, setTrajectory] = React.useState<CareerTrajectory | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let ignore = false;
    async function fetchTrajectory() {
      try {
        const data = await fetchMyCareerTrajectory();
        if (!ignore) {
          setTrajectory(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load trajectory");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    fetchTrajectory();
    return () => {
      ignore = true;
    };
  }, []);

  const getStatusIcon = (status: TrajectoryStepStatus) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
      case "in_progress":
        return <Clock className="h-5 w-5 text-indigo-500 animate-pulse" />;
      case "blocked":
        return <Lock className="h-5 w-5 text-rose-500" />;
      case "not_available":
        return <AlertCircle className="h-5 w-5 text-amber-500" />;
      case "not_started":
      default:
        return <Clock className="h-5 w-5 text-slate-400" />;
    }
  };

  const getStepIcon = (type: string) => {
    switch (type) {
      case "concept_mastery":
        return <BookOpen className="h-4 w-4 text-indigo-600" />;
      case "lesson_learning":
        return <Layers className="h-4 w-4 text-blue-600" />;
      case "skill_assessment":
        return <FileCheck2 className="h-4 w-4 text-emerald-600" />;
      default:
        return <Sparkles className="h-4 w-4 text-purple-600" />;
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-5xl space-y-6">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Link href="/career">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Career Overview
          </Button>
        </Link>
        {trajectory && (
          <Badge variant="outline" className="font-mono text-xs uppercase">
            Engine {trajectory.algorithm_version}
          </Badge>
        )}
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Compass className="h-6 w-6 text-indigo-600" />
          Deterministic Career Trajectory Sequence
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Sequenced learning milestones generated deterministically to close verified skill gaps without hallucinated content.
        </p>
      </div>

      {loading ? (
        <Card className="p-8 text-center bg-white dark:bg-slate-900">
          <RefreshCw className="h-6 w-6 animate-spin text-indigo-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Synthesizing learning path from canonical curriculum mappings...</p>
        </Card>
      ) : error ? (
        <Card className="p-6 text-center text-rose-600 bg-white dark:bg-slate-900">
          <p className="text-xs">{error}</p>
        </Card>
      ) : !trajectory || trajectory.steps.length === 0 ? (
        <Card className="p-8 text-center bg-white dark:bg-slate-900">
          <Compass className="h-8 w-8 text-slate-400 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            No Active Trajectory Path
          </h4>
          <p className="text-xs text-slate-500 mt-1">
            Either no career goal has been set or no mapped learning content is available yet in the academic catalog.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          <Card className="bg-white dark:bg-slate-900">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    Target Career: {trajectory.career_title}
                  </CardTitle>
                  <CardDescription className="text-xs">
                    {trajectory.steps.length} sequential milestone(s) addressing critical and required gaps.
                  </CardDescription>
                </div>
                <Badge variant="secondary" className="capitalize text-xs">
                  Status: {trajectory.status}
                </Badge>
              </div>
            </CardHeader>
          </Card>

          {/* Stepper Timeline */}
          <div className="space-y-3">
            {trajectory.steps.map((step: CareerTrajectoryStep) => (
              <Card
                key={step.id}
                className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-indigo-300 dark:hover:border-indigo-800 transition-all"
              >
                <CardContent className="p-5 flex items-start gap-4">
                  <div className="pt-0.5">{getStatusIcon(step.status)}</div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                          Step 0{step.step_order}
                        </span>
                        <h4 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                          {step.title}
                        </h4>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-[10px] capitalize">
                          {step.priority} Priority
                        </Badge>
                        <Badge
                          variant={step.status === "completed" ? "default" : "secondary"}
                          className="text-[10px] uppercase font-mono"
                        >
                          {step.status}
                        </Badge>
                      </div>
                    </div>

                    {step.description && (
                      <p className="text-xs text-slate-600 dark:text-slate-400">
                        {step.description}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-3 pt-2 text-[11px] text-slate-500 font-mono">
                      <span className="flex items-center gap-1">
                        {getStepIcon(step.step_type)}
                        <span className="capitalize">{step.step_type.replace(/_/g, " ")}</span>
                      </span>

                      {step.lesson_title && (
                        <span>Lesson: {step.lesson_title}</span>
                      )}
                      {step.concept_title && (
                        <span>Concept: {step.concept_title}</span>
                      )}
                      {step.course_title && (
                        <span>Course: {step.course_title}</span>
                      )}
                      {step.reason && (
                        <span className="text-slate-400">({step.reason})</span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
