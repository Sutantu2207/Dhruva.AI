"use client";

import React, { useState } from "react";
import {
  CourseContentDetail,
  Module,
  Lesson,
} from "@/lib/types";
import {
  createCourseModule,
  createModuleLesson,
  addLessonContentBlock,
  submitContentForReview,
  approveContentReview,
  requestChangesContentReview,
} from "@/lib/api";
import {
  Send,
  CheckCircle,
  Layers,
  FileText,
  Eye,
  PlusCircle,
  HelpCircle,
} from "lucide-react";

interface CourseBuilderProps {
  courseContent: CourseContentDetail;
  userRole: string;
  onRefresh: () => void;
}

export function CourseBuilder({
  courseContent,
  userRole,
  onRefresh,
}: CourseBuilderProps) {
  const [selectedModule, setSelectedModule] = useState<Module | null>(
    courseContent.curriculum?.modules?.[0] || null
  );
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(
    selectedModule?.lessons?.[0] || null
  );

  // Form states
  const [isAddingModule, setIsAddingModule] = useState(false);
  const [newModuleTitle, setNewModuleTitle] = useState("");
  const [newModuleSlug, setNewModuleSlug] = useState("");

  const [isAddingLesson, setIsAddingLesson] = useState(false);
  const [newLessonTitle, setNewLessonTitle] = useState("");
  const [newLessonSlug, setNewLessonSlug] = useState("");
  const [newLessonType, setNewLessonType] = useState("text");

  const [isAddingBlock, setIsAddingBlock] = useState(false);
  const [newBlockType, setNewBlockType] = useState("paragraph");
  const [newBlockContent, setNewBlockContent] = useState("");

  const [reviewNotes, setReviewNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const canReview = ["hod", "institution_admin", "super_admin"].includes(userRole);
  const isDraft = courseContent.status === "draft";
  const isInReview = courseContent.status === "in_review";

  const handleCreateModule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!courseContent.curriculum || !newModuleTitle) return;
    try {
      await createCourseModule(courseContent.course_id, {
        curriculum_id: courseContent.curriculum.id,
        title: newModuleTitle,
        slug: newModuleSlug || newModuleTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
      });
      setNewModuleTitle("");
      setNewModuleSlug("");
      setIsAddingModule(false);
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create module";
      setStatusMessage(`Error: ${msg}`);
    }
  };

  const handleCreateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModule || !newLessonTitle) return;
    try {
      await createModuleLesson(selectedModule.id, {
        title: newLessonTitle,
        slug: newLessonSlug || newLessonTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
        lesson_type: newLessonType,
        is_required: true,
      });
      setNewLessonTitle("");
      setNewLessonSlug("");
      setIsAddingLesson(false);
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create lesson";
      setStatusMessage(`Error: ${msg}`);
    }
  };

  const handleAddBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLesson || !newBlockContent) return;
    try {
      await addLessonContentBlock(selectedLesson.id, {
        block_type: newBlockType,
        content: newBlockContent,
      });
      setNewBlockContent("");
      setIsAddingBlock(false);
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to add block";
      setStatusMessage(`Error: ${msg}`);
    }
  };

  const handleSubmitForReview = async () => {
    setIsSubmitting(true);
    setStatusMessage(null);
    try {
      await submitContentForReview(courseContent.id, reviewNotes || "Submitted for institutional review");
      setStatusMessage("Curriculum submitted for review successfully.");
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Submission failed";
      setStatusMessage(`Error: ${msg}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApprove = async () => {
    setIsSubmitting(true);
    setStatusMessage(null);
    try {
      await approveContentReview(courseContent.id, reviewNotes || "Approved for student delivery");
      setStatusMessage("Content published successfully!");
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Approval failed";
      setStatusMessage(`Error: ${msg}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestChanges = async () => {
    setIsSubmitting(true);
    setStatusMessage(null);
    try {
      await requestChangesContentReview(courseContent.id, reviewNotes || "Changes requested by reviewer");
      setStatusMessage("Changes requested. Returned to draft status.");
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Action failed";
      setStatusMessage(`Error: ${msg}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with status badge and workflow actions */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white tracking-tight">
              {courseContent.title}
            </h2>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize ${
                courseContent.status === "published"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                  : courseContent.status === "in_review"
                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  : "bg-slate-800 text-slate-300 border border-slate-700"
              }`}
            >
              {courseContent.status.replace("_", " ")}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Version {courseContent.version} • {courseContent.difficulty} • {courseContent.language}
          </p>
        </div>

        {/* Workflow Action Controls */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {isDraft && (
            <button
              onClick={handleSubmitForReview}
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              Submit for Review
            </button>
          )}

          {isInReview && canReview && (
            <div className="flex flex-wrap items-center gap-2">
              <input
                type="text"
                placeholder="Review notes..."
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={handleApprove}
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition disabled:opacity-50"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                Approve
              </button>
              <button
                onClick={handleRequestChanges}
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold transition disabled:opacity-50"
              >
                Request Changes
              </button>
            </div>
          )}
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-slate-900 border border-indigo-500/30 rounded-xl text-xs text-indigo-300 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-indigo-400 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Builder Layout: Modules List (Left) -> Lessons (Middle) -> Content Editor (Right) */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 min-h-[500px]">
        {/* Module Column */}
        <div className="md:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              Modules
            </span>
            <button
              onClick={() => setIsAddingModule(!isAddingModule)}
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Add</span>
            </button>
          </div>

          {isAddingModule && (
            <form onSubmit={handleCreateModule} className="mb-3 p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
              <input
                type="text"
                placeholder="Module title"
                value={newModuleTitle}
                onChange={(e) => setNewModuleTitle(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                required
              />
              <button
                type="submit"
                className="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium"
              >
                Save Module
              </button>
            </form>
          )}

          <div className="space-y-1 overflow-y-auto flex-1">
            {courseContent.curriculum?.modules.map((mod, idx) => (
              <button
                key={mod.id}
                onClick={() => {
                  setSelectedModule(mod);
                  setSelectedLesson(mod.lessons?.[0] || null);
                }}
                className={`w-full text-left p-3 rounded-xl text-xs transition border flex items-center justify-between ${
                  selectedModule?.id === mod.id
                    ? "bg-indigo-600/10 border-indigo-500/40 text-indigo-300 font-semibold"
                    : "border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                }`}
              >
                <div className="truncate">
                  <div className="text-[10px] text-slate-500">Module {idx + 1}</div>
                  <div className="truncate text-slate-200">{mod.title}</div>
                </div>
                <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono">
                  {mod.lessons?.length || 0} lessons
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Lesson Column */}
        <div className="md:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              Lessons
            </span>
            {selectedModule && (
              <button
                onClick={() => setIsAddingLesson(!isAddingLesson)}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Add</span>
              </button>
            )}
          </div>

          {isAddingLesson && (
            <form onSubmit={handleCreateLesson} className="mb-3 p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
              <input
                type="text"
                placeholder="Lesson title"
                value={newLessonTitle}
                onChange={(e) => setNewLessonTitle(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                required
              />
              <select
                value={newLessonType}
                onChange={(e) => setNewLessonType(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
              >
                <option value="text">Text Lesson</option>
                <option value="video">Video Lesson</option>
                <option value="coding">Coding Sandbox</option>
                <option value="quiz">Quiz</option>
                <option value="assignment">Assignment</option>
              </select>
              <button
                type="submit"
                className="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium"
              >
                Save Lesson
              </button>
            </form>
          )}

          <div className="space-y-1 overflow-y-auto flex-1">
            {selectedModule?.lessons?.map((les) => (
              <button
                key={les.id}
                onClick={() => setSelectedLesson(les)}
                className={`w-full text-left p-3 rounded-xl text-xs transition border flex items-center justify-between ${
                  selectedLesson?.id === les.id
                    ? "bg-indigo-600/10 border-indigo-500/40 text-indigo-300 font-semibold"
                    : "border-transparent text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                }`}
              >
                <div className="truncate">
                  <div className="text-[10px] text-slate-500 uppercase">{les.lesson_type}</div>
                  <div className="truncate text-slate-200">{les.title}</div>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">
                  {les.content_blocks?.length || 0} blocks
                </span>
              </button>
            ))}
            {!selectedModule && (
              <div className="text-center py-8 text-slate-600 text-xs italic">
                Select a module to view lessons.
              </div>
            )}
          </div>
        </div>

        {/* Content Block Editor (Right) */}
        <div className="md:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-indigo-400" />
              Content Blocks
            </span>
            {selectedLesson && (
              <button
                onClick={() => setIsAddingBlock(!isAddingBlock)}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>Add Block</span>
              </button>
            )}
          </div>

          {isAddingBlock && (
            <form onSubmit={handleAddBlock} className="mb-3 p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
              <select
                value={newBlockType}
                onChange={(e) => setNewBlockType(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
              >
                <option value="paragraph">Paragraph</option>
                <option value="heading">Heading</option>
                <option value="code">Code Snippet</option>
                <option value="callout">Callout Alert</option>
                <option value="quote">Quote</option>
              </select>
              <textarea
                placeholder="Content block text (Markdown / Safe HTML)..."
                value={newBlockContent}
                onChange={(e) => setNewBlockContent(e.target.value)}
                rows={4}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none font-mono"
                required
              />
              <button
                type="submit"
                className="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium"
              >
                Insert Block
              </button>
            </form>
          )}

          <div className="space-y-2 overflow-y-auto flex-1">
            {selectedLesson?.content_blocks?.map((block) => (
              <div
                key={block.id}
                className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1"
              >
                <span className="text-[10px] uppercase font-mono text-indigo-400">
                  {block.block_type}
                </span>
                <p className="text-slate-300 line-clamp-3 font-mono text-[11px]">
                  {block.content}
                </p>
              </div>
            ))}
            {!selectedLesson && (
              <div className="text-center py-8 text-slate-600 text-xs italic">
                Select a lesson to manage content blocks.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
