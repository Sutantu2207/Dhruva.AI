"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Save,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { fetchMyPortfolio, updateMyPortfolio, fetchProjects } from "@/lib/api";
import type { StudentProjectSummary } from "@/lib/types";

export default function PortfolioEditPage() {
  const router = useRouter();
  const [availableProjects, setAvailableProjects] = React.useState<StudentProjectSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [success, setSuccess] = React.useState(false);

  // Form state
  const [headline, setHeadline] = React.useState("");
  const [bio, setBio] = React.useState("");
  const [slug, setSlug] = React.useState("");
  const [theme, setTheme] = React.useState("modern");
  const [publicVisibility, setPublicVisibility] = React.useState(false);
  const [contactEmail, setContactEmail] = React.useState("");
  const [githubUrl, setGithubUrl] = React.useState("");
  const [linkedinUrl, setLinkedinUrl] = React.useState("");
  const [twitterUrl, setTwitterUrl] = React.useState("");
  const [selectedProjectIds, setSelectedProjectIds] = React.useState<string[]>([]);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [portData, projData] = await Promise.all([
          fetchMyPortfolio(),
          fetchProjects().catch(() => []),
        ]);
        setAvailableProjects(projData);

        // Pre-fill
        setHeadline(portData.headline || "");
        setBio(portData.bio || "");
        setSlug(portData.slug || "");
        setTheme(portData.theme || "modern");
        setPublicVisibility(portData.public_visibility || false);
        setContactEmail(portData.contact_email || "");
        setSelectedProjectIds(portData.featured_project_ids || []);

        if (portData.social_links) {
          setGithubUrl(portData.social_links.github || "");
          setLinkedinUrl(portData.social_links.linkedin || "");
          setTwitterUrl(portData.social_links.twitter || "");
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load portfolio settings");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleToggleProject = (projId: string) => {
    setSelectedProjectIds((prev) =>
      prev.includes(projId) ? prev.filter((id) => id !== projId) : [...prev, projId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);

      const socialLinks: Record<string, string> = {};
      if (githubUrl.trim()) socialLinks.github = githubUrl.trim();
      if (linkedinUrl.trim()) socialLinks.linkedin = linkedinUrl.trim();
      if (twitterUrl.trim()) socialLinks.twitter = twitterUrl.trim();

      await updateMyPortfolio({
        headline: headline.trim() || undefined,
        bio: bio.trim() || undefined,
        slug: slug.trim() || undefined,
        theme,
        public_visibility: publicVisibility,
        contact_email: contactEmail.trim() || undefined,
        social_links: socialLinks,
        featured_project_ids: selectedProjectIds,
      });

      setSuccess(true);
      setTimeout(() => {
        router.push("/portfolio");
      }, 1000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save portfolio settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="container max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
          <div className="h-96 bg-slate-200 dark:bg-slate-800 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl mx-auto px-4 py-8 space-y-6">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Link href="/portfolio">
          <Button variant="ghost" size="sm" className="gap-2 text-slate-600 dark:text-slate-400">
            <ArrowLeft className="h-4 w-4" />
            Back to Portfolio Hub
          </Button>
        </Link>
        <Link href="/portfolio/preview">
          <Button variant="outline" size="sm">
            Preview Changes
          </Button>
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Customize Your Engineering Portfolio
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Configure profile presentation, vanity slug, public visibility, and curate featured engineering projects.
        </p>
      </div>

      {error && (
        <Card className="border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/20">
          <CardContent className="pt-4 text-xs text-red-600 dark:text-red-400 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </CardContent>
        </Card>
      )}

      {success && (
        <Card className="border-emerald-200 dark:border-emerald-900 bg-emerald-50/50 dark:bg-emerald-950/20">
          <CardContent className="pt-4 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>Portfolio settings updated successfully! Redirecting...</span>
          </CardContent>
        </Card>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Profile Branding */}
        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Profile & Headline</CardTitle>
            <CardDescription className="text-xs">
              Displayed prominently at the top of your portfolio.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Headline / Professional Title
              </label>
              <Input
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="e.g. Distributed Systems Engineer & Full-Stack Developer"
                className="text-xs"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Professional Bio & Statement
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows={4}
                placeholder="Describe your engineering focus, key interests, and foundational skills..."
                className="w-full rounded-md border border-slate-300 dark:border-slate-700 bg-transparent px-3 py-2 text-xs focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Vanity Slug / Handle
                </label>
                <Input
                  value={slug}
                  onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ""))}
                  placeholder="e.g. alex-chen"
                  className="text-xs font-mono"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Public URL: /portfolio/public/{slug || "your-slug"}
                </p>
              </div>

              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Theme Style
                </label>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  className="w-full h-9 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-xs focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="modern">Modern Glassmorphism</option>
                  <option value="minimal">Minimal Clean</option>
                  <option value="dark_terminal">Terminal Dark</option>
                  <option value="classic">Academic Classic</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Visibility & Security */}
        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center justify-between">
              <span>Public Visibility & Privacy Guard</span>
              {publicVisibility ? (
                <Badge className="bg-emerald-600 text-white text-[10px]">Public Live</Badge>
              ) : (
                <Badge variant="secondary" className="text-[10px]">Private</Badge>
              )}
            </CardTitle>
            <CardDescription className="text-xs">
              Dhruva.AI enforces strict privacy boundaries. Even when public, private assessment details, internal intervention records, and faculty feedback notes are never revealed.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
              <input
                type="checkbox"
                id="public_toggle"
                checked={publicVisibility}
                onChange={(e) => setPublicVisibility(e.target.checked)}
                className="h-4 w-4 rounded text-indigo-600 focus:ring-indigo-500"
              />
              <label htmlFor="public_toggle" className="cursor-pointer">
                <span className="font-semibold text-slate-900 dark:text-white block">
                  Enable Public Portfolio Page
                </span>
                <span className="text-slate-500 text-[11px]">
                  Allow recruiters and external employers to view your public projects, verified skills, and certifications at your vanity slug.
                </span>
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Contact & Social Links */}
        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Contact & Social Links</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Contact Email
              </label>
              <Input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="e.g. your.email@example.com"
                className="text-xs"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  GitHub Profile URL
                </label>
                <Input
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/..."
                  className="text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  LinkedIn URL
                </label>
                <Input
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/..."
                  className="text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Twitter / X URL
                </label>
                <Input
                  value={twitterUrl}
                  onChange={(e) => setTwitterUrl(e.target.value)}
                  placeholder="https://x.com/..."
                  className="text-xs"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Curated Projects Selector */}
        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Curate Featured Projects</CardTitle>
            <CardDescription className="text-xs">
              Select which projects to spotlight in your portfolio. Only projects with visibility set to &quot;public&quot; or &quot;institution&quot; can be displayed externally.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            {availableProjects.length === 0 ? (
              <p className="text-slate-400 italic">No projects found. Create a project first.</p>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {availableProjects.map((p) => {
                  const isChecked = selectedProjectIds.includes(p.id);
                  return (
                    <div
                      key={p.id}
                      onClick={() => handleToggleProject(p.id)}
                      className={`p-3 rounded-lg border cursor-pointer flex items-center justify-between transition-colors ${
                        isChecked
                          ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/40"
                          : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="h-4 w-4 rounded text-indigo-600"
                        />
                        <div>
                          <p className="font-semibold text-slate-900 dark:text-white">{p.title}</p>
                          <p className="text-[11px] text-slate-500 capitalize">
                            Type: {p.project_type} · Visibility: {p.visibility}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {p.is_verified && (
                          <Badge className="bg-emerald-600 text-white text-[10px]">
                            Verified
                          </Badge>
                        )}
                        {p.quality_score !== undefined && (
                          <Badge variant="outline" className="text-[10px]">
                            Quality: {p.quality_score}
                          </Badge>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submit Bar */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
          <Link href="/portfolio">
            <Button variant="outline" type="button" size="sm">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={saving}
            size="sm"
            className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : "Save Portfolio Settings"}
          </Button>
        </div>
      </form>
    </div>
  );
}
