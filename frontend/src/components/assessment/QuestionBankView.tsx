"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  fetchQuestionBanks,
  createQuestionBank,
  fetchQuestions,
  createQuestion,
  fetchConcepts,
} from "@/lib/api";
import type {
  QuestionBank,
  Question,
  QuestionType,
  QuestionDifficulty,
  Concept,
} from "@/lib/types";
import {
  BookOpen,
  Plus,
  Search,
  Filter,
  Layers,
  Sparkles,
  HelpCircle,
  Clock,
  Award,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export function QuestionBankView() {
  const [banks, setBanks] = React.useState<QuestionBank[]>([]);
  const [selectedBank, setSelectedBank] = React.useState<QuestionBank | null>(null);
  const [questions, setQuestions] = React.useState<Question[]>([]);
  const [concepts, setConcepts] = React.useState<Concept[]>([]);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = React.useState("");
  const [typeFilter, setTypeFilter] = React.useState<string>("all");
  const [difficultyFilter, setDifficultyFilter] = React.useState<string>("all");

  // Create Bank Modal
  const [showBankModal, setShowBankModal] = React.useState(false);
  const [newBankTitle, setNewBankTitle] = React.useState("");
  const [newBankDesc, setNewBankDesc] = React.useState("");

  // Create Question Modal
  const [showQuestionModal, setShowQuestionModal] = React.useState(false);
  const [newQTitle, setNewQTitle] = React.useState("");
  const [newQType, setNewQType] = React.useState<QuestionType>("single_choice");
  const [newQPrompt, setNewQPrompt] = React.useState("");
  const [newQDifficulty, setNewQDifficulty] = React.useState<QuestionDifficulty>("medium");
  const [newQPoints, setNewQPoints] = React.useState(1);
  const [newQNegative, setNewQNegative] = React.useState(0);
  const [newQExplanation, setNewQExplanation] = React.useState("");
  const [newQConceptId, setNewQConceptId] = React.useState<string>("");
  const [options, setOptions] = React.useState<
    Array<{ text: string; isCorrect: boolean; explanation: string }>
  >([
    { text: "Option A", isCorrect: true, explanation: "" },
    { text: "Option B", isCorrect: false, explanation: "" },
  ]);

  const loadQuestions = React.useCallback(async (bankId: string) => {
    try {
      const qData = await fetchQuestions(bankId, {
        q: searchQuery || undefined,
        question_type: typeFilter !== "all" ? typeFilter : undefined,
        difficulty: difficultyFilter !== "all" ? difficultyFilter : undefined,
      });
      setQuestions(qData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load questions");
    }
  }, [searchQuery, typeFilter, difficultyFilter]);

  React.useEffect(() => {
    let ignore = false;
    async function initBanks() {
      try {
        const [banksData, conceptsData] = await Promise.all([
          fetchQuestionBanks(),
          fetchConcepts().catch(() => []),
        ]);
        if (!ignore) {
          setBanks(banksData);
          setConcepts(conceptsData);
          if (banksData.length > 0) {
            setSelectedBank((prev) => prev || banksData[0]);
          }
        }
      } catch (err: unknown) {
        if (!ignore) setError(err instanceof Error ? err.message : "Failed to load question banks");
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    initBanks();
    return () => {
      ignore = true;
    };
  }, []);

  React.useEffect(() => {
    const bankId = selectedBank?.id;
    if (!bankId) return;
    let ignore = false;
    async function fetchBankQuestions(targetBankId: string) {
      try {
        const qData = await fetchQuestions(targetBankId, {
          q: searchQuery || undefined,
          question_type: typeFilter !== "all" ? typeFilter : undefined,
          difficulty: difficultyFilter !== "all" ? difficultyFilter : undefined,
        });
        if (!ignore) setQuestions(qData);
      } catch (err: unknown) {
        if (!ignore) setError(err instanceof Error ? err.message : "Failed to load questions");
      }
    }
    fetchBankQuestions(bankId);
    return () => {
      ignore = true;
    };
  }, [selectedBank, searchQuery, typeFilter, difficultyFilter]);

  const handleCreateBank = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBankTitle.trim()) return;
    try {
      const created = await createQuestionBank({
        title: newBankTitle.trim(),
        description: newBankDesc.trim() || undefined,
      });
      setBanks((prev) => [created, ...prev]);
      setSelectedBank(created);
      setShowBankModal(false);
      setNewBankTitle("");
      setNewBankDesc("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create bank");
    }
  };

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBank || !newQTitle.trim() || !newQPrompt.trim()) return;

    try {
      const payloadOptions =
        newQType === "single_choice" || newQType === "multiple_choice" || newQType === "true_false"
          ? options.map((opt, idx) => ({
              option_text: opt.text,
              option_order: idx + 1,
              is_correct: opt.isCorrect,
              explanation: opt.explanation || undefined,
            }))
          : undefined;

      await createQuestion(selectedBank.id, {
        title: newQTitle.trim(),
        question_type: newQType,
        prompt: newQPrompt.trim(),
        difficulty: newQDifficulty,
        points: Number(newQPoints),
        negative_marks: Number(newQNegative),
        explanation: newQExplanation.trim() || undefined,
        options: payloadOptions,
        concept_ids: newQConceptId ? [newQConceptId] : [],
      });

      setShowQuestionModal(false);
      setNewQTitle("");
      setNewQPrompt("");
      setNewQExplanation("");
      loadQuestions(selectedBank.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create question");
    }
  };

  const addOption = () => {
    setOptions((prev) => [...prev, { text: `Option ${String.fromCharCode(65 + prev.length)}`, isCorrect: false, explanation: "" }]);
  };

  const removeOption = (index: number) => {
    if (options.length <= 2) return;
    setOptions((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-border pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-primary" />
            Institutional Question Banks
          </h2>
          <p className="text-sm text-muted-foreground">
            Author authoritative, versioned questions mapped to canonical concepts and skills.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowBankModal(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            New Question Bank
          </Button>
          {selectedBank && (
            <Button onClick={() => setShowQuestionModal(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Question
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Grid: Left Bank Selector, Right Questions List */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Left Column: Bank List */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Question Banks ({banks.length})
          </h3>
          {loading && banks.length === 0 ? (
            <p className="text-sm text-muted-foreground">Loading banks...</p>
          ) : banks.length === 0 ? (
            <Card className="p-4 text-center text-sm text-muted-foreground">
              No question banks found. Click &quot;New Question Bank&quot; to create one.
            </Card>
          ) : (
            banks.map((bank) => (
              <Card
                key={bank.id}
                onClick={() => setSelectedBank(bank)}
                className={`cursor-pointer transition-all hover:border-primary/50 ${
                  selectedBank?.id === bank.id ? "border-primary bg-primary/5 shadow-sm" : ""
                }`}
              >
                <CardContent className="p-4 space-y-1">
                  <div className="flex justify-between items-start">
                    <p className="font-semibold text-sm text-foreground">{bank.title}</p>
                    <Badge variant="outline" className="text-xs">
                      {bank.visibility}
                    </Badge>
                  </div>
                  {bank.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2">{bank.description}</p>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Right Column: Questions in Selected Bank */}
        <div className="md:col-span-3 space-y-4">
          {selectedBank ? (
            <>
              {/* Filter Bar */}
              <div className="flex flex-wrap gap-3 items-center justify-between bg-card p-3 rounded-lg border border-border">
                <div className="flex-1 min-w-[200px] relative">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search questions by prompt or title..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 text-sm"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="text-xs border rounded-md px-2 py-1.5 bg-background text-foreground"
                  >
                    <option value="all">All Types</option>
                    <option value="single_choice">Single Choice</option>
                    <option value="multiple_choice">Multiple Choice</option>
                    <option value="true_false">True / False</option>
                    <option value="numeric">Numeric</option>
                    <option value="fill_blank">Fill in Blank</option>
                    <option value="short_answer">Short Answer</option>
                    <option value="coding">Coding</option>
                  </select>
                  <select
                    value={difficultyFilter}
                    onChange={(e) => setDifficultyFilter(e.target.value)}
                    className="text-xs border rounded-md px-2 py-1.5 bg-background text-foreground"
                  >
                    <option value="all">All Difficulties</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                    <option value="expert">Expert</option>
                  </select>
                </div>
              </div>

              {/* Questions List */}
              <div className="space-y-3">
                {questions.length === 0 ? (
                  <Card className="p-8 text-center text-muted-foreground">
                    <HelpCircle className="h-10 w-10 mx-auto text-muted-foreground/40 mb-2" />
                    <p className="font-medium">No questions found</p>
                    <p className="text-xs">Add questions to this bank to begin assembling blueprints.</p>
                  </Card>
                ) : (
                  questions.map((q) => {
                    const ver = q.current_version;
                    return (
                      <Card key={q.id} className="hover:border-border/80 transition-all">
                        <CardHeader className="p-4 pb-2">
                          <div className="flex justify-between items-start gap-2">
                            <div className="space-y-1">
                              <CardTitle className="text-base font-semibold">{q.title}</CardTitle>
                              <div className="flex flex-wrap gap-2 items-center text-xs text-muted-foreground">
                                <Badge variant="secondary" className="capitalize">
                                  {q.question_type.replace("_", " ")}
                                </Badge>
                                {ver && (
                                  <>
                                    <Badge
                                      variant={
                                        ver.difficulty === "easy"
                                          ? "outline"
                                          : ver.difficulty === "medium"
                                          ? "secondary"
                                          : "destructive"
                                      }
                                      className="capitalize"
                                    >
                                      {ver.difficulty}
                                    </Badge>
                                    <span className="flex items-center gap-1">
                                      <Award className="h-3 w-3" /> {ver.points} pts
                                    </span>
                                    {ver.negative_marks > 0 && (
                                      <span className="text-destructive">
                                        -{ver.negative_marks} neg
                                      </span>
                                    )}
                                    <span className="flex items-center gap-1">
                                      <Clock className="h-3 w-3" /> v{ver.version_number}
                                    </span>
                                  </>
                                )}
                              </div>
                            </div>
                            <Badge
                              variant={
                                q.status === "approved"
                                  ? "default"
                                  : q.status === "draft"
                                  ? "secondary"
                                  : "outline"
                              }
                            >
                              {q.status}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent className="p-4 pt-1 space-y-2">
                          {ver && (
                            <>
                              <p className="text-sm text-foreground/90 font-mono bg-muted/30 p-2.5 rounded border border-border/50">
                                {ver.prompt}
                              </p>

                              {/* Options preview for choice questions */}
                              {ver.options && ver.options.length > 0 && (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
                                  {ver.options.map((opt) => (
                                    <div
                                      key={opt.id}
                                      className={`text-xs p-2 rounded flex items-center justify-between border ${
                                        opt.is_correct
                                          ? "border-green-500/50 bg-green-500/10 text-green-700 dark:text-green-300"
                                          : "border-border/50 bg-background text-muted-foreground"
                                      }`}
                                    >
                                      <span>{opt.option_text}</span>
                                      {opt.is_correct && (
                                        <CheckCircle2 className="h-3.5 w-3.5 text-green-600 dark:text-green-400 shrink-0" />
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Concepts and skills */}
                              <div className="flex flex-wrap gap-1.5 pt-1">
                                {ver.concepts?.map((c) => (
                                  <Badge
                                    key={c.id}
                                    variant="outline"
                                    className="text-[10px] bg-primary/5 text-primary border-primary/20 gap-1"
                                  >
                                    <Layers className="h-2.5 w-2.5" />
                                    {c.concept_name || "Concept"}
                                  </Badge>
                                ))}
                                {ver.skills?.map((s) => (
                                  <Badge
                                    key={s.id}
                                    variant="outline"
                                    className="text-[10px] bg-amber-500/5 text-amber-600 dark:text-amber-400 border-amber-500/20 gap-1"
                                  >
                                    <Sparkles className="h-2.5 w-2.5" />
                                    {s.skill_title || "Skill"}
                                  </Badge>
                                ))}
                              </div>
                            </>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })
                )}
              </div>
            </>
          ) : (
            <Card className="p-8 text-center text-muted-foreground">
              Select or create a question bank to view and author questions.
            </Card>
          )}
        </div>
      </div>

      {/* Modal: Create Bank */}
      {showBankModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <Card className="w-full max-w-md shadow-2xl">
            <form onSubmit={handleCreateBank}>
              <CardHeader>
                <CardTitle>Create Question Bank</CardTitle>
                <CardDescription>
                  Group questions by institutional domain, department, or subject.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold">Bank Title *</label>
                  <Input
                    required
                    placeholder="e.g. Data Structures & Algorithms Core Bank"
                    value={newBankTitle}
                    onChange={(e) => setNewBankTitle(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold">Description</label>
                  <textarea
                    rows={3}
                    placeholder="Institutional repository for vetted algorithmic assessment items."
                    value={newBankDesc}
                    onChange={(e) => setNewBankDesc(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setShowBankModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Bank</Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}

      {/* Modal: Create Question */}
      {showQuestionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <Card className="w-full max-w-2xl my-8 shadow-2xl max-h-[90vh] flex flex-col">
            <form onSubmit={handleCreateQuestion} className="flex flex-col h-full overflow-hidden">
              <CardHeader className="border-b">
                <CardTitle>Author Question</CardTitle>
                <CardDescription>
                  Create an immutable versioned question item in &quot;{selectedBank?.title}&quot;.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-4 overflow-y-auto">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Title *</label>
                    <Input
                      required
                      placeholder="e.g. Binary Search Time Complexity"
                      value={newQTitle}
                      onChange={(e) => setNewQTitle(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Question Type</label>
                    <select
                      value={newQType}
                      onChange={(e) => setNewQType(e.target.value as QuestionType)}
                      className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                    >
                      <option value="single_choice">Single Choice</option>
                      <option value="multiple_choice">Multiple Choice</option>
                      <option value="true_false">True / False</option>
                      <option value="numeric">Numeric</option>
                      <option value="fill_blank">Fill in Blank</option>
                      <option value="short_answer">Short Answer</option>
                      <option value="coding">Coding</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold">Prompt *</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Enter the authoritative question prompt..."
                    value={newQPrompt}
                    onChange={(e) => setNewQPrompt(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Difficulty</label>
                    <select
                      value={newQDifficulty}
                      onChange={(e) => setNewQDifficulty(e.target.value as QuestionDifficulty)}
                      className="w-full h-9 px-2 rounded-md border border-input bg-background text-xs"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                      <option value="expert">Expert</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Points</label>
                    <Input
                      type="number"
                      min={1}
                      value={newQPoints}
                      onChange={(e) => setNewQPoints(Number(e.target.value))}
                      className="h-9 text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Negative Marks</label>
                    <Input
                      type="number"
                      min={0}
                      step={0.25}
                      value={newQNegative}
                      onChange={(e) => setNewQNegative(Number(e.target.value))}
                      className="h-9 text-xs"
                    />
                  </div>
                </div>

                {/* Concept Mapping */}
                {concepts.length > 0 && (
                  <div className="space-y-1">
                    <label className="text-xs font-semibold">Canonical Concept Mapping</label>
                    <select
                      value={newQConceptId}
                      onChange={(e) => setNewQConceptId(e.target.value)}
                      className="w-full h-9 px-2 rounded-md border border-input bg-background text-xs"
                    >
                      <option value="">-- No Concept Mapped --</option>
                      {concepts.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Options for MCQ / True False */}
                {(newQType === "single_choice" ||
                  newQType === "multiple_choice" ||
                  newQType === "true_false") && (
                  <div className="space-y-2 border-t pt-3">
                    <div className="flex justify-between items-center">
                      <label className="text-xs font-semibold">Options &amp; Correct Key</label>
                      {newQType !== "true_false" && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={addOption}
                          className="h-7 text-xs gap-1"
                        >
                          <Plus className="h-3 w-3" /> Add Option
                        </Button>
                      )}
                    </div>
                    {options.map((opt, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <input
                          type={newQType === "single_choice" || newQType === "true_false" ? "radio" : "checkbox"}
                          name="correct_option"
                          checked={opt.isCorrect}
                          onChange={(e) => {
                            if (newQType === "single_choice" || newQType === "true_false") {
                              setOptions(
                                options.map((o, i) => ({ ...o, isCorrect: i === idx }))
                              );
                            } else {
                              const updated = [...options];
                              updated[idx].isCorrect = e.target.checked;
                              setOptions(updated);
                            }
                          }}
                        />
                        <Input
                          value={opt.text}
                          onChange={(e) => {
                            const updated = [...options];
                            updated[idx].text = e.target.value;
                            setOptions(updated);
                          }}
                          placeholder={`Option ${idx + 1}`}
                          className="text-xs h-8 flex-1"
                        />
                        {options.length > 2 && newQType !== "true_false" && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeOption(idx)}
                            className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                          >
                            ×
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                <div className="space-y-1 border-t pt-3">
                  <label className="text-xs font-semibold">Explanation (Post-Submission)</label>
                  <textarea
                    rows={2}
                    placeholder="Rationale displayed according to feedback policy..."
                    value={newQExplanation}
                    onChange={(e) => setNewQExplanation(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs"
                  />
                </div>
              </CardContent>
              <CardFooter className="border-t p-4 flex justify-end gap-2 bg-muted/10">
                <Button type="button" variant="outline" onClick={() => setShowQuestionModal(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Question</Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
