"use client";

import * as React from "react";
import Link from "next/link";
import {
  Briefcase,
  AlertTriangle,
  ExternalLink,
  Edit3,
  Eye,
  ShieldCheck,
  Sparkles,
  BookOpen,
  Award,
  Layers,
  FileCheck2,
  TrendingUp,
  Globe,
  Lock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { fetchMyPortfolio, fetchMyPortfolioHealth } from "@/lib/api";
import type { StudentPortfolioConfig, PortfolioHealthData } from "@/lib/types";

export default function PortfolioHubPage() {
  const [portfolio, setPortfolio] = React.useState<StudentPortfolioConfig | null>(null);
  const [health, setHealth] = React.useState<PortfolioHealthData | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadPortfolioData() {
      try {
        setLoading(true);
        const [portData, healthData] = await Promise.all([
          fetchMyPortfolio(),
          fetchMyPortfolioHealth(),
        ]);
        setPortfolio(portData);
        setHealth(healthData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load portfolio data");
      } finally {
        setLoading(false);
      }
    }
    loadPortfolioData();
  }, []);

  if (loading) {
    return (
      <div className="container max-w-7xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
          <div className="h-40 bg-slate-200 dark:bg-slate-800 rounded"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded"></div>
            <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !portfolio || !health) {
    return (
      <div className="container max-w-7xl mx-auto px-4 py-8">
        <Card className="border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/20">
          <CardContent className="pt-6 text-center text-red-600 dark:text-red-400">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
            <p className="font-semibold">{error || "Portfolio data unavailable"}</p>
            <p className="text-sm mt-1">Please ensure your student profile exists in Dhruva.AI.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isAssessed = health.status === "assessed" && health.overall_health_score !== null;

  const healthDimensions = [
    { label: "Technical Depth", score: health.technical_depth, icon: Layers },
    { label: "Project Diversity", score: health.project_diversity, icon: Briefcase },
    { label: "Evidence Quality", score: health.evidence_quality, icon: FileCheck2 },
    { label: "Documentation", score: health.documentation_quality, icon: BookOpen },
    { label: "Career Alignment", score: health.career_alignment, icon: TrendingUp },
    { label: "Professional Presence", score: health.professional_presence, icon: Globe },
    { label: "Verification Coverage", score: health.verification_coverage, icon: ShieldCheck },
  ];

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
              <Briefcase className="h-5 w-5" />
            </span>
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
              Domain 8 Portfolio Engine
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Portfolio Intelligence Hub
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Curate verified evidence, evaluate employer readiness, and publish your public engineering portfolio.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/portfolio/edit">
            <Button variant="outline" size="sm" className="gap-2">
              <Edit3 className="h-4 w-4" />
              Customize Portfolio
            </Button>
          </Link>
          <Link href="/portfolio/preview">
            <Button variant="outline" size="sm" className="gap-2">
              <Eye className="h-4 w-4" />
              Private Preview
            </Button>
          </Link>
          {portfolio.public_visibility && portfolio.slug && (
            <Link href={`/portfolio/public/${portfolio.slug}`} target="_blank">
              <Button size="sm" className="gap-2 bg-indigo-600 hover:bg-indigo-700">
                <Globe className="h-4 w-4" />
                Live Portfolio
                <ExternalLink className="h-3.5 w-3.5 ml-0.5" />
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Portfolio Public Visibility Banner */}
      <Card className="border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40">
        <CardContent className="pt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${portfolio.public_visibility ? "bg-emerald-500/10 text-emerald-600" : "bg-slate-200 dark:bg-slate-800 text-slate-500"}`}>
              {portfolio.public_visibility ? <Globe className="h-6 w-6" /> : <Lock className="h-6 w-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm text-slate-900 dark:text-white">
                  Visibility: {portfolio.public_visibility ? "Public" : "Private"}
                </span>
                <Badge variant={portfolio.public_visibility ? "default" : "secondary"} className={`text-[10px] ${portfolio.public_visibility ? "bg-emerald-600" : ""}`}>
                  {portfolio.public_visibility ? "Live at public URL" : "Private to you and institution"}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {portfolio.slug ? `Custom URL: /portfolio/public/${portfolio.slug}` : "Slug not assigned yet"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/portfolio/edit">
              <Button size="sm" variant="ghost" className="text-xs">
                Change Visibility Settings
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Health Status & Score Section */}
      {!isAssessed ? (
        <Card className="border-amber-200 dark:border-amber-900 bg-amber-50/50 dark:bg-amber-950/20">
          <CardHeader>
            <CardTitle className="text-amber-900 dark:text-amber-300 flex items-center gap-2 text-base">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              Insufficient Evidence for Complete Health Assessment
            </CardTitle>
            <CardDescription className="text-amber-800/80 dark:text-amber-400 text-xs">
              Dhruva.AI never fabricates arbitrary scores. Add engineering projects and submit verification artifacts to unlock your portfolio health metrics.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Link href="/projects/new">
                <Button size="sm" className="bg-amber-600 hover:bg-amber-700 text-white text-xs">
                  Create First Project
                </Button>
              </Link>
              <Link href="/skills/graph">
                <Button size="sm" variant="outline" className="border-amber-300 text-amber-800 text-xs">
                  Inspect Skill Graph
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Health Card */}
          <Card className="lg:col-span-5 border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
            <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-6 text-white text-center">
              <Badge variant="outline" className="border-indigo-400 text-indigo-200 text-xs mb-3">
                Algorithm {health.algorithm_version}
              </Badge>
              <div className="text-5xl font-black text-white mt-1">
                {health.overall_health_score}
                <span className="text-xl font-normal text-indigo-300">/100</span>
              </div>
              <p className="text-xs text-indigo-200 mt-2 font-medium">Overall Portfolio Health</p>
              <p className="text-[11px] text-slate-300 mt-1 max-w-xs mx-auto">
                Deterministic synthesis of engineering depth, documentation, verified evidence, and career alignment.
              </p>
            </div>

            <CardContent className="p-6 space-y-4">
              <div>
                <div className="flex items-center justify-between text-xs font-semibold mb-1">
                  <span>Profile & Portfolio Completeness</span>
                  <span>{health.completeness_score}%</span>
                </div>
                <Progress value={health.completeness_score} className="h-2" />
              </div>

              {health.missing_sections.length > 0 && (
                <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Missing Elements:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {health.missing_sections.map((sec) => (
                      <Badge key={sec} variant="outline" className="text-[10px] capitalize text-amber-700 dark:text-amber-400 border-amber-300">
                        + {sec.replace(/_/g, " ")}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Granular Dimensions */}
          <Card className="lg:col-span-7 border-slate-200 dark:border-slate-800 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold">Health Dimensions Breakdown</CardTitle>
              <CardDescription className="text-xs">
                Each dimension is calculated deterministically from verified repository and academic records.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {healthDimensions.map((dim) => {
                  const Icon = dim.icon;
                  const val = dim.score !== null ? dim.score : 0;
                  return (
                    <div
                      key={dim.label}
                      className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <Icon className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                          {dim.label}
                        </span>
                        <span className="font-bold text-slate-900 dark:text-white">
                          {dim.score !== null ? `${dim.score}/100` : "N/A"}
                        </span>
                      </div>
                      <Progress value={val} className="h-1.5 mt-2" />
                    </div>
                  );
                })}
              </div>

              {/* Recommendations */}
              {health.recommendations.length > 0 && (
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-2">
                  <p className="text-xs font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                    Actionable Improvements
                  </p>
                  <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-400">
                    {health.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-indigo-500 font-bold">•</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Featured Configuration Snapshot */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-indigo-600" />
              Featured Projects
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-600 dark:text-slate-400">
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {portfolio.featured_project_ids?.length || 0}
            </p>
            <p className="mt-1">Projects highlighted on your public portfolio page.</p>
            <Link href="/projects">
              <Button variant="ghost" size="sm" className="h-7 text-xs px-0 text-indigo-600 mt-2">
                Manage Projects →
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Featured Skills
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-600 dark:text-slate-400">
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {portfolio.featured_skill_ids?.length || 0}
            </p>
            <p className="mt-1">Skills verified by assessments or faculty review.</p>
            <Link href="/skills/graph">
              <Button variant="ghost" size="sm" className="h-7 text-xs px-0 text-indigo-600 mt-2">
                Inspect Skill Graph →
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Award className="h-4 w-4 text-amber-600" />
              Certifications & Awards
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-600 dark:text-slate-400">
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {(portfolio.featured_certification_ids?.length || 0) + (portfolio.featured_achievement_ids?.length || 0)}
            </p>
            <p className="mt-1">Credentials verified in your student profile.</p>
            <Link href="/portfolio/edit">
              <Button variant="ghost" size="sm" className="h-7 text-xs px-0 text-indigo-600 mt-2">
                Update Sections →
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
