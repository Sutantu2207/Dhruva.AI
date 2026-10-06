"use client";

import * as React from "react";
import Link from "next/link";
import {
  FolderGit2,
  Plus,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ExternalLink,
  Code2,
  Layers,
  Sparkles,
  BarChart3,
  Search,
  Filter,
  Globe,
  Lock,
  Building,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { fetchProjects } from "@/lib/api";
import type { StudentProjectSummary } from "@/lib/types";

export default function ProjectsPage() {
  const [projects, setProjects] = React.useState<StudentProjectSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [search, setSearch] = React.useState("");
  const [selectedType, setSelectedType] = React.useState<string>("all");
  const [selectedStatus, setSelectedStatus] = React.useState<string>("all");

  React.useEffect(() => {
    let active = true;
    fetchProjects()
      .then((data) => {
        if (active) {
          setProjects(data);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load projects");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      (p.technologies && p.technologies.some((t) => t.toLowerCase().includes(search.toLowerCase()))) ||
      (p.short_description && p.short_description.toLowerCase().includes(search.toLowerCase()));
    const matchesType = selectedType === "all" || p.project_type === selectedType;
    const matchesStatus = selectedStatus === "all" || p.status === selectedStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  const totalCount = projects.length;
  const verifiedCount = projects.filter((p) => p.is_verified).length;
  const inProgressCount = projects.filter((p) => p.status === "in_progress").length;
  const completedCount = projects.filter((p) => p.status === "completed").length;
  const avgQualityScore =
    projects.filter((p) => p.quality_score !== null && p.quality_score !== undefined).length > 0
      ? Math.round(
          projects.reduce((acc, p) => acc + (p.quality_score || 0), 0) /
            projects.filter((p) => p.quality_score !== null && p.quality_score !== undefined).length
        )
      : null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs tracking-wider uppercase mb-1">
            <FolderGit2 className="w-4 h-4" /> Domain 8 Project Intelligence
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-slate-100 via-slate-200 to-indigo-300 bg-clip-text text-transparent">
            Student Project Portfolio & Evidence
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Authoritative, empirical evidence proving practical execution. Deterministically evaluated across
            technical depth, architecture, testing, and career relevance.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/skills/graph">
            <Button variant="outline" className="border-indigo-500/30 text-indigo-300 hover:bg-indigo-950/40">
              <BarChart3 className="w-4 h-4 mr-2" /> Skill Graph
            </Button>
          </Link>
          <Link href="/portfolio">
            <Button variant="outline" className="border-slate-700 hover:bg-slate-800 text-slate-200">
              <Layers className="w-4 h-4 mr-2" /> Portfolio Hub
            </Button>
          </Link>
          <Link href="/projects/new">
            <Button className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-lg shadow-indigo-600/20">
              <Plus className="w-4 h-4 mr-2" /> New Project
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-slate-900/60 border-slate-800">
          <CardContent className="pt-6">
            <div className="text-xs font-mono uppercase text-slate-400">Total Projects</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">{totalCount}</div>
            <div className="text-xs text-slate-500 mt-1">Authoritative records</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900/60 border-emerald-950/40">
          <CardContent className="pt-6">
            <div className="text-xs font-mono uppercase text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Faculty Verified
            </div>
            <div className="text-2xl font-bold text-emerald-300 mt-1">{verifiedCount}</div>
            <div className="text-xs text-slate-500 mt-1">
              {totalCount > 0 ? `${Math.round((verifiedCount / totalCount) * 100)}% verified` : "No projects"}
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900/60 border-slate-800">
          <CardContent className="pt-6">
            <div className="text-xs font-mono uppercase text-amber-400 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> In Progress
            </div>
            <div className="text-2xl font-bold text-amber-300 mt-1">{inProgressCount}</div>
            <div className="text-xs text-slate-500 mt-1">Active implementations</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900/60 border-slate-800">
          <CardContent className="pt-6">
            <div className="text-xs font-mono uppercase text-sky-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Completed
            </div>
            <div className="text-2xl font-bold text-sky-300 mt-1">{completedCount}</div>
            <div className="text-xs text-slate-500 mt-1">Production/Shipped</div>
          </CardContent>
        </Card>
        <Card className="bg-slate-900/60 border-indigo-950/40">
          <CardContent className="pt-6">
            <div className="text-xs font-mono uppercase text-indigo-400 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> Avg Quality Score
            </div>
            <div className="text-2xl font-bold text-indigo-300 mt-1">
              {avgQualityScore !== null ? `${avgQualityScore}/100` : "N/A"}
            </div>
            <div className="text-xs text-slate-500 mt-1">Deterministic v1.0.0</div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-slate-900/40 p-4 rounded-xl border border-slate-800">
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search by title, technology..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-slate-900 border-slate-700 text-slate-200 placeholder:text-slate-500"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
            <Filter className="w-3.5 h-3.5" /> Type:
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-md text-xs py-1.5 px-2.5 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Types</option>
            <option value="capstone">Capstone</option>
            <option value="academic">Academic</option>
            <option value="personal">Personal</option>
            <option value="hackathon">Hackathon</option>
            <option value="open_source">Open Source</option>
            <option value="internship">Internship</option>
            <option value="research">Research</option>
          </select>

          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono ml-2">
            Status:
          </div>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-md text-xs py-1.5 px-2.5 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="in_progress">In Progress</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 font-mono text-sm">
          Loading project portfolio...
        </div>
      ) : error ? (
        <div className="py-12 text-center text-rose-400 font-mono text-sm border border-rose-900/40 rounded-xl bg-rose-950/20">
          {error}
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="py-20 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/20 p-8">
          <FolderGit2 className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-200">No projects found</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
            {search || selectedType !== "all" || selectedStatus !== "all"
              ? "No projects matched your active filters. Try adjusting your search query."
              : "You have not registered any projects yet. Add your first project to start building your verifiable evidence graph."}
          </p>
          <div className="mt-5">
            <Link href="/projects/new">
              <Button className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium">
                <Plus className="w-4 h-4 mr-1.5" /> Create Project
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((p) => {
            const hasQuality = p.quality_score !== null && p.quality_score !== undefined;
            return (
              <Card
                key={p.id}
                className="bg-slate-900/60 border-slate-800 hover:border-slate-700 transition duration-200 flex flex-col justify-between group shadow-sm hover:shadow-indigo-950/20"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <Badge
                      variant="outline"
                      className="capitalize font-mono text-[10px] tracking-wider border-slate-700 bg-slate-800/40 text-slate-300"
                    >
                      {p.project_type.replace("_", " ")}
                    </Badge>
                    <div className="flex items-center gap-1.5">
                      {p.visibility === "public" ? (
                        <span title="Public"><Globe className="w-3.5 h-3.5 text-emerald-400" /></span>
                      ) : p.visibility === "institution" ? (
                        <span title="Institution Only"><Building className="w-3.5 h-3.5 text-sky-400" /></span>
                      ) : (
                        <span title="Private"><Lock className="w-3.5 h-3.5 text-slate-500" /></span>
                      )}
                      {p.is_verified ? (
                        <Badge className="bg-emerald-950 text-emerald-300 border-emerald-800/60 text-[10px] font-mono flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3" /> Verified
                        </Badge>
                      ) : (
                        <Badge
                          variant="outline"
                          className="text-slate-400 border-slate-700 text-[10px] font-mono"
                        >
                          {p.verification_status}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <CardTitle className="text-lg font-bold text-slate-100 group-hover:text-indigo-300 transition line-clamp-1">
                    {p.title}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-400 line-clamp-2 mt-1">
                    {p.short_description || p.description || "No description provided."}
                  </CardDescription>
                </CardHeader>

                <CardContent className="pt-0 space-y-4">
                  {/* Technologies tags */}
                  {p.technologies && p.technologies.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {p.technologies.slice(0, 4).map((tech, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800/80 text-slate-300 border border-slate-700/60"
                        >
                          {tech}
                        </span>
                      ))}
                      {p.technologies.length > 4 && (
                        <span className="text-[11px] font-mono text-slate-500 self-center">
                          +{p.technologies.length - 4}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Quality & Career Relevance Indicators */}
                  <div className="pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <div className="text-[10px] font-mono uppercase text-slate-500">Quality Score</div>
                      <div className="font-semibold text-slate-200 mt-0.5">
                        {hasQuality ? (
                          <span
                            className={
                              (p.quality_score ?? 0) >= 80
                                ? "text-emerald-400 font-bold"
                                : (p.quality_score ?? 0) >= 60
                                ? "text-amber-400 font-bold"
                                : "text-rose-400 font-bold"
                            }
                          >
                            {p.quality_score}/100
                          </span>
                        ) : (
                          <span className="text-slate-500 font-mono">Unscored</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono uppercase text-slate-500">Career Fit</div>
                      <div className="font-semibold text-slate-200 mt-0.5 capitalize">
                        {p.career_relevance_category ? (
                          <span
                            className={
                              p.career_relevance_category === "high"
                                ? "text-indigo-400 font-bold"
                                : p.career_relevance_category === "medium"
                                ? "text-sky-400"
                                : "text-slate-400"
                            }
                          >
                            {p.career_relevance_category}
                          </span>
                        ) : (
                          <span className="text-slate-500 font-mono">Unmapped</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Links & CTA */}
                  <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
                    <div className="flex items-center gap-2">
                      {p.repository_url && (
                        <a
                          href={p.repository_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-400 hover:text-slate-200 transition"
                          title="Repository"
                        >
                          <Code2 className="w-4 h-4" />
                        </a>
                      )}
                      {p.live_url && (
                        <a
                          href={p.live_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-400 hover:text-slate-200 transition"
                          title="Live Deployment"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                    <Link href={`/projects/${p.id}`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-950/40 text-xs font-mono"
                      >
                        Inspect Evidence →
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
