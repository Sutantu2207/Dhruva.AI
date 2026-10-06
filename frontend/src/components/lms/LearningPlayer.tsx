"use client";

import React, { useState, useEffect } from "react";
import {
  Lesson,
  Curriculum,
  LessonProgress,
  StudentBookmark,
  StudentLearningNote,
} from "@/lib/types";
import {
  startLessonProgress,
  updateLessonProgress,
  completeLessonProgress,
  createStudentBookmark,
  deleteStudentBookmark,
  fetchStudentBookmarks,
  fetchStudentNotes,
  createStudentNote,
  deleteStudentNote,
} from "@/lib/api";
import {
  CheckCircle2,
  Circle,
  Bookmark,
  BookmarkCheck,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Code,
  FileText,
  AlertCircle,
  StickyNote,
  Trash2,
  Clock,
} from "lucide-react";

interface LearningPlayerProps {
  curriculum: Curriculum;
  offeringId: string;
  onBackToCourse: () => void;
  onProgressUpdated?: () => void;
}

export function LearningPlayer({
  curriculum,
  offeringId,
  onBackToCourse,
  onProgressUpdated,
}: LearningPlayerProps) {
  // Collect all lessons in sequence
  const allLessons: Lesson[] = curriculum.modules.flatMap((m) => m.lessons);
  const [activeLessonIndex, setActiveLessonIndex] = useState(0);
  const currentLesson = allLessons[activeLessonIndex] || null;

  const [progress, setProgress] = useState<LessonProgress | null>(null);
  const [bookmarks, setBookmarks] = useState<StudentBookmark[]>([]);
  const [notes, setNotes] = useState<StudentLearningNote[]>([]);
  const [newNoteTitle, setNewNoteTitle] = useState("");
  const [newNoteContent, setNewNoteContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);

  // Initialize progress and load bookmarks / notes for current lesson
  useEffect(() => {
    if (!currentLesson) return;

    let mounted = true;
    async function loadLessonContext() {
      try {
        const prog = await startLessonProgress(currentLesson.id, offeringId);
        if (mounted) {
          setProgress(prog);
          setTimeSpent(prog.time_spent_seconds || 0);
        }

        const bms = await fetchStudentBookmarks();
        if (mounted) setBookmarks(bms);

        const lNotes = await fetchStudentNotes("lesson", currentLesson.id);
        if (mounted) setNotes(lNotes);
      } catch (err) {
        console.error("Failed to load lesson context", err);
      }
    }

    loadLessonContext();

    // Local reading timer (increment time every 10s and ping server periodically)
    const timer = setInterval(() => {
      setTimeSpent((prev) => prev + 10);
    }, 10000);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, [currentLesson, offeringId]);

  // Periodic heartbeat sync to persist reading duration
  useEffect(() => {
    if (!currentLesson || timeSpent === 0) return;
    const syncTimer = setTimeout(async () => {
      try {
        await updateLessonProgress(currentLesson.id, offeringId, 10, progress?.completion_percentage || 25);
      } catch {
        // Non-blocking sync error
      }
    }, 10000);
    return () => clearTimeout(syncTimer);
  }, [timeSpent, currentLesson, offeringId, progress?.completion_percentage]);

  const isBookmarked = bookmarks.some(
    (b) => b.target_type === "lesson" && b.target_id === currentLesson?.id
  );

  const toggleBookmark = async () => {
    if (!currentLesson) return;
    try {
      if (isBookmarked) {
        const existing = bookmarks.find(
          (b) => b.target_type === "lesson" && b.target_id === currentLesson.id
        );
        if (existing) {
          await deleteStudentBookmark(existing.id);
          setBookmarks((prev) => prev.filter((b) => b.id !== existing.id));
        }
      } else {
        const created = await createStudentBookmark({
          target_type: "lesson",
          target_id: currentLesson.id,
          title: currentLesson.title,
        });
        setBookmarks((prev) => [...prev, created]);
      }
    } catch (err) {
      console.error("Bookmark toggle failed", err);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentLesson || !newNoteContent.trim()) return;
    try {
      const created = await createStudentNote({
        target_type: "lesson",
        target_id: currentLesson.id,
        title: newNoteTitle.trim() || undefined,
        content: newNoteContent.trim(),
        is_private: true,
      });
      setNotes((prev) => [created, ...prev]);
      setNewNoteTitle("");
      setNewNoteContent("");
    } catch (err) {
      console.error("Failed to add note", err);
    }
  };

  const handleDeleteNote = async (id: string) => {
    try {
      await deleteStudentNote(id);
      setNotes((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      console.error("Failed to delete note", err);
    }
  };

  const handleCompleteLesson = async () => {
    if (!currentLesson) return;
    setIsLoading(true);
    try {
      const updatedProg = await completeLessonProgress(currentLesson.id, offeringId, 10);
      setProgress(updatedProg);
      onProgressUpdated?.();
      // Auto advance to next lesson if available
      if (activeLessonIndex < allLessons.length - 1) {
        setActiveLessonIndex((prev) => prev + 1);
      }
    } catch (err) {
      console.error("Failed to complete lesson", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentLesson) {
    return (
      <div className="p-8 text-center text-slate-400">
        <p>No lessons available in this curriculum.</p>
        <button
          onClick={onBackToCourse}
          className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition"
        >
          Return to Overview
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Learning Navigation Bar */}
      <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-4">
          <button
            onClick={onBackToCourse}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Course Outline</span>
          </button>
          <div className="h-4 w-px bg-slate-800" />
          <h1 className="text-sm font-semibold text-slate-200 truncate max-w-md">
            {curriculum.title}
          </h1>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5" />
            <span>{Math.floor(timeSpent / 60)}m read</span>
          </div>

          <button
            onClick={toggleBookmark}
            className={`p-2 rounded-lg border text-sm transition flex items-center gap-1.5 ${
              isBookmarked
                ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                : "border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800"
            }`}
            title="Bookmark Lesson"
          >
            {isBookmarked ? (
              <BookmarkCheck className="w-4 h-4" />
            ) : (
              <Bookmark className="w-4 h-4" />
            )}
            <span className="hidden sm:inline">Bookmark</span>
          </button>

          {progress?.status === "completed" ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Completed
            </span>
          ) : (
            <button
              onClick={handleCompleteLesson}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Mark Complete
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar: Curriculum Tree Navigation */}
        <aside className="w-80 border-r border-slate-800 bg-slate-900/40 p-4 hidden md:flex flex-col overflow-y-auto">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 px-2">
            Curriculum Structure
          </div>

          <div className="space-y-4">
            {curriculum.modules.map((mod, modIdx) => (
              <div key={mod.id} className="space-y-1">
                <div className="text-xs font-semibold text-slate-300 px-2 py-1">
                  Module {modIdx + 1}: {mod.title}
                </div>
                <div className="space-y-0.5">
                  {mod.lessons.map((les) => {
                    const globalIdx = allLessons.findIndex((l) => l.id === les.id);
                    const isSelected = globalIdx === activeLessonIndex;
                    return (
                      <button
                        key={les.id}
                        onClick={() => setActiveLessonIndex(globalIdx)}
                        className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition ${
                          isSelected
                            ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 font-medium"
                            : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          {isSelected ? (
                            <Circle className="w-3 h-3 fill-indigo-400 text-indigo-400" />
                          ) : (
                            <BookOpen className="w-3 h-3 text-slate-500" />
                          )}
                          <span className="truncate">{les.title}</span>
                        </div>
                        {les.is_required && (
                          <span className="text-[10px] text-slate-500 font-mono">
                            req
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Center: Structured Lesson Content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-12 max-w-4xl mx-auto space-y-8">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-indigo-400 mb-1">
              <span>LESSON {activeLessonIndex + 1} OF {allLessons.length}</span>
              <span>•</span>
              <span className="uppercase">{currentLesson.lesson_type}</span>
            </div>
            <h2 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
              {currentLesson.title}
            </h2>
            {currentLesson.description && (
              <p className="mt-2 text-sm text-slate-400">
                {currentLesson.description}
              </p>
            )}
          </div>

          {/* Structured Content Blocks */}
          <div className="space-y-6">
            {currentLesson.content_blocks && currentLesson.content_blocks.length > 0 ? (
              currentLesson.content_blocks.map((block) => (
                <div key={block.id} className="text-slate-300 leading-relaxed text-sm">
                  {block.block_type === "heading" && (
                    <h3 className="text-lg font-bold text-slate-100 mt-6 mb-2 border-b border-slate-800 pb-2">
                      {block.content}
                    </h3>
                  )}

                  {block.block_type === "paragraph" && (
                    <div
                      className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: block.content }}
                    />
                  )}

                  {block.block_type === "code" && (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 font-mono text-xs text-emerald-300 overflow-x-auto">
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mb-2 border-b border-slate-800 pb-1">
                        <span className="flex items-center gap-1.5">
                          <Code className="w-3.5 h-3.5" />
                          Code Block
                        </span>
                      </div>
                      <pre>{block.content}</pre>
                    </div>
                  )}

                  {block.block_type === "callout" && (
                    <div className="bg-indigo-950/40 border border-indigo-500/30 rounded-xl p-4 flex items-start gap-3 text-indigo-200 text-xs">
                      <AlertCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                      <div>{block.content}</div>
                    </div>
                  )}

                  {block.block_type === "quote" && (
                    <blockquote className="border-l-2 border-indigo-500 pl-4 py-1 italic text-slate-400 text-xs">
                      {block.content}
                    </blockquote>
                  )}
                </div>
              ))
            ) : (
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center text-slate-400">
                <FileText className="w-8 h-8 mx-auto text-slate-600 mb-2" />
                <p className="text-sm">Structured lesson content blocks are being compiled for this lesson.</p>
              </div>
            )}
          </div>

          {/* Previous / Next Lesson Footer Controls */}
          <div className="pt-8 border-t border-slate-800 flex items-center justify-between">
            <button
              onClick={() => setActiveLessonIndex((prev) => Math.max(0, prev - 1))}
              disabled={activeLessonIndex === 0}
              className="px-4 py-2 rounded-lg border border-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-900 disabled:opacity-30 disabled:pointer-events-none flex items-center gap-2 transition"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous Lesson
            </button>

            <button
              onClick={() =>
                setActiveLessonIndex((prev) => Math.min(allLessons.length - 1, prev + 1))
              }
              disabled={activeLessonIndex === allLessons.length - 1}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-30 disabled:pointer-events-none flex items-center gap-2 transition"
            >
              Next Lesson
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </main>

        {/* Right Panel: Private Learning Notes */}
        <aside className="w-72 border-l border-slate-800 bg-slate-900/30 p-4 hidden lg:flex flex-col">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            <StickyNote className="w-3.5 h-3.5 text-indigo-400" />
            <span>Private Notes</span>
          </div>

          {/* Add Note Form */}
          <form onSubmit={handleAddNote} className="space-y-2 mb-4">
            <input
              type="text"
              placeholder="Note title (optional)"
              value={newNoteTitle}
              onChange={(e) => setNewNoteTitle(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
            <textarea
              placeholder="Write a private study note..."
              value={newNoteContent}
              onChange={(e) => setNewNoteContent(e.target.value)}
              rows={3}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 resize-none"
            />
            <button
              type="submit"
              disabled={!newNoteContent.trim()}
              className="w-full py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition disabled:opacity-40"
            >
              Add Note
            </button>
          </form>

          {/* Note List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {notes.map((note) => (
              <div
                key={note.id}
                className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-xs space-y-1 group relative"
              >
                {note.title && (
                  <div className="font-semibold text-slate-200 text-[11px] truncate">
                    {note.title}
                  </div>
                )}
                <p className="text-slate-400 text-[11px] whitespace-pre-wrap">
                  {note.content}
                </p>
                <div className="flex items-center justify-between pt-1 text-[10px] text-slate-600">
                  <span>Private</span>
                  <button
                    onClick={() => handleDeleteNote(note.id)}
                    className="opacity-0 group-hover:opacity-100 text-rose-400 hover:text-rose-300 transition"
                    title="Delete Note"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
            {notes.length === 0 && (
              <div className="text-center py-6 text-slate-600 text-xs italic">
                No notes for this lesson yet.
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
