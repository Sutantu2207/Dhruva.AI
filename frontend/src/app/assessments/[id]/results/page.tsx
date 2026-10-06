"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { AssessmentResultView } from "@/components/assessment/AssessmentResultView";
import { fetchMyAssessmentResults } from "@/lib/api";
import type { AssessmentResult } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Clock } from "lucide-react";

export default function AssessmentResultsPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params.id as string;

  const [result, setResult] = React.useState<AssessmentResult | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!assessmentId) return;
    const load = async () => {
      try {
        setLoading(true);
        const results = await fetchMyAssessmentResults();
        const found = results.find((r) => r.assessment_id === assessmentId);
        if (found) {
          setResult(found);
        } else {
          setError("No released evaluation results found for this assessment yet.");
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load results.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [assessmentId]);

  if (loading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center space-y-3 text-muted-foreground">
        <Clock className="h-8 w-8 animate-spin text-primary" />
        <p>Loading authoritative assessment results...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <Card className="p-8 text-center text-muted-foreground space-y-2">
          <p className="font-bold text-lg text-foreground">Results Notice</p>
          <p className="text-sm">{error || "Results currently unavailable."}</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <AssessmentResultView
        result={result}
        onBack={() => router.push("/assessments")}
      />
    </div>
  );
}
