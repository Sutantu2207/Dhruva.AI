"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  FolderGit2,
  Save,
  Users,
  FileText,
  Link as LinkIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createProject } from "@/lib/api";

export default function NewProjectPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Form states
  const [title, setTitle] = React.useState("");
  const [shortDescription, setShortDescription] = React.useState("");
  const [problemStatement, setProblemStatement] = React.useState("");
  const [solution, setSolution] = React.useState("");
  const [projectType, setProjectType] = React.useState("capstone");
  const [status, setStatus] = React.useState("in_progress");
  const [visibility, setVisibility] = React.useState<"private" | "institution" | "public">("public");

  const [technologiesInput, setTechnologiesInput] = React.useState("");
  const [repositoryUrl, setRepositoryUrl] = React.useState("");
  const [liveUrl, setLiveUrl] = React.useState("");
  const [demoUrl, setDemoUrl] = React.useState("");
  const [documentationUrl, setDocumentationUrl] = React.useState("");

  // Team contribution fields
  const [teamOrIndividual, setTeamOrIndividual] = React.useState<"individual" | "team">("individual");
  const [role, setRole] = React.useState("");
  const [teamSize, setTeamSize] = React.useState(1);
  const [contributionDescription, setContributionDescription] = React.useState("");
  const [contributionPercentage, setContributionPercentage] = React.useState<number | "">("");
  const [modulesInput, setModulesInput] = React.useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Project title is required.");
      return;
    }

    setSubmitting(true);
    setError(null);

    const technologies = technologiesInput
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    const modulesContributed = modulesInput
      .split(",")
      .map((m) => m.trim())
      .filter(Boolean);

    try {
      const created = await createProject({
        title: title.trim(),
        short_description: shortDescription.trim() || undefined,
        problem_statement: problemStatement.trim() || undefined,
        solution: solution.trim() || undefined,
        project_type: projectType,
        status,
        visibility,
        technologies,
        repository_url: repositoryUrl.trim() || undefined,
        live_url: liveUrl.trim() || undefined,
        demo_url: demoUrl.trim() || undefined,
        documentation_url: documentationUrl.trim() || undefined,
        team_or_individual: teamOrIndividual,
        role: role.trim() || undefined,
        team_size: teamOrIndividual === "team" ? Number(teamSize) : 1,
        contribution_description: contributionDescription.trim() || undefined,
        contribution_percentage:
          contributionPercentage !== "" ? Number(contributionPercentage) : undefined,
        modules_contributed: modulesContributed,
      });

      router.push(`/projects/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create project");
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 space-y-8 max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-6">
        <div>
          <Link
            href="/projects"
            className="flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Projects Dashboard
          </Link>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-slate-100 to-indigo-300 bg-clip-text text-transparent">
            Register New Student Project
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Submit a real project implementation with explicit contribution bounds and verifiable empirical artifacts.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-900 text-rose-300 text-sm font-mono">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1: Basic Information */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-200 flex items-center gap-2">
              <FolderGit2 className="w-4 h-4 text-indigo-400" /> Core Project Identity
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Clear title, domain taxonomy, and lifecycle state.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                Project Title <span className="text-rose-400">*</span>
              </label>
              <Input
                placeholder="e.g. Dhruva.AI Skill Graph & Portfolio Engine"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Project Category
                </label>
                <select
                  value={projectType}
                  onChange={(e) => setProjectType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm py-2 px-3 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="capstone">Capstone Project</option>
                  <option value="academic">Academic / Coursework</option>
                  <option value="personal">Personal Project</option>
                  <option value="hackathon">Hackathon</option>
                  <option value="internship">Internship Assignment</option>
                  <option value="research">Research Publication</option>
                  <option value="open_source">Open Source Contribution</option>
                  <option value="freelance">Freelance Client Work</option>
                  <option value="startup">Startup Venture</option>
                  <option value="competition">Competition / Contest</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Lifecycle Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm py-2 px-3 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed / Shipped</option>
                  <option value="draft">Draft</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Portfolio Visibility
                </label>
                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value as "private" | "institution" | "public")}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm py-2 px-3 text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="public">Public (Visible on public portfolio)</option>
                  <option value="institution">Institution (Faculty & Peers only)</option>
                  <option value="private">Private (Only you and assigned faculty)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                Elevator Pitch / Short Description
              </label>
              <Input
                placeholder="One or two sentences explaining the core functionality and business impact."
                value={shortDescription}
                onChange={(e) => setShortDescription(e.target.value)}
                maxLength={500}
                className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* Section 2: Problem & Technical Solution */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-200 flex items-center gap-2">
              <FileText className="w-4 h-4 text-sky-400" /> Engineering Problem & Solution
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Deterministic quality engines award high documentation weight to clear problem-solution framing.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                Problem Statement
              </label>
              <textarea
                rows={3}
                placeholder="What specific engineering challenge, bottleneck, or user pain point does this project address?"
                value={problemStatement}
                onChange={(e) => setProblemStatement(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm p-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                Implemented Technical Solution
              </label>
              <textarea
                rows={3}
                placeholder="How did you solve this problem? Explain algorithms, architectural decisions, and data pipelines."
                value={solution}
                onChange={(e) => setSolution(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm p-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                Technologies Used (Comma separated)
              </label>
              <Input
                placeholder="e.g. FastAPI, Python, React, TypeScript, PostgreSQL, Docker, Redis"
                value={technologiesInput}
                onChange={(e) => setTechnologiesInput(e.target.value)}
                className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* Section 3: Empirical Artifacts & URLs */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-200 flex items-center gap-2">
              <LinkIcon className="w-4 h-4 text-emerald-400" /> Empirical Evidence Links
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Repository URLs automatically generate audit evidence items for the verification engine.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Source Code Repository URL
                </label>
                <Input
                  placeholder="https://github.com/organization/repo"
                  value={repositoryUrl}
                  onChange={(e) => setRepositoryUrl(e.target.value)}
                  className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Live Production URL
                </label>
                <Input
                  placeholder="https://app.yourproject.com"
                  value={liveUrl}
                  onChange={(e) => setLiveUrl(e.target.value)}
                  className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Documentation URL
                </label>
                <Input
                  placeholder="https://docs.yourproject.com or Notion/Wiki link"
                  value={documentationUrl}
                  onChange={(e) => setDocumentationUrl(e.target.value)}
                  className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Demo Video / Presentation URL
                </label>
                <Input
                  placeholder="https://youtu.be/... or Loom walkthrough"
                  value={demoUrl}
                  onChange={(e) => setDemoUrl(e.target.value)}
                  className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Section 4: Individual Contribution Bounds */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-200 flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" /> Team & Contribution Bounds
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Crucial: A team project does NOT treat the student as author of all parts. Evidence is strictly tied to
              your specific contributed modules.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Project Format
                </label>
                <select
                  value={teamOrIndividual}
                  onChange={(e) => setTeamOrIndividual(e.target.value as "individual" | "team")}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm py-2 px-3 text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="individual">Solo / Individual Project</option>
                  <option value="team">Team Project</option>
                </select>
              </div>

              {teamOrIndividual === "team" && (
                <>
                  <div>
                    <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                      Team Size
                    </label>
                    <Input
                      type="number"
                      min={2}
                      max={50}
                      value={teamSize}
                      onChange={(e) => setTeamSize(Number(e.target.value))}
                      className="bg-slate-900 border-slate-700 text-slate-100"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                      Your Role
                    </label>
                    <Input
                      placeholder="e.g. Backend Lead, DevOps Engineer"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                      className="bg-slate-900 border-slate-700 text-slate-100"
                    />
                  </div>
                </>
              )}
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                Specific Contribution Description
              </label>
              <textarea
                rows={2}
                placeholder="Exactly which services, schemas, or frontend views did you personally implement?"
                value={contributionDescription}
                onChange={(e) => setContributionDescription(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm p-3 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Modules Contributed (Comma separated)
                </label>
                <Input
                  placeholder="e.g. Auth Service, Payment Gateway, CI/CD Pipeline"
                  value={modulesInput}
                  onChange={(e) => setModulesInput(e.target.value)}
                  className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                />
              </div>
              {teamOrIndividual === "team" && (
                <div>
                  <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                    Estimated Contribution % (Optional)
                  </label>
                  <Input
                    type="number"
                    min={1}
                    max={100}
                    placeholder="e.g. 35"
                    value={contributionPercentage}
                    onChange={(e) =>
                      setContributionPercentage(e.target.value ? Number(e.target.value) : "")
                    }
                    className="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Submit Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
          <Link href="/projects">
            <Button variant="outline" type="button" className="border-slate-700 text-slate-300">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={submitting}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-6 shadow-lg shadow-indigo-600/20"
          >
            <Save className="w-4 h-4 mr-2" /> {submitting ? "Saving Project..." : "Register Project"}
          </Button>
        </div>
      </form>
    </div>
  );
}
