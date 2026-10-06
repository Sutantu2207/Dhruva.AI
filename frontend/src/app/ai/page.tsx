"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchAIConversations,
  createAIConversation,
  fetchAIConversation,
  sendAIMessage,
  submitAIFeedback,
} from "@/lib/api";
import {
  AIConversation,
  AIMessage,
  AIConversationalMode,
} from "@/lib/types";
import {
  Bot,
  User,
  Send,
  Plus,
  ShieldCheck,
  BookOpen,
  Sparkles,
  HelpCircle,
  Code,
  Compass,
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
  Info,
} from "lucide-react";

const MODES: { mode: AIConversationalMode; label: string; icon: React.ReactNode; desc: string }[] = [
  { mode: "EXPLAIN", label: "Explain Concept", icon: <BookOpen className="w-4 h-4" />, desc: "Clear, grounded explanations of concepts" },
  { mode: "SOCRATIC", label: "Socratic Tutor", icon: <HelpCircle className="w-4 h-4" />, desc: "Guides your thinking with targeted questions" },
  { mode: "PRACTICE", label: "Practice Drills", icon: <Code className="w-4 h-4" />, desc: "Drills with instant feedback" },
  { mode: "REVIEW", label: "Spaced Review", icon: <Compass className="w-4 h-4" />, desc: "Focuses on retention & SM-2 priorities" },
  { mode: "EXAM_PREP", label: "Exam Prep", icon: <CheckCircle2 className="w-4 h-4" />, desc: "High-yield topics & prerequisite checks" },
  { mode: "PROJECT_GUIDANCE", label: "Project Mentor", icon: <Sparkles className="w-4 h-4" />, desc: "Architecture & skill integration advice" },
];

