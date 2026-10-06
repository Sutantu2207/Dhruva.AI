"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchAIConversations,
  createAIConversation,
  fetchAIConversation,
  sendAIMessage,
} from "@/lib/api";
import { AIConversation, AIMessage } from "@/lib/types";
import {
  Bot,
  User,
  Send,
  Plus,
  ShieldCheck,
  FileQuestion,
  ListChecks,
  PenTool,
  AlertTriangle,
  FileText,
} from "lucide-react";

export default function FacultyAICopilotPage() {
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<AIConversation | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  const selectConversation = React.useCallback(async (id: string) => {
    try {
      const full = await fetchAIConversation(id);
      setActiveConversation(full);
      setMessages(full.messages || []);
    } catch (e) {
      console.error("Failed to fetch conversation details:", e);
    }
  }, []);

  const loadConversations = React.useCallback(async () => {
    try {
      setLoading(true);
      const list = await fetchAIConversations("FACULTY");
      setConversations(list);
      if (list.length > 0) {
        selectConversation(list[0].id);
      }
    } catch (e) {
      console.error("Failed to load faculty conversations:", e);
    } finally {
      setLoading(false);
    }
  }, [selectConversation]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  async function handleNewConversation() {
    try {
      const created = await createAIConversation({
        scope: "FACULTY",
        title: "Faculty Assistant Session",
        mode: "EXPLAIN",
      });
      setConversations((prev) => [created, ...prev]);
      setActiveConversation(created);
      setMessages([]);
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
          scope: "FACULTY",
          title: inputPrompt.slice(0, 30),
          mode: "EXPLAIN",
        });
        setConversations((prev) => [targetConv!, ...prev]);
        setActiveConversation(targetConv);
      } catch (err) {
        console.error("Failed to initialize conversation:", err);
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
    } catch (err) {
      console.error("Failed to send message:", err);
      const fallbackMsg: AIMessage = {
        id: `err-${Date.now()}`,
        conversation_id: targetConv.id,
        role: "ASSISTANT",
        content: "Dhruva AI Copilot is temporarily unavailable. Your course and grading records remain unchanged.",
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

  return (
    <div className="flex h-screen bg-neutral-950 text-neutral-100 font-sans">
      {/* Sidebar */}
      <div className="w-80 border-r border-neutral-800 bg-neutral-900/60 flex flex-col p-4">
        <div className="flex items-center justify-between pb-4 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 font-bold">
              Φ
            </div>
            <div>
              <h2 className="font-semibold text-sm text-neutral-200">Faculty AI Copilot</h2>
              <span className="text-[10px] text-indigo-400 font-medium">Drafting & Analytics Assistant</span>
            </div>
          </div>
          <Link
            href="/ai/trust"
            className="text-xs text-neutral-400 hover:text-indigo-400 transition-colors"
            title="AI Trust Manifest"
          >
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
          </Link>
        </div>

        <button
          onClick={handleNewConversation}
          className="mt-4 w-full py-2.5 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          New Copilot Session
        </button>

        {/* Faculty Workflow Prompts */}
        <div className="mt-4">
          <label className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider">
            Quick Assistance
          </label>
          <div className="grid grid-cols-1 gap-1.5 mt-2 text-xs">
            <button
              onClick={() => setInputPrompt("Draft 3 conceptual multiple-choice questions for Binary Search Trees.")}
              className="p-2 rounded bg-neutral-900/60 border border-neutral-800 hover:bg-neutral-800/80 text-left text-neutral-300 flex items-center gap-2"
            >
              <FileQuestion className="w-3.5 h-3.5 text-indigo-400" />
              <span>Draft Assessment Questions</span>
            </button>
            <button
              onClick={() => setInputPrompt("Generate a 4-criterion grading rubric for a full-stack project.")}
              className="p-2 rounded bg-neutral-900/60 border border-neutral-800 hover:bg-neutral-800/80 text-left text-neutral-300 flex items-center gap-2"
            >
              <ListChecks className="w-3.5 h-3.5 text-indigo-400" />
              <span>Generate Rubric Template</span>
            </button>
            <button
              onClick={() => setInputPrompt("Summarize learning difficulties in my assigned course offerings.")}
              className="p-2 rounded bg-neutral-900/60 border border-neutral-800 hover:bg-neutral-800/80 text-left text-neutral-300 flex items-center gap-2"
            >
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span>Summarize Course Difficulties</span>
            </button>
          </div>
        </div>

        {/* Sessions List */}
        <div className="mt-5 flex-1 overflow-y-auto space-y-1 pr-1">
          <label className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider">
            Previous Consultations
          </label>
          {loading && <p className="text-xs text-neutral-500 mt-2">Loading sessions...</p>}
          {!loading && conversations.length === 0 && (
            <p className="text-xs text-neutral-500 mt-2">No prior consultations.</p>
          )}
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className={`w-full text-left p-2.5 rounded-lg text-xs truncate transition-colors ${
                activeConversation?.id === conv.id
                  ? "bg-neutral-800 text-neutral-200 border border-neutral-700"
                  : "text-neutral-400 hover:bg-neutral-800/40 hover:text-neutral-300"
              }`}
            >
              {conv.title}
            </button>
          ))}
        </div>

        {/* Draft Notice */}
        <div className="mt-auto pt-3 border-t border-neutral-800 text-[11px] text-amber-400/90 flex items-start gap-1.5">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
          <span>All AI-generated questions and rubrics are AI DRAFTS. Faculty approval is mandatory before publishing.</span>
        </div>
      </div>

      {/* Main Conversation Canvas */}
      <div className="flex-1 flex flex-col bg-neutral-950">
        <div className="h-14 border-b border-neutral-800 flex items-center justify-between px-6 bg-neutral-900/30">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-pulse" />
            <h1 className="text-sm font-medium text-neutral-200">
              {activeConversation ? activeConversation.title : "Faculty AI Copilot"}
            </h1>
            <span className="text-xs px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-800 text-indigo-400 font-mono">
              ROLE: FACULTY
            </span>
          </div>

          <div className="text-xs text-neutral-400 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            <span>Offering-Scoped Authorization Active</span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="max-w-xl mx-auto my-12 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-indigo-900/30 border border-indigo-600/30 flex items-center justify-center mx-auto text-indigo-400">
                <PenTool className="w-6 h-6" />
              </div>
              <h2 className="text-lg font-semibold text-neutral-200">How can I assist your teaching today?</h2>
              <p className="text-xs text-neutral-400 leading-relaxed">
                Draft assessment questions, create grading rubrics, analyze course-level intervention signals, or summarize prerequisite gaps for your section.
              </p>
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
                <div className="w-7 h-7 rounded-lg bg-indigo-950/80 border border-indigo-800 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`rounded-xl p-4 text-xs leading-relaxed ${
                  msg.role === "USER"
                    ? "bg-indigo-600 text-white max-w-lg shadow-sm"
                    : "bg-neutral-900 border border-neutral-800 text-neutral-200 max-w-2xl"
                }`}
              >
                {msg.role === "ASSISTANT" && (
                  <div className="mb-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800 text-[10px] text-amber-300 font-mono">
                    <AlertTriangle className="w-3 h-3 text-amber-400" />
                    AI DRAFT — Requires Faculty Review
                  </div>
                )}
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-neutral-800 space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider">
                      Grounding References
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.citations.map((c) => (
                        <div
                          key={c.id}
                          className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-neutral-950/80 border border-neutral-800 text-[11px] text-indigo-300"
                        >
                          <span>{c.title}</span>
                        </div>
                      ))}
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
              <div className="w-7 h-7 rounded-lg bg-indigo-950/80 border border-indigo-800 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5 animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-3.5 text-xs text-neutral-400 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                <span>Preparing faculty draft and verifying course context...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="p-4 border-t border-neutral-800 bg-neutral-900/40">
          <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto flex gap-2">
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder="Ask Faculty AI Copilot..."
              disabled={sending}
              className="flex-1 bg-neutral-950 border border-neutral-800 rounded-lg px-4 py-2.5 text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-indigo-500/80 transition-colors"
            />
            <button
              type="submit"
              disabled={sending || !inputPrompt.trim()}
              className="px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-xs font-medium flex items-center gap-1.5 transition-all"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
