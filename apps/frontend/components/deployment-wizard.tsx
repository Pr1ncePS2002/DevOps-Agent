"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, ChevronRight, Loader2, Upload } from "lucide-react";

import {
  approvePlan,
  fetchExecution,
  fetchProjects,
  parseCommand,
  registerProject,
  rollbackExecution,
  uploadEnv
} from "@/lib/api";
import { POLL_INTERVAL_MS } from "@/lib/config";
import type { ExecutionDetail, PlanPreview, Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { LiveLog } from "./live-log";
import { StatusPill } from "./status-pill";

const STEPS = ["Add Project", "Upload .env", "Review Plan", "Deploy", "Logs & Status"];

export function DeploymentWizard() {
  const [step, setStep] = useState(1);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [registerSource, setRegisterSource] = useState<"local" | "github">("local");
  const [registerPath, setRegisterPath] = useState("");
  const [registering, setRegistering] = useState(false);
  const [envFile, setEnvFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [planPreview, setPlanPreview] = useState<PlanPreview | null>(null);
  const [execution, setExecution] = useState<ExecutionDetail | null>(null);
  const [pollingId, setPollingId] = useState<number | null>(null);
  const [commandText, setCommandText] = useState("Deploy to staging");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleRegister = useCallback(async () => {
    if (!registerPath.trim()) {
      setError("Enter path or GitHub URL");
      return;
    }
    setError(null);
    setRegistering(true);
    try {
      const result = await registerProject({
        source_type: registerSource,
        path_or_url: registerPath.trim()
      });
      const list = await loadProjects();
      const proj = list.find((p) => p.id === result.project_id) ?? {
        id: result.project_id,
        name: result.name,
        workspace_path: result.workspace_path,
        detected_stack: result.detected_stack,
        dockerfile_path: result.dockerfile_path,
        has_env_file: false
      } as Project;
      setSelectedProject(proj);
      setStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setRegistering(false);
    }
  }, [registerPath, registerSource, loadProjects, projects]);

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

  useEffect(() => {
    if (!pollingId) return;
    const poll = async () => {
      try {
        const data = await fetchExecution(pollingId);
        setExecution(data);
        if (["failed", "succeeded", "rolled_back"].includes(data.status)) {
          setPollingId(null);
        }
      } catch {
        setPollingId(null);
      }
    };
    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [pollingId]);

  const logLines = useMemo(
    () => (execution?.logs ? execution.logs.trim().split("\n") : []),
    [execution?.logs]
  );

  const canRollback =
    execution &&
    ["failed", "succeeded"].includes(execution.status) &&
    selectedProject?.last_known_good_tag;

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
          <p className="mt-1 text-sm text-white/60">
            Provide a local path or GitHub repository URL
          </p>
          <div className="mt-4 flex flex-col gap-4">
            <select
              value={registerSource}
              onChange={(e) => setRegisterSource(e.target.value as "local" | "github")}
              className="w-full max-w-xs rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white"
            >
              <option value="local">Local path</option>
              <option value="github">GitHub URL</option>
            </select>
            <input
              type="text"
              value={registerPath}
              onChange={(e) => setRegisterPath(e.target.value)}
              placeholder={
                registerSource === "local"
                  ? "C:/projects/my-app"
                  : "https://github.com/user/repo"
              }
              className="w-full rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white placeholder:text-white/40"
            />
            <button
              type="button"
              onClick={handleRegister}
              disabled={registering}
              className="flex w-full max-w-xs items-center justify-center gap-2 rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 disabled:opacity-50"
            >
              {registering ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
              Register Project
            </button>
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
              accept=".env"
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
            <div className="flex items-center justify-between">
              <span className="text-white/80">{planPreview.action}</span>
              <StatusPill status={planPreview.status} />
            </div>
            <p className="text-sm text-white/60">
              Stack: {planPreview.detected_stack} | Dockerfile: {planPreview.dockerfile_path ?? "generated"}
            </p>
            {planPreview.warnings.length > 0 && (
              <ul className="list-disc space-y-1 rounded-xl border border-yellow-500/30 bg-yellow-500/5 p-4 text-sm text-yellow-200">
                {planPreview.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            )}
            <button
              type="button"
              onClick={handleApprove}
              className="flex w-full items-center justify-center gap-2 rounded-2xl border border-accent-400/50 bg-accent-500/20 px-4 py-3 text-sm font-semibold text-accent-300"
            >
              Approve & Execute
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
          <LiveLog
            lines={logLines}
            title={execution ? `Execution #${execution.id}` : undefined}
          />
        </div>
      )}
    </div>
  );
}
