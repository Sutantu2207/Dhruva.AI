"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, GitFork, RefreshCw, CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { compareCareers, fetchCatalogCareers } from "@/lib/api";
import type { CareerComparisonItem, CareerCatalog } from "@/lib/types";

export default function CareerComparePage() {
  const [catalogCareers, setCatalogCareers] = React.useState<CareerCatalog[]>([]);
  const [selectedIds, setSelectedIds] = React.useState<string[]>([]);
  const [comparison, setComparison] = React.useState<CareerComparisonItem[]>([]);
  const [loadingCatalog, setLoadingCatalog] = React.useState(true);
  const [comparing, setComparing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Load available careers from national catalog
  React.useEffect(() => {
    let ignore = false;
    async function loadCatalog() {
      try {
        const careers = await fetchCatalogCareers({ limit: 50 });
        if (!ignore) {
          setCatalogCareers(careers);
          if (careers.length > 0) {
            setSelectedIds(careers.slice(0, 3).map((c) => c.id));
          }
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to load career catalog");
        }
      } finally {
        if (!ignore) {
          setLoadingCatalog(false);
        }
      }
    }
    loadCatalog();
    return () => {
      ignore = true;
    };
  }, []);

  // When selectedIds changes, execute backend comparison
  React.useEffect(() => {
    if (selectedIds.length === 0) return;
    let ignore = false;
    async function runComparison() {
      try {
        const results = await compareCareers(selectedIds);
        if (!ignore) {
          setComparison(results);
          setError(null);
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Failed to evaluate career comparison");
        }
      } finally {
        if (!ignore) {
          setComparing(false);
        }
      }
    }
    runComparison();
    return () => {
      ignore = true;
    };
  }, [selectedIds]);

  const toggleCareer = (id: string) => {
    setSelectedIds((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      if (next.length === 0) {
        setComparison([]);
      }
      return next;
    });
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl space-y-6">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Link href="/career">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600">
            <ArrowLeft className="h-4 w-4" /> Back to Career Overview
          </Button>
        </Link>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <GitFork className="h-6 w-6 text-indigo-600" />
          Deterministic Career Comparison Matrix
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Side-by-side comparative analysis calculated deterministically by the backend readiness engine.
        </p>
      </div>

      {/* Career Selector */}
      <Card className="bg-white dark:bg-slate-900">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold text-slate-900 dark:text-slate-100">
            Select Careers to Compare (Select 2 or more)
          </CardTitle>
          <CardDescription className="text-xs">
            Toggle careers from your institutional academic catalog to compare required competencies and gaps.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingCatalog ? (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin text-indigo-600" />
              Loading catalog careers...
            </div>
          ) : catalogCareers.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No careers found in academic catalog.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {catalogCareers.map((c) => {
                const isSelected = selectedIds.includes(c.id);
                return (
                  <button
                    key={c.id}
                    onClick={() => toggleCareer(c.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors flex items-center gap-1.5 ${
                      isSelected
                        ? "bg-indigo-600 text-white border-indigo-600 shadow-xs"
                        : "bg-white text-slate-700 border-slate-200 hover:border-indigo-300 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300"
                    }`}
                  >
                    {isSelected && <CheckCircle2 className="h-3.5 w-3.5" />}
                    <span>{c.title}</span>
                  </button>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Comparison Matrix */}
      {comparing ? (
        <Card className="p-8 text-center bg-white dark:bg-slate-900">
          <RefreshCw className="h-6 w-6 animate-spin text-indigo-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Evaluating multi-career readiness matrix...</p>
        </Card>
      ) : error ? (
        <Card className="p-6 text-center text-rose-600 bg-white dark:bg-slate-900">
          <p className="text-xs">{error}</p>
        </Card>
      ) : comparison.length === 0 ? (
        <Card className="p-8 text-center bg-white dark:bg-slate-900">
          <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Select at least one career to view deterministic comparison metrics.</p>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="p-4">Career Goal</th>
                <th className="p-4">Readiness Score</th>
                <th className="p-4">Evidence Confidence</th>
                <th className="p-4">Required Coverage</th>
                <th className="p-4">Critical Coverage</th>
                <th className="p-4">Critical Gaps</th>
                <th className="p-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {comparison.map((item) => {
                const scorePct = Math.round(item.readiness_score * 100);
                const confPct = Math.round(item.confidence * 100);
                const reqPct = Math.round(item.required_skill_coverage * 100);
                const critPct = Math.round(item.critical_skill_coverage * 100);

                return (
                  <tr key={item.career_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="p-4">
                      <div className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                        {item.career_title}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {item.total_skills_count} mapped competencies
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-indigo-600 dark:text-indigo-400 text-base font-mono">
                          {scorePct}%
                        </span>
                        <Progress value={scorePct} className="h-1.5 w-16 bg-slate-100 dark:bg-slate-800" />
                      </div>
                    </td>
                    <td className="p-4 font-mono">
                      <span className="text-emerald-600 font-semibold">{confPct}%</span>
                    </td>
                    <td className="p-4 font-mono">{reqPct}%</td>
                    <td className="p-4 font-mono">{critPct}%</td>
                    <td className="p-4">
                      {item.critical_gaps_count > 0 ? (
                        <Badge variant="destructive" className="font-mono text-[10px]">
                          {item.critical_gaps_count} Blocking
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="border-emerald-200 text-emerald-700 font-mono text-[10px]">
                          0 Gaps
                        </Badge>
                      )}
                    </td>
                    <td className="p-4">
                      <Link href={`/career/${item.career_id}`}>
                        <Button variant="outline" size="sm" className="h-7 text-xs font-semibold">
                          View Details
                        </Button>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="p-4 bg-slate-50/50 dark:bg-slate-800/40 border-t border-slate-200 dark:border-slate-800 flex items-center gap-2 text-[11px] text-slate-500">
            <ShieldCheck className="h-4 w-4 text-indigo-600 shrink-0" />
            <span>
              All scores are evaluated by the authoritative deterministic engine. Ranking never relies on client-side approximations.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
