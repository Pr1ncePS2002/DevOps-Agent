"use client";

import { cn } from "@/lib/utils";
import { Loader2, Send } from "lucide-react";
import { useRef } from "react";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function ChatInput({ value, onChange, onSend, isLoading, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && !disabled && value.trim()) {
        onSend();
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  };

  const canSend = !isLoading && !disabled && value.trim().length > 0;

  return (
    <div className="flex items-end gap-3 rounded-2xl border border-white/10 bg-black/30 p-3 focus-within:border-accent-500/50 transition">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        rows={1}
        placeholder="Ask me to deploy, check status, or explain anything..."
        disabled={disabled || isLoading}
        className="flex-1 resize-none bg-transparent text-sm text-white/90 placeholder-white/25 focus:outline-none disabled:opacity-50"
        style={{ minHeight: "24px", maxHeight: "120px" }}
      />
      <button
        type="button"
        onClick={onSend}
        disabled={!canSend}
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition",
          canSend
            ? "bg-accent-500/80 text-surface-900 hover:bg-accent-500"
            : "bg-white/5 text-white/20"
        )}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </button>
    </div>
  );
}
