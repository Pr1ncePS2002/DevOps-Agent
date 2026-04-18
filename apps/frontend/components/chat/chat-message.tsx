"use client";

import { approvePlan } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Check, Loader2, TriangleAlert } from "lucide-react";
import { useState } from "react";

interface ChatMessageProps {
  message: ChatMessage;
  onPlanApproved?: (executionId: number) => void;
}

export function ChatMessageBubble({ message, onPlanApproved }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isError = message.message_type === "error";
  const hasPlan = message.message_type === "plan_preview" && message.metadata?.plan_id != null;

  const timestamp = new Date(message.created_at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar dot */}
      <div
        className={cn(
          "mt-1 h-7 w-7 shrink-0 rounded-full flex items-center justify-center text-xs font-bold",
          isUser
            ? "bg-accent-500/80 text-surface-900"
            : "bg-surface-700 text-white/70 border border-white/10"
        )}
      >
        {isUser ? "U" : "AI"}
      </div>

      <div className={cn("flex max-w-[80%] flex-col gap-1", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-accent-500/20 border border-accent-500/30 text-white/90"
              : isError
              ? "bg-red-500/10 border border-red-500/20 text-red-300"
              : "bg-surface-700/80 border border-white/5 text-white/85 backdrop-blur-sm"
          )}
        >
          {isError && (
            <div className="mb-1 flex items-center gap-1.5 text-xs text-red-400">
              <TriangleAlert className="h-3 w-3" />
              <span>Error</span>
            </div>
          )}
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {hasPlan && (
          <InlinePlanCard
            planId={message.metadata.plan_id as number}
            onApproved={onPlanApproved}
          />
        )}

        <span className="text-[10px] text-white/25">{timestamp}</span>
      </div>
    </div>
  );
}

// ── Inline plan card ──────────────────────────────────────────────────────────

interface InlinePlanCardProps {
  planId: number;
  onApproved?: (executionId: number) => void;
}

function InlinePlanCard({ planId, onApproved }: InlinePlanCardProps) {
  const [loading, setLoading] = useState(false);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleApprove = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await approvePlan(planId);
      setApproved(true);
      onApproved?.(result.execution_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-1 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 backdrop-blur-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-white/40">Deployment Plan</p>
          <p className="mt-0.5 text-xs text-white/60">Plan #{planId} — pending approval</p>
        </div>
        {approved ? (
          <div className="flex items-center gap-1.5 rounded-xl bg-green-500/20 px-3 py-1.5 text-xs font-semibold text-green-400">
            <Check className="h-3.5 w-3.5" />
            Approved
          </div>
        ) : (
          <button
            type="button"
            onClick={handleApprove}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-xl bg-accent-500/80 px-3 py-1.5 text-xs font-semibold text-surface-900 transition hover:bg-accent-500 disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
            Approve & Execute
          </button>
        )}
      </div>
      {error && <p className="mt-1.5 text-xs text-red-400">{error}</p>}
    </div>
  );
}
