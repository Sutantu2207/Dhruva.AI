"use client";

import * as React from "react";
import Link from "next/link";
import {
  Briefcase,
  ExternalLink,
  Mail,
  ShieldCheck,
  Globe,
  Edit3,
  Layers,
  Link2,
  Code2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchMyPortfolio, fetchProjects, fetchMySkillGraph } from "@/lib/api";
import type { StudentPortfolioConfig, StudentProjectSummary, StudentSkillGraphData } from "@/lib/types";

export default function PortfolioPreviewPage() {
  const [portfolio, setPortfolio] = React.useState<StudentPortfolioConfig | null>(null);
  const [projects, setProjects] = React.useState<StudentProjectSummary[]>([]);
  const [skillGraph, setSkillGraph] = React.useState<StudentSkillGraphData | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [portData, projData, graphData] = await Promise.all([
          fetchMyPortfolio(),
          fetchProjects().catch(() => []),
          fetchMySkillGraph().catch(() => null),
        ]);
        setPortfolio(portData);
        setProjects(projData);
        setSkillGraph(graphData);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load preview data");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="container max-w-5xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
          <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !portfolio) {
    return (
      <div className="container max-w-5xl mx-auto px-4 py-8">
        <p className="text-red-500">{error || "Preview unavailable"}</p>
      </div>
    );
  }

  // Filter featured projects if curated, otherwise show non-private projects
  const featured = portfolio.featured_project_ids && portfolio.featured_project_ids.length > 0
    ? projects.filter((p) => portfolio.featured_project_ids.includes(p.id))
    : projects.filter((p) => p.visibility !== "private");

  const verifiedSkills = skillGraph?.skills.filter((s) => s.verification_status === "verified") || [];

  return (
    <div className="container max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800">
        <div className="flex items-center gap-3">
          <EyeIcon />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-indigo-950 dark:text-indigo-200">
                Portfolio Preview Mode
              </span>
              <Badge variant={portfolio.public_visibility ? "default" : "secondary"} className="text-[10px]">
                {portfolio.public_visibility ? "Publicly Live" : "Private Draft"}
              </Badge>
            </div>
            <p className="text-xs text-indigo-800/80 dark:text-indigo-300 mt-0.5">
              This preview matches what recruiters and external peers see. Private projects and internal comments are omitted.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Link href="/portfolio/edit">
            <Button size="sm" variant="outline" className="text-xs gap-1.5">
              <Edit3 className="h-3.5 w-3.5" />
              Edit Settings
            </Button>
          </Link>
          <Link href="/portfolio">
            <Button size="sm" variant="ghost" className="text-xs">
              Exit Preview
            </Button>
          </Link>
        </div>
      </div>

      {/* Portfolio Header Canvas */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 p-8 text-center sm:text-left sm:flex items-start justify-between gap-8 shadow-xs">
        <div className="space-y-3 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-xs font-semibold">
            <Briefcase className="h-3.5 w-3.5" />
            <span>Engineering Portfolio</span>
          </div>

          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {portfolio.headline || "Engineering Student & Developer"}
          </h1>

          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {portfolio.bio || "Building verifiable, production-grade systems and software solutions."}
          </p>

          {/* Social and Contact Links */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            {portfolio.contact_email && (
              <a
                href={`mailto:${portfolio.contact_email}`}
                className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600"
              >
                <Mail className="h-3.5 w-3.5" />
                <span>{portfolio.contact_email}</span>
              </a>
            )}
            {portfolio.social_links?.github && (
              <a
                href={portfolio.social_links.github}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600"
              >
                <Link2 className="h-3.5 w-3.5" />
                <span>GitHub</span>
              </a>
            )}
            {portfolio.social_links?.linkedin && (
              <a
                href={portfolio.social_links.linkedin}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600"
              >
                <Link2 className="h-3.5 w-3.5" />
                <span>LinkedIn</span>
              </a>
            )}
            {portfolio.social_links?.twitter && (
              <a
                href={portfolio.social_links.twitter}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600"
              >
                <Link2 className="h-3.5 w-3.5" />
                <span>Twitter / X</span>
              </a>
            )}
          </div>
        </div>

        {portfolio.slug && (
          <div className="mt-6 sm:mt-0 p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-center shrink-0">
            <p className="text-slate-500 text-[11px]">Public Shareable Handle</p>
            <p className="font-mono font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
              @{portfolio.slug}
            </p>
          </div>
        )}
      </div>

      {/* Featured Projects Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-600" />
            Featured Engineering Projects
          </h2>
          <span className="text-xs text-slate-500">
            {featured.length} project{featured.length !== 1 ? "s" : ""}
          </span>
        </div>

        {featured.length === 0 ? (
          <Card className="border-slate-200 dark:border-slate-800 text-center py-8">
            <CardContent>
              <p className="text-xs text-slate-500">No public or featured projects currently spotlighted.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {featured.map((p) => (
              <Card key={p.id} className="border-slate-200 dark:border-slate-800 flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base font-bold text-slate-900 dark:text-white">
                      {p.title}
                    </CardTitle>
                    {p.is_verified && (
                      <Badge className="bg-emerald-600 text-white text-[10px] shrink-0">
                        Faculty Verified
                      </Badge>
                    )}
                  </div>
                  <CardDescription className="text-xs line-clamp-2 mt-1">
                    {p.short_description || "Applied engineering project."}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4 text-xs">
                  {p.technologies && p.technologies.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {p.technologies.map((t) => (
                        <Badge key={t} variant="secondary" className="text-[10px] py-0">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
                    <span className="text-[11px] text-slate-500 capitalize">
                      {p.project_type}
                    </span>
                    <div className="flex items-center gap-2">
                      {p.repository_url && (
                        <a
                          href={p.repository_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-500 hover:text-indigo-600"
                        >
                          <Code2 className="h-4 w-4" />
                        </a>
                      )}
                      {p.live_url && (
                        <a
                          href={p.live_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-500 hover:text-indigo-600"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                      <Link href={`/projects/${p.id}`}>
                        <Button variant="ghost" size="sm" className="h-7 text-xs">
                          Details
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Verified Skills Section */}
      {verifiedSkills.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              Verified Competencies
            </h2>
            <span className="text-xs text-slate-500">Backing Evidence Authenticated</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {verifiedSkills.map((s) => (
              <div
                key={s.skill_id}
                className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900 dark:text-white">{s.name}</span>
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                </div>
                <p className="text-[11px] text-slate-500 capitalize mt-1">
                  Proficiency: {Math.round(s.verified_proficiency * 100)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function EyeIcon() {
  return (
    <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
      <Globe className="h-5 w-5" />
    </div>
  );
}
