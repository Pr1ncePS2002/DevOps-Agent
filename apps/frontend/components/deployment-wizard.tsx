"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronRight, ExternalLink, Loader2, Upload } from "lucide-react";

import {
  approvePlan,
  fetchDeployStatus,
  fetchExecution,
  fetchProjects,
  parseCommand,
  rollbackExecution,
  uploadEnv
} from "@/lib/api";
import { POLL_INTERVAL_MS } from "@/lib/config";
import type { DeployStatusResponse, ExecutionDetail, PlanPreview, Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { LiveLog } from "./live-log";
import { StatusPill } from "./status-pill";
import { ProjectRegistration } from "./project-registration";
import { DemoButton } from "./demo-button";

const STEPS = ["Add Project", "Upload .env", "Review Plan", "Deploy", "Logs & Status"];

const DEPLOY_STATUS_POLL_MS = 5000;

const DEPLOY_STATUS_COLORS: Record<string, string> = {
  queued: "text-purple-300",
  building: "text-sky-300",
  deploying: "text-yellow-300",
  live: "text-green-400",
  failed: "text-red-400",
};

export function DeploymentWizard() {
  const [step, setStep] = useState(1);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [envFile, setEnvFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [planPreview, setPlanPreview] = useState<PlanPreview | null>(null);
  const [execution, setExecution] = useState<ExecutionDetail | null>(null);
  const [pollingId, setPollingId] = useState<number | null>(null);
  const [commandText, setCommandText] = useState("Deploy to staging");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Cloud deploy status polling (Phase 3c)
  const [cloudStatus, setCloudStatus] = useState<DeployStatusResponse | null>(null);
  const [cloudPolling, setCloudPolling] = useState<{ provider: string; deploymentId: string } | null>(null);

  const loadProjects = useCallback(async (): Promise<Project[]> => {
    try {
      const list = await fetchProjects();
      setProjects(list);
      if (list.length > 0 && !selectedProject) {
        setSelectedProject(list[0]);
      }
      return list;
    } catch {
      setProjects([]);
      return [];
    }
  }, [selectedProject]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleRegistered = useCallback(async () => {
    const list = await loadProjects();
    if (list.length > 0) {
      setSelectedProject(list[0]);
    }
    setStep(2);
  }, [loadProjects]);

  const handleUploadEnv = useCallback(async () => {
    const file = envFile ?? fileInputRef.current?.files?.[0];
    if (!file || !selectedProject) return;
    setError(null);
    setUploading(true);
    try {
      await uploadEnv(selectedProject.id, file);
      await loadProjects();
      setSelectedProject((p) => (p ? { ...p, has_env_file: true } : null));
      setStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [envFile, selectedProject, loadProjects]);

  const handleParse = useCallback(async () => {
    if (!selectedProject || !commandText.trim()) return;
    setError(null);
    try {
      const plan = await parseCommand({
        project_id: selectedProject.id,
        text: commandText.trim()
      });
      setPlanPreview(plan);
      setStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Parse failed");
    }
  }, [selectedProject, commandText]);

  const handleApprove = useCallback(async () => {
    if (!planPreview) return;
    setError(null);
    try {
      const approval = await approvePlan(planPreview.plan_id);
      setPollingId(approval.execution_id);
      setStep(5);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approve failed");
    }
  }, [planPreview]);

  const handleRollback = useCallback(async () => {
    if (!execution) return;
    setError(null);
    try {
      await rollbackExecution(execution.id);
      setPollingId(execution.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rollback failed");
    }
  }, [execution]);

  // Execution polling
  useEffect(() => {
    if (!pollingId) return;
    const poll = async () => {
      try {
        const data = await fetchExecution(pollingId);
        setExecution(data);
        if (["failed", "succeeded", "rolled_back"].includes(data.status)) {
          setPollingId(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch execution status");
        setPollingId(null);
      }
    };
    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [pollingId]);

  // Cloud deploy status polling (Phase 3c)
  useEffect(() => {
    if (!cloudPolling) return;
    const poll = async () => {
      try {
        const status = await fetchDeployStatus(cloudPolling.provider, cloudPolling.deploymentId);
        setCloudStatus(status);
        if (status.is_terminal) {
          setCloudPolling(null);
        }
      } catch {
        setCloudPolling(null);
      }
    };
    poll();
    const id = setInterval(poll, DEPLOY_STATUS_POLL_MS);
    return () => clearInterval(id);
  }, [cloudPolling]);

  const logLines = useMemo(
    () => (execution?.logs ? execution.logs.trim().split("\n") : []),
    [execution?.logs]
  );

  const canRollback =
    execution &&
    ["failed", "succeeded"].includes(execution.status) &&
    selectedProject?.last_known_good_tag;

  const isCloudDeploy = selectedProject?.deployment_platform === "vercel" || selectedProject?.deployment_platform === "render";

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap gap-2">
        {STEPS.map((label, i) => (
          <button
            key={label}
            type="button"
            onClick={() => setStep(i + 1)}
            className={cn(
              "flex items-center gap-1 rounded-xl px-3 py-1.5 text-sm font-medium transition",
              step >= i + 1
                ? "bg-accent-500/20 text-accent-300"
                : "bg-white/5 text-white/50"
            )}
          >
            {step > i + 1 ? <Check className="h-4 w-4" /> : null}
            {label}
            {i < STEPS.length - 1 && <ChevronRight className="h-4 w-4" />}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Step 1: Add Project */}
      {step === 1 && (
        <div className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
          <h3 className="text-lg font-semibold text-white">Add Project</h3>
          <p className="mt-1 mb-5 text-sm text-white/60">
            Configure source, deployment platform, and environment variables.
          </p>
          <ProjectRegistration onSuccess={handleRegistered} />
          <div className="mt-6 border-t border-white/5 pt-6">
            <DemoButton onDemoStarted={(executionId) => {
              loadProjects();
              setPollingId(executionId);
              setStep(5);
            }} />
          </div>
        </div>
      )}

      {/* Step 2: Upload .env */}
      {step === 2 && (
        <div className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
          <h3 className="text-lg font-semibold text-white">Upload .env</h3>
          <p className="mt-1 text-sm text-white/60">
            Upload environment file for deployment.
          </p>
          {projects.length > 1 && (
            <select
              value={selectedProject?.id}
              onChange={(e) => setSelectedProject(projects.find((p) => p.id === Number(e.target.value)) ?? null)}
              className="mt-2 w-full max-w-md rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}
          <div className="mt-4 flex flex-col gap-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".env,.env.local,.env.production,.env.staging"
              onChange={(e) => setEnvFile(e.target.files?.[0] ?? null)}
              className="rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white/90 file:mr-4 file:rounded-lg file:border-0 file:bg-accent-500 file:px-4 file:py-2 file:text-surface-900"
            />
            <button
              type="button"
              onClick={handleUploadEnv}
              disabled={uploading || !envFile}
              className="flex w-full max-w-xs items-center justify-center gap-2 rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 disabled:opacity-50"
            >
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              Upload .env
            </button>
            {selectedProject?.has_env_file && (
              <>
                <p className="text-sm text-green-400">✓ Env file already uploaded</p>
                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="flex w-full max-w-xs items-center justify-center gap-2 rounded-2xl border border-accent-400/50 px-4 py-3 text-sm font-semibold text-accent-300"
                >
                  Continue to Review Plan
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Step 3: Review Plan */}
      {step === 3 && (
        <div className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
          <h3 className="text-lg font-semibold text-white">Review Plan</h3>
          <p className="mt-1 text-sm text-white/60">
            Enter deployment command and generate plan
          </p>
          <div className="mt-4 flex flex-col gap-4">
            <select
              value={selectedProject?.id}
              onChange={(e) => setSelectedProject(projects.find((p) => p.id === Number(e.target.value)) ?? null)}
              className="w-full max-w-md rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.detected_stack ?? "?"})
                </option>
              ))}
            </select>
            <textarea
              value={commandText}
              onChange={(e) => setCommandText(e.target.value)}
              rows={3}
              placeholder="Deploy to staging"
              className="w-full rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white placeholder:text-white/40"
            />
            <button
              type="button"
              onClick={handleParse}
              className="flex w-full max-w-xs items-center justify-center gap-2 rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900"
            >
              Generate Plan
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Deploy */}
      {step === 4 && planPreview && (
        <div className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
          <h3 className="text-lg font-semibold text-white">Deploy</h3>
          <div className="mt-4 space-y-4">
            {/* Action + confidence + status */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-2xl font-semibold capitalize text-white">{planPreview.action}</p>
                <p className="text-sm text-white/60">
                  Version: {planPreview.version ?? "Not specified"}
                </p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <StatusPill status={planPreview.status} />
                {planPreview.confidence !== undefined && (
                  <span className={cn(
                    "rounded-full border px-2.5 py-1 text-xs font-medium",
                    planPreview.confidence > 0.8
                      ? "border-emerald-400/50 bg-emerald-500/15 text-emerald-300"
                      : "border-yellow-400/50 bg-yellow-500/15 text-yellow-200"
                  )}>
                    AI {Math.round(planPreview.confidence * 100)}% confident
                  </span>
                )}
              </div>
            </div>

            {/* AI reasoning */}
            {planPreview.reasoning && (
              <p className="text-sm italic text-white/50">AI understood: {planPreview.reasoning}</p>
            )}

            {/* Environments + Post steps */}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                <p className="text-xs uppercase tracking-widest text-white/50">Environments</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-white/90">
                  {planPreview.environments.map((env) => <li key={env}>{env}</li>)}
                </ul>
              </div>
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                <p className="text-xs uppercase tracking-widest text-white/50">Post Steps</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-white/80">
                  {planPreview.post_steps.length > 0
                    ? planPreview.post_steps.map((s, i) => <li key={i}>{s.replace(/_/g, " ")}</li>)
                    : <li className="text-white/40">None</li>}
                </ul>
              </div>
            </div>

            {/* Deployment details */}
            <div className="rounded-2xl border border-white/5 bg-black/30 p-4 text-sm">
              <p className="text-xs uppercase tracking-widest text-white/50">Deployment Details</p>
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
                <div className="flex justify-between gap-2">
                  <dt className="text-white/50">Env vars</dt>
                  <dd className={planPreview.env_injected ? "text-emerald-300" : "text-white/40"}>
                    {planPreview.env_injected ? "Injected" : "None"}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Risk bar */}
            {planPreview.risk_score !== undefined && planPreview.risk_level && (
              <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-widest text-white/50">Risk Assessment</p>
                  <span className={cn("text-xs font-semibold uppercase", {
                    "text-emerald-300": planPreview.risk_level === "low",
                    "text-yellow-300": planPreview.risk_level === "medium",
                    "text-orange-300": planPreview.risk_level === "high",
                    "text-red-400": planPreview.risk_level === "critical",
                  })}>
                    {planPreview.risk_level.toUpperCase()} — {planPreview.risk_score}/100
                  </span>
                </div>
                <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-white/10">
                  <div
                    className={cn("h-full rounded-full transition-all duration-500", {
                      "bg-emerald-500": planPreview.risk_level === "low",
                      "bg-yellow-500": planPreview.risk_level === "medium",
                      "bg-orange-500": planPreview.risk_level === "high",
                      "bg-red-500": planPreview.risk_level === "critical",
                    })}
                    style={{ width: `${planPreview.risk_score}%` }}
                  />
                </div>
              </div>
            )}

            {/* Warnings */}
            {planPreview.warnings.length > 0 && (
              <div className="rounded-2xl border border-yellow-500/40 bg-yellow-500/5 p-4">
                <p className="text-xs uppercase tracking-widest text-yellow-300">Policy Warnings</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-yellow-100">
                  {planPreview.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}

            {/* Recommendations */}
            {planPreview.recommendations && planPreview.recommendations.length > 0 && (
              <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-4">
                <p className="text-xs uppercase tracking-widest text-emerald-400">Recommendations</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-emerald-100">
                  {planPreview.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}

            {planPreview.suggested_confirmation && (
              <p className="text-center text-xs text-white/40">{planPreview.suggested_confirmation}</p>
            )}

            <button
              type="button"
              onClick={handleApprove}
              className="flex w-full items-center justify-center gap-2 rounded-2xl border border-accent-400/50 bg-accent-500/20 px-4 py-3 text-sm font-semibold text-accent-300 transition hover:bg-accent-500/30"
            >
              <Check className="h-4 w-4" /> Approve & Execute
            </button>
          </div>
        </div>
      )}

      {/* Step 5: Logs & Status */}
      {step === 5 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">
              Logs & Status
              {execution && ` — ${execution.status}`}
            </h3>
            {canRollback && (
              <button
                type="button"
                onClick={handleRollback}
                className="rounded-xl border border-amber-500/50 bg-amber-500/20 px-4 py-2 text-sm font-medium text-amber-200"
              >
                Rollback
              </button>
            )}
          </div>

          {/* Cloud deploy status (Phase 3c) */}
          {isCloudDeploy && cloudStatus && (
            <div className="rounded-2xl border border-white/10 bg-surface-800/70 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={cn("text-sm font-semibold uppercase", DEPLOY_STATUS_COLORS[cloudStatus.status] ?? "text-white/60")}>
                    {cloudStatus.status}
                  </span>
                  {!cloudStatus.is_terminal && (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-white/40" />
                  )}
                </div>
                <span className="text-xs text-white/40">{cloudStatus.provider}</span>
              </div>
              <p className="text-xs text-white/50">{cloudStatus.message}</p>
              {cloudStatus.url && cloudStatus.status === "live" && (
                <a
                  href={cloudStatus.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-sm font-medium text-green-400 hover:text-green-300"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open live app →
                </a>
              )}
            </div>
          )}

          <LiveLog
            lines={logLines}
            title={execution ? `Execution #${execution.id}` : undefined}
          />
        </div>
      )}
    </div>
  );
}
