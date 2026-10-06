"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Compass,
  BarChart3,
  GitFork,
  ShieldCheck,
  Search,
  Briefcase,
  Target,
  CheckCircle2,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { CareerIntelligenceCard } from "@/components/career/CareerIntelligenceCard";
import { fetchCatalogCareers, fetchMyCareerGoals, addMyCareerGoal, triggerRecomputeCareer } from "@/lib/api";
import type { CareerCatalog, StudentCareerGoal } from "@/lib/types";

export default function CareerPage() {
  const [careers, setCareers] = React.useState<CareerCatalog[]>([]);
  const [goals, setGoals] = React.useState<StudentCareerGoal[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [search, setSearch] = React.useState<string>("");
  const [selectedIndustry, setSelectedIndustry] = React.useState<string>("all");
  const [settingGoalId, setSettingGoalId] = React.useState<string | null>(null);
  const [refreshKey, setRefreshKey] = React.useState<number>(0);

  const reloadData = React.useCallback(async () => {
    try {
      setLoading(true);
      const [careersRes, goalsRes] = await Promise.all([
        fetchCatalogCareers({ limit: 100 }),
        fetchMyCareerGoals().catch(() => []),
      ]);
      setCareers(careersRes);
      setGoals(goalsRes);
    } catch {
      // Handled silently
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    let ignore = false;
    async function fetchInitial() {
      try {
        const [careersRes, goalsRes] = await Promise.all([
          fetchCatalogCareers({ limit: 100 }),
          fetchMyCareerGoals().catch(() => []),
        ]);
        if (!ignore) {
          setCareers(careersRes);
          setGoals(goalsRes);
        }
      } catch {
        // Handled silently
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }
    fetchInitial();
    return () => {
      ignore = true;
    };
  }, []);

  const activeGoalCareerIds = React.useMemo(() => {
    return new Set(goals.map((g) => g.career_catalog_id));
  }, [goals]);

  const primaryGoalCareerId = React.useMemo(() => {
    if (goals.length === 0) return null;
    const sorted = [...goals].sort((a, b) => a.priority - b.priority);
    return sorted[0].career_catalog_id;
  }, [goals]);

  const industries = React.useMemo(() => {
    const set = new Set<string>();
    for (const c of careers) {
      if (c.industry) set.add(c.industry);
    }
    return Array.from(set).sort();
  }, [careers]);

  const filteredCareers = React.useMemo(() => {
    return careers.filter((c) => {
      const matchSearch =
        search.trim() === "" ||
        c.title.toLowerCase().includes(search.toLowerCase()) ||
        c.code.toLowerCase().includes(search.toLowerCase()) ||
        (c.description && c.description.toLowerCase().includes(search.toLowerCase()));
      const matchIndustry = selectedIndustry === "all" || c.industry === selectedIndustry;
      return matchSearch && matchIndustry;
    });
  }, [careers, search, selectedIndustry]);

  const handleSetTarget = async (careerId: string) => {
    try {
      setSettingGoalId(careerId);
      await addMyCareerGoal({
        career_catalog_id: careerId,
        priority: 1,
      });
      await triggerRecomputeCareer(careerId).catch(() => {});
      await reloadData();
      setRefreshKey((k) => k + 1);
    } catch {
      // Revert loading on error
    } finally {
      setSettingGoalId(null);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl space-y-8">
      {/* Top Header & Navigation */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-600 dark:text-slate-400 mb-1">
              <ArrowLeft className="h-4 w-4" /> Back to Dashboard
            </Button>
          </Link>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Compass className="h-6 w-6 text-indigo-600" />
            Career Intelligence &amp; Target Trajectories
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Authoritative, deterministic career readiness evaluation anchored to National Academic Catalog standards.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link href="/skills">
            <Button variant="outline" size="sm" className="text-xs flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-indigo-600" />
              Verified Skills
            </Button>
          </Link>
          <Link href="/career/readiness">
            <Button variant="outline" size="sm" className="text-xs flex items-center gap-1.5">
              <BarChart3 className="h-3.5 w-3.5 text-indigo-600" />
              Readiness Deep Dive
            </Button>
          </Link>
          <Link href="/career/trajectory">
            <Button variant="outline" size="sm" className="text-xs flex items-center gap-1.5">
              <Compass className="h-3.5 w-3.5 text-indigo-600" />
              Trajectory Sequence
            </Button>
          </Link>
          <Link href="/career/compare">
            <Button variant="outline" size="sm" className="text-xs flex items-center gap-1.5">
              <GitFork className="h-3.5 w-3.5 text-indigo-600" />
              Compare Careers
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Authoritative Career Intelligence Component */}
      <CareerIntelligenceCard key={refreshKey} />

      {/* National Career Pathways & Target Selection */}
      <section className="space-y-4 pt-2">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-indigo-600" />
              National Career Catalog &amp; Target Selection
            </h2>
            <p className="text-xs text-slate-500">
              Browse canonical career pathways mapped by the National Academic Taxonomy. Set your target role to evaluate your profile.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={reloadData}
              className="text-xs"
              disabled={loading}
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1 ${loading ? "animate-spin" : ""}`} />
              Refresh Catalog
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 items-center">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search careers by title, code, or description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 h-9 text-xs"
            />
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-xs text-slate-500 font-medium whitespace-nowrap">Industry:</span>
            <select
              value={selectedIndustry}
              onChange={(e) => setSelectedIndustry(e.target.value)}
              className="h-9 text-xs rounded-md border border-slate-300 bg-white px-2.5 py-1 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
            >
              <option value="all">All Industries ({careers.length})</option>
              {industries.map((ind) => (
                <option key={ind} value={ind}>
                  {ind}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Career Cards Grid */}
        {loading ? (
          <div className="py-12 text-center space-y-3">
            <RefreshCw className="h-6 w-6 animate-spin text-indigo-600 mx-auto" />
            <p className="text-xs text-slate-500 font-medium">Loading canonical career catalog...</p>
          </div>
        ) : filteredCareers.length === 0 ? (
          <Card className="p-8 text-center bg-white dark:bg-slate-900 border-dashed">
            <Briefcase className="h-8 w-8 text-slate-400 mx-auto mb-2" />
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              No matching careers found
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Try adjusting your search query or industry filter.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCareers.map((c) => {
              const isPrimary = c.id === primaryGoalCareerId;
              const isGoal = activeGoalCareerIds.has(c.id);
              const isBusy = settingGoalId === c.id;

              return (
                <Card
                  key={c.id}
                  className={`flex flex-col justify-between transition-shadow hover:shadow-md ${
                    isPrimary
                      ? "border-indigo-400 bg-indigo-50/20 dark:border-indigo-600 dark:bg-indigo-950/20 ring-1 ring-indigo-400/50"
                      : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
                  }`}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Badge variant="outline" className="text-[10px] font-mono uppercase mb-1">
                          {c.code}
                        </Badge>
                        <CardTitle className="text-base font-bold text-slate-900 dark:text-slate-100">
                          {c.title}
                        </CardTitle>
                      </div>
                      {isPrimary ? (
                        <Badge className="bg-indigo-600 text-white text-[10px] font-semibold gap-1 shrink-0">
                          <Target className="h-3 w-3" />
                          Primary Target
                        </Badge>
                      ) : isGoal ? (
                        <Badge variant="secondary" className="text-[10px] font-medium gap-1 shrink-0">
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                          Target Goal
                        </Badge>
                      ) : null}
                    </div>
                    {c.industry && (
                      <CardDescription className="text-xs text-indigo-700 dark:text-indigo-300 font-medium pt-1">
                        {c.industry}
                      </CardDescription>
                    )}
                  </CardHeader>

                  <CardContent className="pb-4 text-xs text-slate-600 dark:text-slate-400">
                    <p className="line-clamp-2">
                      {c.description || "Canonical career pathway defined by the National Academic Catalog."}
                    </p>
                  </CardContent>

                  <CardFooter className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-2">
                    <Link href={`/career/${c.id}`} className="flex-1">
                      <Button variant="ghost" size="sm" className="w-full text-xs gap-1 text-slate-700 dark:text-slate-300">
                        <span>Requirements</span>
                        <ExternalLink className="h-3 w-3" />
                      </Button>
                    </Link>

                    {isPrimary ? (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled
                        className="text-xs text-indigo-700 border-indigo-200 dark:text-indigo-300 dark:border-indigo-800"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 mr-1 text-emerald-600" />
                        Active Goal
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="default"
                        disabled={isBusy}
                        onClick={() => handleSetTarget(c.id)}
                        className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white"
                      >
                        {isBusy ? (
                          <>
                            <RefreshCw className="h-3 w-3 animate-spin mr-1" />
                            Evaluating...
                          </>
                        ) : (
                          <>
                            <Target className="h-3 w-3 mr-1" />
                            Set as Target
                          </>
                        )}
                      </Button>
                    )}
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
