"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  CourseSearchItem,
  CourseContentDetail,
  Curriculum,
  CourseProgress,
  StudentBookmark,
  StudentLearningNote,
  UserRole,
} from "@/lib/types";
import {
  fetchCoursesSearch,
  fetchCourseContent,
  fetchCourseCurriculum,
  fetchCourseOfferingProgress,
  fetchStudentBookmarks,
  fetchStudentNotes,
  deleteStudentBookmark,
  deleteStudentNote,
  createCourseContent,
} from "@/lib/api";
import { LearningPlayer } from "./LearningPlayer";
import { CourseBuilder } from "./CourseBuilder";
import {
  BookOpen,
  Search,
  Bookmark,
  StickyNote,
  Layers,
  GraduationCap,
  PlayCircle,
  PlusCircle,
  Trash2,
} from "lucide-react";

interface CourseDeliveryViewProps {
  userRole: UserRole;
  institutionId?: string | null;
}

export function CourseDeliveryView({
  userRole,
  institutionId,
}: CourseDeliveryViewProps) {
  const [courses, setCourses] = useState<CourseSearchItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [difficultyFilter, setDifficultyFilter] = useState("");
  const [activeTab, setActiveTab] = useState<"library" | "bookmarks" | "notes">("library");

  // Selected course details
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null);
  const [selectedContent, setSelectedContent] = useState<CourseContentDetail | null>(null);
  const [activeCurriculum, setActiveCurriculum] = useState<Curriculum | null>(null);
  const [activeOfferingProgress, setActiveOfferingProgress] = useState<CourseProgress | null>(null);

  // Active player mode
  const [isPlaying, setIsPlaying] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);

  // Bookmarks & Notes
  const [bookmarks, setBookmarks] = useState<StudentBookmark[]>([]);
  const [notes, setNotes] = useState<StudentLearningNote[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const isStudent = userRole === "student";
  const isFacultyOrAdmin = ["teacher", "hod", "institution_admin", "super_admin"].includes(userRole);

  const loadCourses = useCallback(async () => {
    try {
      const results = await fetchCoursesSearch({
        q: searchQuery || undefined,
        difficulty: difficultyFilter || undefined,
        institution_id: institutionId || undefined,
      });
      setCourses(results);
    } catch (err) {
      console.error("Failed to load courses", err);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, difficultyFilter, institutionId]);

  const loadUserData = useCallback(async () => {
    if (!isStudent) return;
    try {
      const [bms, nts] = await Promise.all([
        fetchStudentBookmarks(),
        fetchStudentNotes(),
      ]);
      setBookmarks(bms);
      setNotes(nts);
    } catch (err) {
      console.error("Failed to load bookmarks or notes", err);
    }
  }, [isStudent]);

  useEffect(() => {
    let ignore = false;
    async function fetchAll() {
      try {
        const results = await fetchCoursesSearch({
          q: searchQuery || undefined,
          difficulty: difficultyFilter || undefined,
          institution_id: institutionId || undefined,
        });
        if (!ignore) {
          setCourses(results);
        }
      } catch (err) {
        if (!ignore) console.error("Failed to load courses", err);
      }
    }
    fetchAll();
    return () => {
      ignore = true;
    };
  }, [searchQuery, difficultyFilter, institutionId]);

  useEffect(() => {
    if (!isStudent) return;
    let ignore = false;
    async function fetchUser() {
      try {
        const [bms, nts] = await Promise.all([
          fetchStudentBookmarks(),
          fetchStudentNotes(),
        ]);
        if (!ignore) {
          setBookmarks(bms);
          setNotes(nts);
        }
      } catch (err) {
        if (!ignore) console.error("Failed to load bookmarks or notes", err);
      }
    }
    fetchUser();
    return () => {
      ignore = true;
    };
  }, [isStudent]);

  const handleSelectCourse = async (item: CourseSearchItem) => {
    setSelectedCourseId(item.course_id);
    setIsPlaying(false);
    setIsBuilding(false);

    if (isStudent && item.course_id) {
      fetchCourseOfferingProgress(item.course_id)
        .then(setActiveOfferingProgress)
        .catch(() => setActiveOfferingProgress(null));
    } else {
      setActiveOfferingProgress(null);
    }

    try {
      if (item.course_content_id) {
        const content = await fetchCourseContent(item.course_content_id);
        setSelectedContent(content);
        if (content.curriculum) {
          setActiveCurriculum(content.curriculum);
        }
      } else {
        setSelectedContent(null);
        setActiveCurriculum(null);
      }
    } catch {
      setSelectedContent(null);
      setActiveCurriculum(null);
    }
  };

  const handleStartLearning = async () => {
    if (!selectedCourseId) return;
    try {
      const curr = await fetchCourseCurriculum(selectedCourseId);
      setActiveCurriculum(curr);
      setIsPlaying(true);
    } catch (err) {
      console.error("Could not launch learning player", err);
    }
  };

  const handleCreateDefaultContent = async () => {
    if (!selectedCourseId) return;
    try {
      const created = await createCourseContent(selectedCourseId, {
        title: "Curriculum Content",
        short_description: "Structured curriculum for delivery",
        difficulty: "intermediate",
        language: "English",
      });
      setSelectedContent(created);
      setIsBuilding(true);
      loadCourses();
    } catch (err) {
      console.error("Failed to initialize course content", err);
    }
  };

  // If in learning player mode:
  if (isPlaying && activeCurriculum) {
    return (
      <LearningPlayer
        curriculum={activeCurriculum}
        offeringId={selectedCourseId || "default"}
        onBackToCourse={() => {
          setIsPlaying(false);
          loadUserData();
        }}
        onProgressUpdated={() => {
          if (selectedCourseId) {
            fetchCourseOfferingProgress(selectedCourseId)
              .then(setActiveOfferingProgress)
              .catch(() => {});
          }
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Tab Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-indigo-400" />
            LMS Course Delivery & Content Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Structured modular curriculum, canonical concept graphs, and deterministic learning progress
          </p>
        </div>

        {isStudent && (
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
            <button
              onClick={() => setActiveTab("library")}
              className={`px-3 py-1.5 rounded-lg transition font-medium ${
                activeTab === "library"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Courses
            </button>
            <button
              onClick={() => setActiveTab("bookmarks")}
              className={`px-3 py-1.5 rounded-lg transition font-medium flex items-center gap-1.5 ${
                activeTab === "bookmarks"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Bookmark className="w-3.5 h-3.5" />
              <span>Bookmarks ({bookmarks.length})</span>
            </button>
            <button
              onClick={() => setActiveTab("notes")}
              className={`px-3 py-1.5 rounded-lg transition font-medium flex items-center gap-1.5 ${
                activeTab === "notes"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <StickyNote className="w-3.5 h-3.5" />
              <span>Notes ({notes.length})</span>
            </button>
          </div>
        )}
      </div>

      {/* Bookmarks Tab View */}
      {activeTab === "bookmarks" && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Bookmark className="w-4 h-4 text-amber-400" />
            Saved Learning Bookmarks
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {bookmarks.map((bm) => (
              <div
                key={bm.id}
                className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-[11px] text-indigo-400 uppercase font-mono">
                    <span>{bm.target_type}</span>
                    <button
                      onClick={async () => {
                        await deleteStudentBookmark(bm.id);
                        setBookmarks((prev) => prev.filter((b) => b.id !== bm.id));
                      }}
                      className="text-slate-500 hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="font-semibold text-white text-sm mt-1">
                    {bm.title || "Untitled Bookmark"}
                  </div>
                  {bm.notes && <p className="text-xs text-slate-400 mt-1">{bm.notes}</p>}
                </div>
                <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-900">
                  Saved on {new Date(bm.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
            {bookmarks.length === 0 && (
              <div className="col-span-full py-8 text-center text-slate-500 text-xs italic">
                No bookmarks saved yet. Use the bookmark button while studying lessons.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Notes Tab View */}
      {activeTab === "notes" && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <StickyNote className="w-4 h-4 text-indigo-400" />
            Private Learning Notes
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {notes.map((note) => (
              <div
                key={note.id}
                className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <span className="uppercase text-indigo-400">{note.target_type}</span>
                    <button
                      onClick={async () => {
                        await deleteStudentNote(note.id);
                        setNotes((prev) => prev.filter((n) => n.id !== note.id));
                      }}
                      className="text-slate-500 hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  {note.title && (
                    <div className="font-semibold text-white text-sm mt-1">
                      {note.title}
                    </div>
                  )}
                  <p className="text-xs text-slate-300 mt-2 whitespace-pre-wrap leading-relaxed">
                    {note.content}
                  </p>
                </div>
                <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-900 flex items-center justify-between">
                  <span>Private</span>
                  <span>{new Date(note.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
            {notes.length === 0 && (
              <div className="col-span-full py-8 text-center text-slate-500 text-xs italic">
                No learning notes created yet. Take private notes while studying lessons.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Course Library & Detail Area */}
      {activeTab === "library" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Search & Course Catalog List */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs">
              <Search className="w-4 h-4 text-slate-500 shrink-0" />
              <input
                type="text"
                placeholder="Search courses or codes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent text-white placeholder-slate-500 focus:outline-none"
              />
              <select
                value={difficultyFilter}
                onChange={(e) => setDifficultyFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-slate-300 text-[11px] focus:outline-none"
              >
                <option value="">All Levels</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            <div className="space-y-2">
              {courses.map((c) => {
                const isSelected = selectedCourseId === c.course_id;
                return (
                  <button
                    key={c.course_id}
                    onClick={() => handleSelectCourse(c)}
                    className={`w-full text-left p-4 rounded-2xl border transition flex flex-col gap-1.5 ${
                      isSelected
                        ? "bg-indigo-600/10 border-indigo-500/50 shadow-sm"
                        : "bg-slate-900 border-slate-800 hover:bg-slate-850 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-indigo-400 font-semibold">
                        {c.course_code}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize ${
                          c.status === "published"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : c.status === "in_review"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {c.status?.replace("_", " ") || "No Content"}
                      </span>
                    </div>

                    <div className="font-bold text-white text-sm">
                      {c.course_title}
                    </div>

                    {c.short_description && (
                      <p className="text-xs text-slate-400 line-clamp-2">
                        {c.short_description}
                      </p>
                    )}

                    <div className="flex items-center gap-3 pt-2 text-[11px] text-slate-500">
                      {c.difficulty && <span>Level: {c.difficulty}</span>}
                    </div>
                  </button>
                );
              })}

              {courses.length === 0 && !isLoading && (
                <div className="p-8 text-center text-slate-500 text-xs italic bg-slate-900 border border-slate-800 rounded-2xl">
                  No courses found matching your criteria.
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Course Detail / Curriculum Player / Builder */}
          <div className="lg:col-span-7">
            {selectedCourseId ? (
              <div className="space-y-6">
                {isBuilding && selectedContent ? (
                  <div>
                    <div className="flex justify-end mb-2">
                      <button
                        onClick={() => setIsBuilding(false)}
                        className="text-xs text-slate-400 hover:text-white transition"
                      >
                        Back to Overview
                      </button>
                    </div>
                    <CourseBuilder
                      courseContent={selectedContent}
                      userRole={userRole}
                      onRefresh={() => {
                        if (selectedContent) {
                          fetchCourseContent(selectedContent.id).then(setSelectedContent);
                        }
                      }}
                    />
                  </div>
                ) : (
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                      <div>
                        <span className="text-xs font-mono text-indigo-400 font-semibold">
                          COURSE OVERVIEW
                        </span>
                        <h3 className="text-2xl font-bold text-white mt-1">
                          {selectedContent?.title || courses.find((c) => c.course_id === selectedCourseId)?.course_title}
                        </h3>
                        <p className="text-xs text-slate-400 mt-1">
                          {selectedContent?.short_description || courses.find((c) => c.course_id === selectedCourseId)?.short_description}
                        </p>
                        {activeOfferingProgress && (
                          <div className="mt-2 flex items-center gap-3">
                            <span className="text-xs text-indigo-400 font-semibold font-mono">
                              Progress: {Math.round(activeOfferingProgress.percentage)}%
                            </span>
                            <span className="text-[11px] text-slate-500">
                              ({activeOfferingProgress.completed_lessons} of {activeOfferingProgress.total_required_lessons} lessons completed)
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {/* Student Start Learning */}
                        {isStudent && selectedContent?.status === "published" && (
                          <button
                            onClick={handleStartLearning}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md transition"
                          >
                            <PlayCircle className="w-4 h-4" />
                            <span>Start Learning</span>
                          </button>
                        )}

                        {/* Faculty/Admin Course Builder */}
                        {isFacultyOrAdmin && (
                          selectedContent ? (
                            <button
                              onClick={() => setIsBuilding(true)}
                              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition"
                            >
                              <Layers className="w-4 h-4 text-indigo-400" />
                              <span>Course Builder</span>
                            </button>
                          ) : (
                            <button
                              onClick={handleCreateDefaultContent}
                              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition"
                            >
                              <PlusCircle className="w-4 h-4" />
                              <span>Initialize Curriculum</span>
                            </button>
                          )
                        )}
                      </div>
                    </div>

                    {/* Curriculum Modules Outline */}
                    <div className="space-y-4">
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                        Curriculum Structure
                      </div>

                      {activeCurriculum && activeCurriculum.modules.length > 0 ? (
                        <div className="space-y-3">
                          {activeCurriculum.modules.map((m, mIdx) => (
                            <div
                              key={m.id}
                              className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2"
                            >
                              <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                                <span>
                                  Module {mIdx + 1}: {m.title}
                                </span>
                                <span className="text-[10px] text-slate-500 font-mono">
                                  {m.lessons.length} lessons
                                </span>
                              </div>
                              <div className="space-y-1 pl-2">
                                {m.lessons.map((l, lIdx) => (
                                  <div
                                    key={l.id}
                                    className="text-xs text-slate-400 flex items-center justify-between py-1 border-b border-slate-900 last:border-0"
                                  >
                                    <div className="flex items-center gap-2">
                                      <span className="font-mono text-slate-600 text-[11px]">
                                        {mIdx + 1}.{lIdx + 1}
                                      </span>
                                      <span>{l.title}</span>
                                    </div>
                                    <span className="text-[10px] uppercase font-mono text-slate-500">
                                      {l.lesson_type}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="p-8 text-center text-slate-500 text-xs italic bg-slate-950 border border-slate-800 rounded-xl">
                          {isStudent
                            ? "Curriculum content for this course is being published."
                            : "No modules created yet. Click 'Course Builder' to add modules and lessons."}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-16 text-center text-slate-500 text-xs italic bg-slate-900 border border-slate-800 rounded-2xl flex flex-col items-center justify-center">
                <BookOpen className="w-10 h-10 text-slate-700 mb-3" />
                <p>Select a course from the catalog to view curriculum details and learning progress.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
