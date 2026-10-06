"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { AssessmentPlayer } from "@/components/assessment/AssessmentPlayer";
import { startAssessmentAttempt } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Clock } from "lucide-react";

export default function AssessmentAttemptPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params.id as string;

  const [attemptId, setAttemptId] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!assessmentId) return;
    const init = async () => {
      try {
        setLoading(true);
        const attempt = await startAssessmentAttempt(assessmentId);
        setAttemptId(attempt.id);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to initiate assessment attempt.");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [assessmentId]);

  if (loading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center space-y-3 text-muted-foreground">
        <Clock className="h-8 w-8 animate-spin text-primary" />
        <p>Initializing secure attempt session...</p>
      </div>
    );
  }

  if (error || !attemptId) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <Card className="p-8 text-center text-destructive border-destructive/20 space-y-2">
          <p className="font-bold text-lg">Unable to Start Assessment</p>
          <p className="text-sm">{error || "Attempt could not be created."}</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <AssessmentPlayer
        attemptId={attemptId}
        onSubmitted={() => {
          router.push(`/assessments/${assessmentId}/results`);
        }}
        onCancel={() => router.push("/assessments")}
      />
    </div>
  );
}
