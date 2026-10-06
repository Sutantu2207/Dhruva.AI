"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Award, CheckCircle2, RefreshCw, Search, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { fetchMySkillIntelligence, triggerRecomputeSkills } from "@/lib/api";
import type { StudentSkillIntelligence, ProficiencyTier } from "@/lib/types";

export default function SkillsPage() {
  const [skills, setSkills] = React.useState<StudentSkillIntelligence[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [search, setSearch] = React.useState("");
  const [selectedTier, setSelectedTier] = React.useState<string>("all");

  const loadSkills = React.useCallback(async () => {
    try {
      const data = await fetchMySkillIntelligence();
      setSkills(data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load skills");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    let ignore = false;
    async function fetchInitial() {
      try {
        const data = await fetchMySkillIntelligence();
        if (!ignore) {
          setSkills(data);
          setError(null);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load skills");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }
    fetchInitial();
    return () => {
      ignore = true;
    };
  }, []);

  const handleRecompute = async () => {
    setRefreshing(true);
    try {
      await triggerRecomputeSkills();
      await loadSkills();
    } catch {
      await loadSkills();
    }
  };

  const filteredSkills = skills.filter((s) => {
    const matchesSearch =
      s.skill_name.toLowerCase().includes(search.toLowerCase()) ||
      s.skill_code.toLowerCase().includes(search.toLowerCase());
    const matchesTier = selectedTier === "all" || s.proficiency_tier === selectedTier;
    return matchesSearch && matchesTier;
  });

  const verifiedCount = skills.filter((s) => s.verification_status === "verified").length;
  const proficientCount = skills.filter(
    (s) => s.proficiency_tier === "proficient" || s.proficiency_tier === "advanced"
  ).length;

  const getTierColor = (tier: ProficiencyTier) => {
    switch (tier) {
      case "advanced":
        return "bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-950/40 dark:text-purple-300";
      case "proficient":
        return "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300";
      case "developing":
        return "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300";
      case "beginner":
        return "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-950/40 dark:text-blue-300";
      case "exposure":
      default:
        return "bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300";
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl space-y-6">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Link href="/dashboard">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Dashboard
          </Button>
        </Link>
        <div className="flex items-center gap-2">
          <Link href="/career">
            <Button variant="outline" size="sm" className="text-xs">
              Career Trajectories
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRecompute}
            disabled={refreshing}
            className="text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1 ${refreshing ? "animate-spin" : ""}`} />
            Recompute Skills
          </Button>
        </div>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-indigo-600" />
          Verified Skill Intelligence
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Deterministic competencies evaluated from assessment attempts, project artifacts, concept mastery states, and certifications.
        </p>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-white dark:bg-slate-900">
          <CardContent className="pt-4 pb-3">
            <span className="text-xs font-medium text-slate-500">Evaluated Skills</span>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-0.5">
              {skills.length}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white dark:bg-slate-900">
          <CardContent className="pt-4 pb-3">
            <span className="text-xs font-medium text-slate-500">Proficient / Advanced</span>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
              {proficientCount}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white dark:bg-slate-900">
          <CardContent className="pt-4 pb-3">
            <span className="text-xs font-medium text-slate-500">Fully Verified</span>
            <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
              {verifiedCount}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white dark:bg-slate-900">
          <CardContent className="pt-4 pb-3">
            <span className="text-xs font-medium text-slate-500">Algorithm Engine</span>
            <div className="text-sm font-bold text-slate-700 dark:text-slate-300 font-mono mt-1">
              v1.0.0-deterministic
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search skills by name or code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1">
          {["all", "advanced", "proficient", "developing", "beginner", "exposure"].map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-3 py-1 rounded-md text-xs font-medium capitalize transition-colors ${
                selectedTier === tier
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
              }`}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      {/* Skills Grid */}
      {loading ? (
        <Card className="p-8 text-center bg-white dark:bg-slate-900">
          <RefreshCw className="h-6 w-6 animate-spin text-indigo-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Evaluating multi-source skill intelligence...</p>
        </Card>
      ) : error ? (
        <Card className="p-6 text-center text-rose-600 bg-white dark:bg-slate-900">
          <p className="text-xs">{error}</p>
        </Card>
      ) : filteredSkills.length === 0 ? (
        <Card className="p-8 text-center bg-white dark:bg-slate-900">
          <Award className="h-8 w-8 text-slate-400 mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">No skills match your filter</h4>
          <p className="text-xs text-slate-500 mt-1">Complete assessments or link projects to generate authoritative skill evidence.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSkills.map((s) => {
            const observedPct = Math.round(s.observed_proficiency * 100);
            const verifiedPct = Math.round(s.verified_proficiency * 100);
            const confidencePct = Math.round(s.confidence * 100);

            return (
              <Card
                key={s.id}
                className="bg-white dark:bg-slate-900 hover:border-indigo-300 dark:hover:border-indigo-800 transition-all flex flex-col justify-between"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {s.skill_name}
                      </CardTitle>
                      <CardDescription className="font-mono text-[10px] text-slate-400">
                        {s.skill_code}
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className={`text-[10px] capitalize font-semibold ${getTierColor(s.proficiency_tier)}`}>
                      {s.proficiency_tier}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4 pt-0">
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Verified Proficiency</span>
                      <span className="font-bold text-indigo-600 dark:text-indigo-400 font-mono">
                        {verifiedPct}%
                      </span>
                    </div>
                    <Progress value={verifiedPct} className="h-2 bg-slate-100 dark:bg-slate-800" />
                    <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                      <span>Observed: {observedPct}%</span>
                      <span>Confidence: {confidencePct}%</span>
                    </div>
                  </div>

                  {/* Evidence Distribution */}
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-1 text-[10px] text-slate-500">
                    <div>
                      <span className="block text-slate-400">Assessments</span>
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        {s.assessment_evidence_count}
                      </span>
                    </div>
                    <div>
                      <span className="block text-slate-400">Projects</span>
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        {s.project_evidence_count}
                      </span>
                    </div>
                    <div>
                      <span className="block text-slate-400">Mastery</span>
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        {Math.round(s.concept_mastery_contribution * 100)}%
                      </span>
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase text-slate-400 flex items-center gap-1">
                      {s.verification_status === "verified" && <CheckCircle2 className="h-3 w-3 text-emerald-500" />}
                      {s.verification_status}
                    </span>
                    <Link href={`/skills/${s.skill_id}`}>
                      <Button variant="ghost" size="sm" className="h-7 text-xs text-indigo-600 font-semibold px-2">
                        View Provenance →
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
