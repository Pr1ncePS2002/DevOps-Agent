"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle, Info, Sparkles, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/config";

interface DeploymentSummary {
  summary: string;
  key_events: string[];
  root_cause: string | null;
  recommendations: string[];
  severity: "info" | "warning" | "critical";
}

interface ExecutionSummaryProps {
  executionId: number;
  status: string;
}

const severityConfig = {
  info: {
    bg: "bg-green-500/10 border-green-500/20",
    icon: <CheckCircle className="h-5 w-5 text-green-400" />,
    label: "Deployment Succeeded",
    labelColor: "text-green-400",
  },
  warning: {
    bg: "bg-yellow-500/10 border-yellow-500/20",
    icon: <AlertTriangle className="h-5 w-5 text-yellow-400" />,
    label: "Deployment Warning",
    labelColor: "text-yellow-400",
  },
  critical: {
    bg: "bg-red-500/10 border-red-500/20",
    icon: <XCircle className="h-5 w-5 text-red-400" />,
    label: "Deployment Failed",
    labelColor: "text-red-400",
  },
};

export function ExecutionSummary({ executionId, status }: ExecutionSummaryProps) {
  const [data, setData] = useState<DeploymentSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isFinished = ["succeeded", "failed", "rolled_back"].includes(status);

  const fetchSummary = useCallback(async () => {
    if (!isFinished) return;
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/executions/${executionId}/summary`);
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail);
      }
      const json: DeploymentSummary = await res.json();
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load summary");
    } finally {
      setLoading(false);
    }
  }, [executionId, isFinished]);

  useEffect(() => {
    if (isFinished) fetchSummary();
  }, [isFinished, fetchSummary]);

  if (!isFinished) return null;

  if (loading) {
    return (
      <div className="rounded-2xl border border-white/5 bg-surface-800/60 p-5 animate-pulse">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-accent-300 animate-spin" />
          <span className="text-sm text-white/50">Generating AI summary...</span>
        </div>
        <div className="space-y-2">
          <div className="h-4 bg-surface-700/50 rounded w-3/4" />
          <div className="h-4 bg-surface-700/50 rounded w-1/2" />
        </div>
      </div>
    );
  }

  if (error || !data) return null;

  const config = severityConfig[data.severity] ?? severityConfig.info;

  return (
    <div className={cn("rounded-2xl border p-5 space-y-4", config.bg)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {config.icon}
          <span className={cn("text-sm font-medium", config.labelColor)}>{config.label}</span>
        </div>
        <span className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-white/30 border border-white/10 rounded-full px-2 py-0.5">
          <Sparkles className="h-3 w-3" />
          AI Generated
        </span>
      </div>

      {/* Summary */}
      <p className="text-sm text-white/80 leading-relaxed">{data.summary}</p>

      {/* Key events */}
      {data.key_events.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/40 mb-2">Key Events</p>
          <ol className="space-y-1">
            {data.key_events.map((event, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-white/60">
                <span className="text-white/30 mt-0.5 flex-shrink-0">{i + 1}.</span>
                {event}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Root cause (failures only) */}
      {data.root_cause && (
        <div className="rounded-xl bg-red-500/5 border border-red-500/10 p-3">
          <p className="text-[10px] uppercase tracking-[0.2em] text-red-400/60 mb-1">Probable Root Cause</p>
          <p className="text-sm text-red-300/90">{data.root_cause}</p>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/40 mb-2">Recommendations</p>
          <ul className="space-y-1">
            {data.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-accent-300/80">
                <Info className="h-3 w-3 mt-0.5 flex-shrink-0 text-accent-400/50" />
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
