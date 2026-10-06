"use client";

import * as React from "react";
import Link from "next/link";
import {
  ExternalLink,
  Mail,
  ShieldCheck,
  Award,
  Lock,
  Layers,
  Link2,
  Code2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchPublicPortfolio } from "@/lib/api";
import type { PublicPortfolioData } from "@/lib/types";

interface PublicPortfolioProps {
  params: Promise<{ slug: string }>;
}

export default function PublicPortfolioPage({ params }: PublicPortfolioProps) {
  const resolvedParams = React.use(params);
  const slug = resolvedParams.slug;

  const [portfolio, setPortfolio] = React.useState<PublicPortfolioData | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadPublicData() {
      try {
        setLoading(true);
        const data = await fetchPublicPortfolio(slug);
        setPortfolio(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Portfolio not found or set to private");
      } finally {
        setLoading(false);
      }
    }
    loadPublicData();
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 py-16 px-4">
        <div className="max-w-4xl mx-auto space-y-8 animate-pulse">
          <div className="h-12 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
          <div className="h-48 bg-slate-200 dark:bg-slate-800 rounded"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-56 bg-slate-200 dark:bg-slate-800 rounded"></div>
            <div className="h-56 bg-slate-200 dark:bg-slate-800 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !portfolio) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
        <Card className="max-w-md w-full border-slate-200 dark:border-slate-800 text-center p-6 shadow-sm">
          <div className="p-3 rounded-full bg-slate-100 dark:bg-slate-900 w-fit mx-auto text-slate-500 mb-3">
            <Lock className="h-8 w-8" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            Portfolio Private or Unavailable
          </h1>
          <p className="text-xs text-slate-500 mt-2">
            The requested student portfolio is either private or does not exist on Dhruva.AI.
          </p>
          <Link href="/">
            <Button variant="outline" size="sm" className="mt-6 text-xs">
              Return to Dhruva.AI Home
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 py-12 px-4 selection:bg-indigo-500 selection:text-white">
      <div className="max-w-4xl mx-auto space-y-10">
        {/* Verification Top Pill */}
        <div className="flex items-center justify-between text-xs text-slate-500 border-b border-slate-200 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span>Dhruva.AI Verified Student Profile</span>
          </div>
          <span className="font-mono text-[11px] text-slate-400">@{slug}</span>
        </div>

        {/* Hero Canvas */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 sm:p-10 shadow-xs relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="space-y-4 max-w-2xl">
            <div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
                {portfolio.student_name}
              </h1>
              {portfolio.headline && (
                <p className="text-base font-medium text-indigo-600 dark:text-indigo-400 mt-1">
                  {portfolio.headline}
                </p>
              )}
            </div>

            {portfolio.bio && (
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                {portfolio.bio}
              </p>
            )}

            {/* Social & Contact Bar */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              {portfolio.contact_email && (
                <a
                  href={`mailto:${portfolio.contact_email}`}
                  className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600 transition-colors"
                >
                  <Mail className="h-4 w-4" />
                  <span>{portfolio.contact_email}</span>
                </a>
              )}
              {portfolio.social_links?.github && (
                <a
                  href={portfolio.social_links.github}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600 transition-colors"
                >
                  <Link2 className="h-4 w-4" />
                  <span>GitHub</span>
                </a>
              )}
              {portfolio.social_links?.linkedin && (
                <a
                  href={portfolio.social_links.linkedin}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600 transition-colors"
                >
                  <Link2 className="h-4 w-4" />
                  <span>LinkedIn</span>
                </a>
              )}
              {portfolio.social_links?.twitter && (
                <a
                  href={portfolio.social_links.twitter}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-indigo-600 transition-colors"
                >
                  <Link2 className="h-4 w-4" />
                  <span>Twitter / X</span>
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Featured Projects Section */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-600" />
              Verified Engineering Projects
            </h2>
            <span className="text-xs text-slate-500">
              {portfolio.projects.length} project{portfolio.projects.length !== 1 ? "s" : ""}
            </span>
          </div>

          {portfolio.projects.length === 0 ? (
            <Card className="border-slate-200 dark:border-slate-800 text-center py-8">
              <CardContent>
                <p className="text-xs text-slate-500">No public projects available.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {portfolio.projects.map((p) => (
                <Card
                  key={p.id}
                  className="border-slate-200 dark:border-slate-800 flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-all shadow-xs"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="text-base font-bold text-slate-900 dark:text-white">
                        {p.title}
                      </CardTitle>
                      {p.is_verified && (
                        <Badge className="bg-emerald-600 text-white text-[10px] shrink-0">
                          Verified
                        </Badge>
                      )}
                    </div>
                    {p.short_description && (
                      <CardDescription className="text-xs line-clamp-2 mt-1">
                        {p.short_description}
                      </CardDescription>
                    )}
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
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-slate-500 capitalize">{p.project_type}</span>
                        {p.quality_score !== undefined && (
                          <Badge variant="outline" className="text-[10px]">
                            Quality: {p.quality_score}/100
                          </Badge>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {p.repository_url && (
                          <a
                            href={p.repository_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-slate-500 hover:text-indigo-600 transition-colors"
                            title="Repository"
                          >
                            <Code2 className="h-4 w-4" />
                          </a>
                        )}
                        {p.live_url && (
                          <a
                            href={p.live_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-slate-500 hover:text-indigo-600 transition-colors"
                            title="Live Demo"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>

        {/* Verified Skills Section */}
        {portfolio.skills && portfolio.skills.length > 0 && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-600" />
                Demonstrated & Verified Competencies
              </h2>
              <span className="text-xs text-slate-500">
                {portfolio.skills.length} competencies
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {portfolio.skills.map((s, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900 dark:text-white">{s.name}</span>
                    <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                  </div>
                  <p className="text-[11px] text-slate-500 capitalize mt-1">
                    {s.proficiency} · {s.category || "Skill"}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Certifications Section */}
        {portfolio.certifications && portfolio.certifications.length > 0 && (
          <section className="space-y-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Award className="h-5 w-5 text-amber-600" />
              Verified Certifications
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {portfolio.certifications.map((c, idx) => (
                <Card key={idx} className="border-slate-200 dark:border-slate-800 text-xs">
                  <CardContent className="pt-4 flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold text-slate-900 dark:text-white text-sm">{c.title}</p>
                      <p className="text-slate-500 mt-0.5">{c.issuer}</p>
                      {c.issue_date && (
                        <p className="text-[11px] text-slate-400 mt-1">Issued: {c.issue_date}</p>
                      )}
                    </div>
                    {c.credential_url && (
                      <a
                        href={c.credential_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-600 hover:text-indigo-700 shrink-0"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}

        {/* Verification & Trust Footer */}
        <div className="pt-8 border-t border-slate-200 dark:border-slate-800 text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 text-xs font-semibold">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>Deterministic Verification Powered by Dhruva.AI</span>
          </div>
          <p className="text-[11px] text-slate-400 max-w-md mx-auto">
            Skills, projects, and credentials displayed on this portfolio are authenticated against institutional records and academic evaluation engines.
          </p>
        </div>
      </div>
    </div>
  );
}