export default function StudentAIMentorPage() {
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<AIConversation | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [selectedMode, setSelectedMode] = useState<AIConversationalMode>("EXPLAIN");
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, number>>({});

  const selectConversation = React.useCallback(async (id: string) => {
    try {
      const full = await fetchAIConversation(id);
      setActiveConversation(full);
      setMessages(full.messages || []);
      setSelectedMode(full.mode);
    } catch (e) {
      console.error("Failed to fetch conversation details:", e);
    }
  }, []);

  const loadConversations = React.useCallback(async () => {
    try {
      setLoading(true);
      const list = await fetchAIConversations("STUDENT");
      setConversations(list);
      if (list.length > 0) {
        selectConversation(list[0].id);
      }
    } catch (e) {
      console.error("Failed to load conversations:", e);
    } finally {
      setLoading(false);
    }
  }, [selectConversation]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  async function handleNewConversation(mode: AIConversationalMode = selectedMode) {
    try {
      const created = await createAIConversation({
        scope: "STUDENT",
        title: `${mode.replace("_", " ")} Session`,
        mode,
      });
      setConversations((prev) => [created, ...prev]);
      setActiveConversation(created);
      setMessages([]);
      setSelectedMode(mode);
    } catch (e) {
      console.error("Failed to create conversation:", e);
    }
  }

  async function handleSendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!inputPrompt.trim() || sending) return;

    let targetConv = activeConversation;
    if (!targetConv) {
      try {
        targetConv = await createAIConversation({
          scope: "STUDENT",
          title: inputPrompt.slice(0, 30),
          mode: selectedMode,
        });
        setConversations((prev) => [targetConv!, ...prev]);
        setActiveConversation(targetConv);
      } catch (err) {
        console.error("Failed to create initial conversation:", err);
        return;
      }
    }

    const userMessage: AIMessage = {
      id: `temp-${Date.now()}`,
      conversation_id: targetConv.id,
      role: "USER",
      content: inputPrompt,
      provider: "client",
      model: "input",
      input_tokens: 0,
      output_tokens: 0,
      latency_ms: 0,
      status: "COMPLETED",
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const promptToSend = inputPrompt;
    setInputPrompt("");
    setSending(true);

    try {
      const reply = await sendAIMessage(targetConv.id, {
        content: promptToSend,
      });
      setMessages((prev) => [...prev, reply]);
    } catch (err: unknown) {
      console.error("Message send failure:", err);
      const fallbackMsg: AIMessage = {
        id: `err-${Date.now()}`,
        conversation_id: targetConv.id,
        role: "ASSISTANT",
        content: "Dhruva AI is temporarily unable to complete that request. Your academic data remains unchanged.",
        provider: "error",
        model: "fallback",
        input_tokens: 0,
        output_tokens: 0,
        latency_ms: 0,
        status: "FAILED",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setSending(false);
    }
  }

  async function handleRateMessage(messageId: string, rating: number) {
    try {
      await submitAIFeedback({ message_id: messageId, rating });
      setFeedbackSent((prev) => ({ ...prev, [messageId]: rating }));
    } catch (e) {
      console.error("Failed to submit feedback:", e);
    }
  }

  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-100 font-sans">
      {/* Sidebar: Conversations & Modes */}
      <div className="w-80 border-r border-neutral-800 bg-neutral-900/60 flex flex-col p-4">
        {/* Branding & Trust Link */}
        <div className="flex items-center justify-between pb-4 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold">
              Δ
            </div>
            <div>
              <h2 className="font-semibold text-sm text-neutral-200">Dhruva AI Mentor</h2>
              <span className="text-[10px] text-emerald-400 font-medium">Grounded Explainer</span>
            </div>
          </div>
          <Link
            href="/ai/trust"
            className="text-xs text-neutral-400 hover:text-emerald-400 transition-colors flex items-center gap-1"
            title="Dhruva AI Trust & Transparency Manifest"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-[11px]">Trust</span>
          </Link>
        </div>

        {/* New Session Button */}
        <button
          onClick={() => handleNewConversation(selectedMode)}
          className="mt-4 w-full py-2.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          New Learning Session
        </button>

        {/* Learning Mode Selection */}
        <div className="mt-4">
          <label className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider">
            Pedagogical Mode
          </label>
          <div className="grid grid-cols-2 gap-1.5 mt-2">
            {MODES.map((item) => (
              <button
                key={item.mode}
                onClick={() => {
                  setSelectedMode(item.mode);
                  if (activeConversation && activeConversation.mode !== item.mode) {
                    handleNewConversation(item.mode);
                  }
                }}
                className={`flex items-center gap-1.5 p-2 rounded text-left text-xs transition-colors border ${
                  selectedMode === item.mode
                    ? "bg-neutral-800 border-emerald-500/50 text-emerald-400 font-medium"
                    : "bg-neutral-900/40 border-neutral-800 text-neutral-400 hover:bg-neutral-800/60"
                }`}
              >
                {item.icon}
                <span className="truncate">{item.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Conversation History List */}
        <div className="mt-5 flex-1 overflow-y-auto space-y-1 pr-1">
          <label className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider">
            Recent Sessions
          </label>
          {loading && <p className="text-xs text-neutral-500 mt-2">Loading sessions...</p>}
          {!loading && conversations.length === 0 && (
            <p className="text-xs text-neutral-500 mt-2">No previous sessions found.</p>
          )}
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className={`w-full text-left p-2.5 rounded-lg text-xs truncate transition-colors flex items-center justify-between ${
                activeConversation?.id === conv.id
                  ? "bg-neutral-800 text-neutral-200 border border-neutral-700"
                  : "text-neutral-400 hover:bg-neutral-800/40 hover:text-neutral-300"
              }`}
            >
              <span className="truncate">{conv.title}</span>
              <span className="text-[10px] text-neutral-400 font-mono ml-2 shrink-0">{conv.mode}</span>
            </button>
          ))}
        </div>

        {/* Academic Authority Principle Notice */}
        <div className="mt-auto pt-3 border-t border-neutral-800 text-[11px] text-neutral-400 flex items-start gap-2">
          <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <span>
            Deterministic Dhruva engines remain the sole source of academic truth. AI tutors and explains.
          </span>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex-1 flex flex-col bg-neutral-950">
        {/* Top Header Bar */}
        <div className="h-14 border-b border-neutral-800 flex items-center justify-between px-6 bg-neutral-900/30">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h1 className="text-sm font-medium text-neutral-200">
              {activeConversation ? activeConversation.title : "New Student AI Session"}
            </h1>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400 font-mono">
              MODE: {selectedMode}
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs text-neutral-400">
            <span className="flex items-center gap-1.5 text-neutral-400">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Verified Scope Isolation Active
            </span>
          </div>
        </div>

        {/* Message Trajectory View */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="max-w-xl mx-auto my-12 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-900/30 border border-emerald-600/30 flex items-center justify-center mx-auto text-emerald-400">
                <Bot className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-semibold text-neutral-200">How can I assist your learning today?</h2>
              <p className="text-xs text-neutral-400 leading-relaxed">
                Ask about your verified concept masteries, current remediation plan, prerequisite concepts,
                spaced repetition review list, or career skill gaps.
              </p>

              <div className="grid grid-cols-2 gap-2 text-left pt-2">
                {[
                  "What should I study today based on my mastery?",
                  "Why am I struggling with my weak concepts?",
                  "Explain my current remediation plan.",
                  "How does my project support my career readiness?",
                ].map((samplePrompt) => (
                  <button
                    key={samplePrompt}
                    onClick={() => {
                      setInputPrompt(samplePrompt);
                    }}
                    className="p-2.5 rounded-lg border border-neutral-800 bg-neutral-900/60 text-xs text-neutral-300 hover:border-emerald-500/50 hover:bg-neutral-800/60 transition-all text-left"
                  >
                    {samplePrompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-3xl ${
                msg.role === "USER" ? "ml-auto justify-end" : "mr-auto justify-start"
              }`}
            >
              {msg.role !== "USER" && (
                <div className="w-7 h-7 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`rounded-xl p-4 text-xs leading-relaxed ${
                  msg.role === "USER"
                    ? "bg-emerald-600 text-white max-w-lg shadow-sm"
                    : "bg-neutral-900 border border-neutral-800 text-neutral-200 max-w-2xl"
                }`}
              >
                {/* Message Body */}
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Grounding Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-neutral-800 space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider">
                      Verified Dhruva Citations
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.citations.map((c) => (
                        <div
                          key={c.id}
                          className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-neutral-950/80 border border-neutral-800 text-[11px] text-emerald-300"
                        >
                          <BookOpen className="w-3 h-3 text-emerald-400" />
                          <span>{c.title}</span>
                          <span className="text-[10px] text-neutral-400">({Math.round(c.relevance_score * 100)}%)</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Deterministic Tool Invocations Footnote */}
                {msg.tool_invocations && msg.tool_invocations.length > 0 && (
                  <div className="mt-2 text-[10px] text-neutral-400 flex items-center gap-1 font-mono">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    <span>Engines consulted: {msg.tool_invocations.map((t) => t.tool_name).join(", ")}</span>
                  </div>
                )}

                {/* Turn Feedback */}
                {msg.role === "ASSISTANT" && (
                  <div className="mt-3 pt-2 border-t border-neutral-800/60 flex items-center justify-between text-[10px] text-neutral-400">
                    <span>Model: {msg.model}</span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleRateMessage(msg.id, 1)}
                        className={`p-1 rounded hover:text-emerald-400 transition-colors ${
                          feedbackSent[msg.id] === 1 ? "text-emerald-400 font-bold" : ""
                        }`}
                        title="Helpful"
                      >
                        <ThumbsUp className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleRateMessage(msg.id, -1)}
                        className={`p-1 rounded hover:text-rose-400 transition-colors ${
                          feedbackSent[msg.id] === -1 ? "text-rose-400 font-bold" : ""
                        }`}
                        title="Not helpful"
                      >
                        <ThumbsDown className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {msg.role === "USER" && (
                <div className="w-7 h-7 rounded-lg bg-neutral-800 border border-neutral-700 text-neutral-300 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="flex gap-3 max-w-xl mr-auto">
              <div className="w-7 h-7 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5 animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-3.5 text-xs text-neutral-400 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>Resolving academic context & consulting deterministic engines...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Composer */}
        <div className="p-4 border-t border-neutral-800 bg-neutral-900/40">
          <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto flex gap-2">
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder="Ask your Dhruva AI tutor..."
              disabled={sending}
              className="flex-1 bg-neutral-950 border border-neutral-800 rounded-lg px-4 py-2.5 text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-emerald-500/80 transition-colors"
            />
            <button
              type="submit"
              disabled={sending || !inputPrompt.trim()}
              className="px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-medium flex items-center gap-1.5 transition-all"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </form>
          <div className="max-w-3xl mx-auto mt-2 text-[10px] text-neutral-400 text-center">
            AI responses are grounded on your verified curriculum, mastery and progress records. Prompt injection and data exfiltration are defended in code.
          </div>
        </div>
      </div>
    </div>
  );
}
