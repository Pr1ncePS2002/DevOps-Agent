"use client";

import {
  createChatSession,
  getChatMessages,
  listChatSessions,
  sendChatMessage,
} from "@/lib/api";
import type { ChatMessage, ChatSession, Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Bot, MessageSquarePlus, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChatInput } from "./chat-input";
import { ChatMessageBubble } from "./chat-message";

interface ChatPanelProps {
  projects: Project[];
}

export function ChatPanel({ projects }: ChatPanelProps) {
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    () => projects.at(0)?.id ?? null
  );
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load sessions when project changes
  useEffect(() => {
    if (!selectedProjectId) return;
    setActiveSession(null);
    setMessages([]);
    listChatSessions(selectedProjectId)
      .then((s) => {
        setSessions(s);
        if (s.length > 0) {
          loadSession(s[0]);
        }
      })
      .catch(() => setSessions([]));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProjectId]);

  const loadSession = useCallback(async (session: ChatSession) => {
    setActiveSession(session);
    setIsLoadingHistory(true);
    setError(null);
    try {
      const history = await getChatMessages(session.id);
      setMessages(history);
    } catch {
      setError("Failed to load conversation history.");
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  const handleNewConversation = useCallback(async () => {
    if (!selectedProjectId) return;
    setError(null);
    try {
      const session = await createChatSession(selectedProjectId);
      setSessions((prev) => [session, ...prev]);
      setActiveSession(session);
      setMessages([]);
    } catch {
      setError("Failed to create conversation.");
    }
  }, [selectedProjectId]);

  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;

    // Ensure we have an active session
    let session = activeSession;
    if (!session) {
      if (!selectedProjectId) {
        setError("Select a project first.");
        return;
      }
      try {
        session = await createChatSession(selectedProjectId);
        setSessions((prev) => [session!, ...prev]);
        setActiveSession(session);
      } catch {
        setError("Failed to start conversation.");
        return;
      }
    }

    const userContent = inputValue.trim();
    setInputValue("");
    setIsLoading(true);
    setError(null);

    // Optimistic user message
    const optimisticMsg: ChatMessage = {
      id: Date.now(),
      session_id: session.id,
      role: "user",
      content: userContent,
      message_type: "text",
      metadata: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMsg]);

    try {
      const response = await sendChatMessage(session.id, userContent);

      // Replace optimistic + add real assistant reply
      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        session_id: session.id,
        role: "assistant",
        content: response.response,
        message_type: response.plan_id ? "plan_preview" : response.type === "error" ? "error" : "text",
        metadata: response.plan_id ? { plan_id: response.plan_id } : {},
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message.");
      setMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id));
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, activeSession, selectedProjectId]);

  return (
    <div className="flex h-[calc(100vh-16rem)] min-h-[520px] gap-4">
      {/* Sidebar */}
      <div className="hidden w-52 shrink-0 flex-col gap-2 lg:flex">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.3em] text-white/40">Sessions</p>
          <button
            type="button"
            onClick={handleNewConversation}
            disabled={!selectedProjectId}
            title="New conversation"
            className="rounded-lg p-1 text-white/40 transition hover:text-accent-400 disabled:opacity-30"
          >
            <MessageSquarePlus className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1">
          {sessions.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => loadSession(s)}
              className={cn(
                "w-full rounded-xl px-3 py-2 text-left text-xs transition",
                activeSession?.id === s.id
                  ? "bg-accent-500/20 text-accent-300 border border-accent-500/30"
                  : "text-white/50 hover:bg-white/5 hover:text-white/80"
              )}
            >
              <p className="truncate font-medium">Session #{s.id}</p>
              <p className="mt-0.5 text-[10px] text-white/30">
                {new Date(s.last_message_at).toLocaleDateString()}
              </p>
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-white/25 px-1">No sessions yet</p>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col rounded-3xl border border-white/5 bg-surface-800/70 shadow-card overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 px-5 py-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent-500/20 border border-accent-500/30">
              <Bot className="h-4 w-4 text-accent-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white/90">DevOps AI Assistant</p>
              {activeSession && (
                <p className="text-[10px] text-white/30">Session #{activeSession.id}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Project selector */}
            <select
              value={selectedProjectId ?? ""}
              onChange={(e) => setSelectedProjectId(Number(e.target.value) || null)}
              className="rounded-xl border border-white/10 bg-black/20 px-2 py-1 text-xs text-white/70 focus:border-accent-500/50 focus:outline-none"
              disabled={projects.length === 0}
            >
              {projects.length === 0 ? (
                <option value="">No projects</option>
              ) : (
                projects.map((p) => (
                  <option key={p.id} value={p.id} className="bg-surface-900">
                    {p.name}
                  </option>
                ))
              )}
            </select>
            <button
              type="button"
              onClick={handleNewConversation}
              disabled={!selectedProjectId}
              title="New conversation"
              className="flex items-center gap-1.5 rounded-xl border border-white/10 px-2 py-1.5 text-xs text-white/50 transition hover:border-accent-500/30 hover:text-accent-400 disabled:opacity-30"
            >
              <RefreshCw className="h-3 w-3" />
              New
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {isLoadingHistory ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-sm text-white/30">Loading history...</p>
            </div>
          ) : messages.length === 0 ? (
            <EmptyState onSuggest={setInputValue} />
          ) : (
            messages.map((msg) => (
              <ChatMessageBubble key={msg.id} message={msg} />
            ))
          )}
          {isLoading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {error && (
          <p className="mx-5 mb-2 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-400">
            {error}
          </p>
        )}

        {/* Input */}
        <div className="border-t border-white/5 px-5 py-4">
          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSend}
            isLoading={isLoading}
            disabled={projects.length === 0}
          />
          <p className="mt-2 text-center text-[10px] text-white/20">
            Powered by Gemini 2.5 Pro · Enter to send · Shift+Enter for newline
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Subcomponents ─────────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="mt-1 h-7 w-7 shrink-0 rounded-full flex items-center justify-center text-xs font-bold bg-surface-700 text-white/70 border border-white/10">
        AI
      </div>
      <div className="rounded-2xl border border-white/5 bg-surface-700/80 px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-accent-400 animate-bounce [animation-delay:0ms]" />
          <span className="h-1.5 w-1.5 rounded-full bg-accent-400 animate-bounce [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 rounded-full bg-accent-400 animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onSuggest }: { onSuggest: (text: string) => void }) {
  const suggestions = [
    "Deploy the latest version to staging",
    "What's currently running?",
    "Roll back to the previous version",
    "Deploy to production with smoke tests",
  ];

  return (
    <div className="flex flex-col items-center justify-center py-10 gap-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-500/10 border border-accent-500/20">
        <Bot className="h-6 w-6 text-accent-400/70" />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-white/60">How can I help you deploy today?</p>
        <p className="mt-1 text-xs text-white/30">Ask me anything about your project</p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSuggest(s)}
            className="rounded-xl border border-white/10 px-3 py-1.5 text-xs text-white/50 transition hover:border-accent-500/30 hover:text-accent-300"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
