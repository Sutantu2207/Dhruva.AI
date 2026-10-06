"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  FileCheck2,
  Plus,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Save,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  fetchProjectDetail,
  fetchProjectEvidence,
  submitProjectEvidence,
  verifyProjectEvidence,
} from "@/lib/api";
import type { StudentProjectDetail, ProjectEvidenceItem } from "@/lib/types";

export default function ProjectEvidencePage() {
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = React.useState<StudentProjectDetail | null>(null);
  const [evidenceList, setEvidenceList] = React.useState<ProjectEvidenceItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

  // New evidence form state
  const [evidenceType, setEvidenceType] = React.useState("repository");
  const [source, setSource] = React.useState("github");
  const [sourceReference, setSourceReference] = React.useState("");
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [evidenceStrength, setEvidenceStrength] = React.useState(0.85);

  const loadData = React.useCallback(async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      const [pData, evData] = await Promise.all([
        fetchProjectDetail(projectId),
        fetchProjectEvidence(projectId),
      ]);
      setProject(pData);
      setEvidenceList(evData);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load project evidence");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  React.useEffect(() => {
    if (!projectId) return;
    let active = true;
    Promise.all([
      fetchProjectDetail(projectId),
      fetchProjectEvidence(projectId),
    ])
      .then(([pData, evData]) => {
        if (active) {
          setProject(pData);
          setEvidenceList(evData);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load project evidence");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [projectId]);

  const handleAddEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !sourceReference.trim()) {
      setError("Title and Source Reference URL are required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);

    try {
      await submitProjectEvidence(projectId, {
        evidence_type: evidenceType,
        source,
        source_reference: sourceReference.trim(),
        title: title.trim(),
        description: description.trim() || undefined,
        evidence_strength: Number(evidenceStrength),
      });

      // Reset form
      setTitle("");
      setSourceReference("");
      setDescription("");
      setSuccessMsg("Evidence successfully submitted into provenance ledger!");
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit evidence");
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (evidenceId: string, decision: "verified" | "rejected") => {
    try {
      await verifyProjectEvidence(projectId, evidenceId, decision, "Reviewed and verified by instructor.");
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Verification action failed");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex items-center justify-center font-mono text-sm text-slate-400">
        Loading evidence ledger...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800/80 pb-6 space-y-2">
        <Link
          href={`/projects/${projectId}`}
          className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to {project?.title || "Project"}
        </Link>
        <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs tracking-wider uppercase">
          <FileCheck2 className="w-4 h-4" /> Empirical Provenance Ledger
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">
          Project Empirical Evidence
        </h1>
        <p className="text-sm text-slate-400 max-w-2xl">
          Submit verifiable artifacts (repositories, pull requests, test reports, architecture diagrams).
          Students submit; authorized faculty review and verify.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-900 text-rose-300 text-sm font-mono flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-900 text-emerald-300 text-sm font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" /> {successMsg}
        </div>
      )}

      {/* Submission Form */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader>
          <CardTitle className="text-base font-bold text-slate-200 flex items-center gap-2">
            <Plus className="w-4 h-4 text-indigo-400" /> Submit New Evidence Item
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Every record is recorded with an immutable timestamp and audit trail.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddEvidence} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Evidence Type
                </label>
                <select
                  value={evidenceType}
                  onChange={(e) => setEvidenceType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm py-2 px-3 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="repository">Source Code Repository</option>
                  <option value="test_report">Automated Test Report / Coverage</option>
                  <option value="architecture_diagram">System Architecture Diagram</option>
                  <option value="deployment">Live Cloud Deployment</option>
                  <option value="documentation">Technical Documentation / API Spec</option>
                  <option value="pull_request">Merged Pull Request / Code Review</option>
                  <option value="demo">Recorded Demo / Screencast</option>
                  <option value="screenshot">Screenshot / UI Proof</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Source Platform
                </label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm py-2 px-3 text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab</option>
                  <option value="ci_pipeline">CI / CD Pipeline</option>
                  <option value="cloud_provider">Cloud Provider (AWS/GCP/Vercel)</option>
                  <option value="notion">Notion / Wiki</option>
                  <option value="external_url">External Web Link</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Evidence Title <span className="text-rose-400">*</span>
                </label>
                <Input
                  placeholder="e.g. Unit Test Coverage Report (94%)"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  className="bg-slate-900 border-slate-700 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                  Source Reference URL / Identifier <span className="text-rose-400">*</span>
                </label>
                <Input
                  placeholder="https://ci.example.com/build/129 or repo link"
                  value={sourceReference}
                  onChange={(e) => setSourceReference(e.target.value)}
                  required
                  className="bg-slate-900 border-slate-700 text-slate-100"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 uppercase mb-1.5">
                Technical Context / Description
              </label>
              <textarea
                rows={2}
                placeholder="Briefly describe what this evidence proves and which skills it exercises."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-md text-sm p-3 text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-slate-400">Claimed Strength:</span>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={evidenceStrength}
                  onChange={(e) => setEvidenceStrength(parseFloat(e.target.value))}
                  className="w-32 accent-indigo-500"
                />
                <span className="text-xs font-bold font-mono text-indigo-300">
                  {Math.round(evidenceStrength * 100)}%
                </span>
              </div>

              <Button
                type="submit"
                disabled={submitting}
                className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium"
              >
                <Save className="w-3.5 h-3.5 mr-1.5" />
                {submitting ? "Submitting..." : "Submit Evidence"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Existing Evidence Ledger */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-200">
          Recorded Evidence Ledger ({evidenceList.length})
        </h2>

        {evidenceList.length === 0 ? (
          <Card className="bg-slate-900/40 border-dashed border-slate-800 p-8 text-center">
            <p className="text-sm text-slate-400">
              No empirical evidence recorded for this project yet. Use the form above to register artifacts.
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {evidenceList.map((ev) => (
              <Card key={ev.id} className="bg-slate-900/60 border-slate-800">
                <CardContent className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-slate-200">{ev.title}</span>
                      <Badge
                        variant="outline"
                        className="font-mono text-[10px] uppercase border-slate-700 bg-slate-800 text-slate-400"
                      >
                        {ev.evidence_type.replace("_", " ")}
                      </Badge>
                      <Badge
                        className={
                          ev.verification_status === "verified"
                            ? "bg-emerald-950 text-emerald-300 border-emerald-800 text-[10px] font-mono"
                            : ev.verification_status === "rejected"
                            ? "bg-rose-950 text-rose-300 border-rose-800 text-[10px] font-mono"
                            : "bg-slate-800 text-slate-300 border-slate-700 text-[10px] font-mono"
                        }
                      >
                        {ev.verification_status}
                      </Badge>
                    </div>

                    <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                      <span>Source: <strong className="text-slate-300">{ev.source}</strong></span>
                      <span>•</span>
                      <a
                        href={ev.source_reference}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 flex items-center gap-1"
                      >
                        Reference <ExternalLink className="w-3 h-3" />
                      </a>
                      <span>•</span>
                      <span>Submitted: {new Date(ev.submitted_at).toLocaleDateString()}</span>
                    </div>

                    {ev.description && (
                      <p className="text-xs text-slate-300 mt-1">{ev.description}</p>
                    )}
                  </div>

                  {/* Verification Reviewer Controls */}
                  <div className="flex items-center gap-2 shrink-0">
                    {ev.verification_status !== "verified" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleVerify(ev.id, "verified")}
                        className="border-emerald-600/40 text-emerald-400 hover:bg-emerald-950/40 text-xs font-mono"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Approve
                      </Button>
                    )}
                    {ev.verification_status !== "rejected" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleVerify(ev.id, "rejected")}
                        className="border-rose-600/40 text-rose-400 hover:bg-rose-950/40 text-xs font-mono"
                      >
                        <XCircle className="w-3.5 h-3.5 mr-1" /> Reject
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
