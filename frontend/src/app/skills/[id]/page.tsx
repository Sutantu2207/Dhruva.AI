"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, CheckCircle2, ShieldAlert, ShieldCheck, RefreshCw, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { fetchSkillDetail } from "@/lib/api";
import type { StudentSkillIntelligence } from "@/lib/types";

export default function SkillDetailPage() {
  const params = useParams();
  const skillId = params.id as string;

  const [skill, setSkill] = React.useState<StudentSkillIntelligence | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let ignore = false;
    async function fetchDetail() {
      try {
        const data = await fetchSkillDetail(skillId);
        if (!ignore) {
          setSkill(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load skill details");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    fetchDetail();
    return () => {
      ignore = true;
    };
  }, [skillId]);

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-5xl text-center space-y-4">
        <RefreshCw className="h-6 w-6 animate-spin text-indigo-600 mx-auto" />
        <p className="text-xs text-slate-500">Retrieving authoritative skill provenance...</p>
      </div>
    );
  }

  if (error || !skill) {
    return (
      <div className="container mx-auto p-6 max-w-5xl space-y-4">
        <Link href="/skills">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Skills
          </Button>
        </Link>
        <Card className="p-6 text-center text-rose-600 bg-white dark:bg-slate-900">
          <p className="text-xs">{error || "Skill intelligence not found"}</p>
        </Card>
      </div>
    );
  }

  const observedPct = Math.round(skill.observed_proficiency * 100);
  const verifiedPct = Math.round(skill.verified_proficiency * 100);
  const confidencePct = Math.round(skill.confidence * 100);

  return (
    <div className="container mx-auto p-6 max-w-5xl space-y-6">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Link href="/skills">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Verified Skills
          </Button>
        </Link>
        <Badge variant="outline" className="font-mono text-xs uppercase">
          Engine {skill.algorithm_version}
        </Badge>
      </div>

      {/* Main Header Card */}
      <Card className="bg-white dark:bg-slate-900 border-indigo-100 dark:border-indigo-900/40">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {skill.skill_name}
                </CardTitle>
                <Badge variant="outline" className="font-mono text-xs">
                  {skill.skill_code}
                </Badge>
              </div>
              <CardDescription className="text-xs mt-1">
                Deterministic competence evaluated across {skill.evidence_count} evidence records ({skill.verified_evidence_count} verified).
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="capitalize text-xs px-3 py-1 font-semibold">
                Tier: {skill.proficiency_tier}
              </Badge>
              <Badge
                variant={skill.verification_status === "verified" ? "default" : "outline"}
                className={`text-xs px-3 py-1 uppercase font-semibold ${
                  skill.verification_status === "verified"
                    ? "bg-emerald-600 text-white"
                    : "border-amber-300 text-amber-700"
                }`}
              >
                {skill.verification_status}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg border border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-800/50">
              <span className="text-xs text-slate-500 font-medium block">Verified Proficiency</span>
              <div className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400 font-mono mt-1">
                {verifiedPct}%
              </div>
              <Progress value={verifiedPct} className="h-2 mt-2 bg-slate-200 dark:bg-slate-700" />
              <p className="text-[10px] text-slate-400 mt-1">Weighted evidence discounted by variance</p>
            </div>

            <div className="p-4 rounded-lg border border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-800/50">
              <span className="text-xs text-slate-500 font-medium block">Observed Proficiency</span>
              <div className="text-3xl font-extrabold text-slate-800 dark:text-slate-200 font-mono mt-1">
                {observedPct}%
              </div>
              <Progress value={observedPct} className="h-2 mt-2 bg-slate-200 dark:bg-slate-700" />
              <p className="text-[10px] text-slate-400 mt-1">Raw multi-source weighted aggregation</p>
            </div>

            <div className="p-4 rounded-lg border border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-800/50">
              <span className="text-xs text-slate-500 font-medium block">Evidence Confidence</span>
              <div className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono mt-1">
                {confidencePct}%
              </div>
              <Progress value={confidencePct} className="h-2 mt-2 bg-slate-200 dark:bg-slate-700" />
              <p className="text-[10px] text-slate-400 mt-1">Based on volume and source diversity</p>
            </div>
          </div>

          {/* Explainability Panel */}
          <div className="rounded-xl border border-indigo-100 bg-indigo-50/20 p-5 dark:border-indigo-900/30 dark:bg-indigo-950/10">
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900 dark:text-indigo-200 mb-2 flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-indigo-600" />
              Deterministic Explainability Factors
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-slate-500 block">Assessment Records</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{skill.assessment_evidence_count}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Project Records</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{skill.project_evidence_count}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Course Completions</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{skill.course_evidence_count}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Concept Contribution</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">
                  {Math.round(skill.concept_mastery_contribution * 100)}%
                </span>
              </div>
            </div>
          </div>

          {/* Evidence Records Table */}
          <div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4 text-slate-600" />
              Evidence Provenance Records ({skill.evidence_records?.length ?? 0})
            </h4>

            {(!skill.evidence_records || skill.evidence_records.length === 0) ? (
              <p className="text-xs text-slate-400 italic">No granular evidence records logged.</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="p-3">Source Type</th>
                      <th className="p-3">Normalized Score</th>
                      <th className="p-3">Strength</th>
                      <th className="p-3">Weight</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Recorded At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {skill.evidence_records.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="p-3 font-mono font-medium capitalize">{r.source_type.replace(/_/g, " ")}</td>
                        <td className="p-3 font-mono">{Math.round(r.normalized_score * 100)}%</td>
                        <td className="p-3 font-mono">{Math.round(r.evidence_strength * 100)}%</td>
                        <td className="p-3 font-mono">{r.weight.toFixed(2)}</td>
                        <td className="p-3">
                          {r.verified ? (
                            <span className="flex items-center gap-1 text-emerald-600 font-semibold text-[11px]">
                              <CheckCircle2 className="h-3 w-3" /> Verified
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-slate-400 text-[11px]">
                              <ShieldAlert className="h-3 w-3" /> Recorded
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-slate-400 font-mono text-[11px]">
                          {new Date(r.recorded_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
