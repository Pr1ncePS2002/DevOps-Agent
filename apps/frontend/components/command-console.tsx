"use client";

import { useCallback, useEffect, useMemo, useState, useTransition } from "react";
import { Check, Loader2, Send, Sparkles } from "lucide-react";

import { approvePlan, fetchExecution, parseCommand } from "@/lib/api";
import { POLL_INTERVAL_MS } from "@/lib/config";
import type { ExecutionDetail, PlanPreview, Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { LiveLog } from "./live-log";
import { StatusPill } from "./status-pill";

interface CommandConsoleProps {
  projects: Project[];
}

export function CommandConsole({ projects }: CommandConsoleProps) {
  const [selectedProject, setSelectedProject] = useState(() => projects.at(0)?.id ?? 0);
  const [commandText, setCommandText] = useState("Deploy the api service to staging and smoke test afterwards");
  const [planPreview, setPlanPreview] = useState<PlanPreview | null>(null);
  const [execution, setExecution] = useState<ExecutionDetail | null>(null);
  const [pollingId, setPollingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (selectedProject === 0 && projects.length > 0) {
      setSelectedProject(projects[0].id);
    }
  }, [projects, selectedProject]);

  useEffect(() => {
    if (!pollingId) {
      setIsPolling(false);
      return;
    }

    setIsPolling(true);
    let isCancelled = false;

    const poll = async () => {
      try {
        const data = await fetchExecution(pollingId);
        if (!isCancelled) {
          setExecution(data);
          if (["failed", "succeeded", "rolled_back"].includes(data.status)) {
            setIsPolling(false);
            setPollingId(null);
          }
        }
      } catch (pollError) {
        if (!isCancelled) {
          setError(pollError instanceof Error ? pollError.message : "Unable to fetch execution");
          setIsPolling(false);
        }
      }
    };

    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      isCancelled = true;
      clearInterval(id);
    };
  }, [pollingId]);

  const handleParse = useCallback(() => {
    if (!selectedProject || !commandText.trim()) {
      setError("Select a project and describe what you want to run.");
      return;
    }

    setError(null);

    startTransition(async () => {
      try {
        const plan = await parseCommand({ project_id: selectedProject, text: commandText.trim() });
        setPlanPreview(plan);
        setExecution(null);
        setPollingId(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to parse command");
      }
    });
  }, [commandText, selectedProject]);

  const handleApprove = useCallback(async () => {
    if (!planPreview) return;
    setError(null);

    try {
      const approval = await approvePlan(planPreview.plan_id);
      setPollingId(approval.execution_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to approve plan");
    }
  }, [planPreview]);

  const logLines = useMemo(() => (execution?.logs ? execution.logs.trim().split("\n") : []), [execution?.logs]);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">Command Briefing</p>
          {planPreview ? <StatusPill status={planPreview.status} /> : null}
        </div>
        <textarea
          value={commandText}
          onChange={(event) => setCommandText(event.target.value)}
          rows={6}
          className="mt-4 w-full rounded-2xl border border-white/10 bg-black/30 p-4 font-mono text-sm text-white/90 focus:border-accent-500 focus:outline-none"
        />
        <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center">
          <select
            value={selectedProject}
            onChange={(event) => setSelectedProject(Number(event.target.value))}
            className="w-full rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white/90 focus:border-accent-400"
            disabled={projects.length === 0}
          >
            {projects.map((project) => (
              <option key={project.id} value={project.id} className="bg-surface-900 text-white">
                {project.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleParse}
            className={cn(
              "flex w-full items-center justify-center gap-2 rounded-2xl bg-accent-500/80 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-surface-900 transition hover:bg-accent-500",
              (isPending || projects.length === 0) && "opacity-40"
            )}
            disabled={isPending || projects.length === 0}
          >
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />} Generate Plan
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
        <p className="mt-4 flex items-center gap-1.5 text-xs text-white/25">
          <Sparkles className="h-3 w-3" />
          Powered by Gemini 2.0 Flash
        </p>
      </div>

      <div className="rounded-3xl border border-white/5 bg-surface-800/80 p-6 shadow-card">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">Preview</p>
        {planPreview ? (
          <div className="mt-4 space-y-4">
            {/* Action title + confidence badge */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-2xl font-display font-semibold capitalize text-white">
                  {planPreview.action}
                </p>
                <p className="text-sm text-white/70">
                  Version target: {planPreview.version || "Not specified"}
                </p>
              </div>
              {planPreview.confidence !== undefined && (
                <ConfidenceBadge confidence={planPreview.confidence} />
              )}
            </div>

            {/* AI reasoning */}
            {planPreview.reasoning ? (
              <p className="text-sm italic text-white/60">
                AI understood: {planPreview.reasoning}
              </p>
            ) : null}

            {/* Environments + Post Steps */}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                <p className="text-xs uppercase tracking-[0.25em] text-white/60">Environments</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-white/90">
                  {planPreview.environments.map((env) => (
                    <li key={env}>{env}</li>
                  ))}
                </ul>
              </div>
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                <p className="text-xs uppercase tracking-[0.25em] text-white/60">Post Steps</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-white/80">
                  {planPreview.post_steps.length > 0 ? (
                    planPreview.post_steps.map((step, idx) => (
                      <li key={`${step}-${idx}`}>{step.replace(/_/g, " ")}</li>
                    ))
                  ) : (
                    <li className="text-white/40">None</li>
                  )}
                </ul>
              </div>
            </div>

            {/* Risk score bar */}
            {planPreview.risk_score !== undefined && planPreview.risk_level ? (
              <RiskBar score={planPreview.risk_score} level={planPreview.risk_level} />
            ) : null}

            {/* Policy warnings */}
            {planPreview.warnings.length > 0 ? (
              <div className="rounded-2xl border border-yellow-500/40 bg-yellow-500/5 p-4 text-sm text-yellow-100">
                <p className="text-xs uppercase tracking-[0.3em] text-yellow-300">Policy Warnings</p>
                <ul className="mt-2 list-disc space-y-1 pl-4">
                  {planPreview.warnings.map((warning, idx) => (
                    <li key={`${warning}-${idx}`}>{warning}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {/* Recommendations */}
            {planPreview.recommendations && planPreview.recommendations.length > 0 ? (
              <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-4 text-sm text-emerald-100">
                <p className="text-xs uppercase tracking-[0.3em] text-emerald-400">Recommendations</p>
                <ul className="mt-2 list-disc space-y-1 pl-4">
                  {planPreview.recommendations.map((rec, idx) => (
                    <li key={`${rec}-${idx}`}>{rec}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {/* Deployment details */}
            {(planPreview.detected_stack || planPreview.image_tag || planPreview.dockerfile_path || (planPreview.ports && planPreview.ports.length > 0)) ? (
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4 text-sm">
                <p className="text-xs uppercase tracking-[0.25em] text-white/60">Deployment Details</p>
                <dl className="mt-2 space-y-1.5">
                  {planPreview.detected_stack && (
                    <div className="flex justify-between gap-2">
                      <dt className="text-white/50">Stack</dt>
                      <dd className="font-mono text-white/90">{planPreview.detected_stack}</dd>
                    </div>
                  )}
                  {planPreview.image_tag && (
                    <div className="flex justify-between gap-2">
                      <dt className="text-white/50">Image</dt>
                      <dd className="font-mono text-white/90">{planPreview.image_tag}</dd>
                    </div>
                  )}
                  {planPreview.dockerfile_path && (
                    <div className="flex justify-between gap-2">
                      <dt className="text-white/50">Dockerfile</dt>
                      <dd className="truncate font-mono text-white/90">{planPreview.dockerfile_path}</dd>
                    </div>
                  )}
                  {planPreview.ports && planPreview.ports.length > 0 && (
                    <div className="flex justify-between gap-2">
                      <dt className="text-white/50">Ports</dt>
                      <dd className="font-mono text-white/90">{planPreview.ports.join(", ")}</dd>
                    </div>
                  )}
                  {planPreview.env_injected !== undefined && (
                    <div className="flex justify-between gap-2">
                      <dt className="text-white/50">Env vars</dt>
                      <dd className={planPreview.env_injected ? "text-emerald-300" : "text-white/40"}>
                        {planPreview.env_injected ? "Injected" : "None"}
                      </dd>
                    </div>
                  )}
                </dl>
              </div>
            ) : null}

            {/* Suggested confirmation above approve */}
            {planPreview.suggested_confirmation ? (
              <p className="text-center text-xs text-white/50">
                {planPreview.suggested_confirmation}
              </p>
            ) : null}

            <button
              type="button"
              onClick={handleApprove}
              disabled={!planPreview || isPolling}
              className={cn(
                "flex w-full items-center justify-center gap-2 rounded-2xl border border-accent-400/50 bg-transparent px-4 py-3 text-sm font-semibold uppercase tracking-wide text-accent-300 transition",
                (!planPreview || isPolling) && "opacity-40"
              )}
            >
              {isPolling ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Approve & Execute
            </button>
          </div>
        ) : (
          <div className="mt-6 rounded-2xl border border-dashed border-white/10 p-6 text-sm text-white/70">
            Generate a plan to see the AI breakdown.
          </div>
        )}
      </div>

      <div className="lg:col-span-2">
        <LiveLog lines={logLines} title={execution ? `Execution #${execution.id} (${execution.status})` : undefined} />
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    pct > 80
      ? "border-emerald-400/50 bg-emerald-500/15 text-emerald-300"
      : pct >= 50
        ? "border-yellow-400/50 bg-yellow-500/15 text-yellow-200"
        : "border-red-400/40 bg-red-500/10 text-red-300";

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center rounded-full border px-2.5 py-1 text-xs font-medium",
        color
      )}
    >
      AI {pct}% confident
    </span>
  );
}

const RISK_CONFIG = {
  low: { bar: "bg-emerald-500", text: "text-emerald-300", label: "LOW" },
  medium: { bar: "bg-yellow-500", text: "text-yellow-300", label: "MEDIUM" },
  high: { bar: "bg-orange-500", text: "text-orange-300", label: "HIGH" },
  critical: { bar: "bg-red-500", text: "text-red-400", label: "CRITICAL" },
} as const;

function RiskBar({ score, level }: { score: number; level: "low" | "medium" | "high" | "critical" }) {
  const cfg = RISK_CONFIG[level] ?? RISK_CONFIG.low;
  return (
    <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.25em] text-white/60">Risk Assessment</p>
        <span className={cn("text-xs font-semibold uppercase", cfg.text)}>
          {cfg.label} — {score}/100
        </span>
      </div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className={cn("h-full rounded-full transition-all duration-500", cfg.bar)}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
