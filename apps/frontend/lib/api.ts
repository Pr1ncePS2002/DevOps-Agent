import { API_BASE_URL } from "./config";
import type {
  AnalyticsSummary,
  ChatMessage,
  ChatResponse,
  ChatSession,
  ExecutionDetail,
  PlanPreview,
  Project,
  ProjectRegistrationPayload,
  ProjectRegistrationResult,
  VercelConnectResponse,
  RenderConnectResponse,
  DeployStatusResponse,
} from "./types";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail: string;
    const ct = res.headers.get("content-type") ?? "";
    if (ct.includes("application/json")) {
      const json = await res.json();
      detail = json.detail ?? json.message ?? JSON.stringify(json);
    } else {
      detail = (await res.text()) || res.statusText;
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ── Projects ──────────────────────────────────────────────────────────────────

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE_URL}/projects`, { cache: "no-store" });
  if (res.status === 404) return [];
  return handleResponse<Project[]>(res);
}

/**
 * DEPRECATED — use registerProjectV2 instead.
 */
export async function createProject(payload: {
  name: string;
  repo_path?: string | null;
  repo_url?: string | null;
}): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<Project>(res);
}

/**
 * Unified project registration — new single entry point.
 */
export async function registerProjectV2(
  payload: ProjectRegistrationPayload
): Promise<ProjectRegistrationResult> {
  const res = await fetch(`${API_BASE_URL}/projects/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<ProjectRegistrationResult>(res);
}

/**
 * @deprecated Use registerProjectV2 instead.
 */
export async function registerProject(payload: {
  source_type: "local" | "github";
  path_or_url: string;
}): Promise<{
  project_id: number;
  name: string;
  workspace_path: string;
  detected_stack: string;
  dockerfile_path: string | null;
  dockerfile_generated: boolean;
}> {
  const newPayload: ProjectRegistrationPayload = {
    projectName: payload.path_or_url.split("/").pop() ?? "project",
    description: "",
    source: {
      type: payload.source_type,
      config:
        payload.source_type === "local"
          ? { path: payload.path_or_url }
          : { repoUrl: payload.path_or_url, branch: "main" },
    },
    deployment: { platform: "docker", config: {} },
    env: {},
  };
  const res = await fetch(`${API_BASE_URL}/projects/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(newPayload),
  });
  const result = await handleResponse<ProjectRegistrationResult>(res);
  return {
    project_id: result.projectId,
    name: result.name,
    workspace_path: result.workspacePath,
    detected_stack: result.detectedStack,
    dockerfile_path: result.dockerfilePath,
    dockerfile_generated: result.dockerfileGenerated,
  };
}

// ── Env upload ────────────────────────────────────────────────────────────────

export async function uploadEnv(projectId: number, file: File): Promise<{ status: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/env`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(res);
}

// ── Commands & executions ─────────────────────────────────────────────────────

export async function rollbackExecution(executionId: number): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE_URL}/executions/${executionId}/rollback`, { method: "POST" });
  return handleResponse(res);
}

export async function parseCommand(payload: { project_id: number; text: string }): Promise<PlanPreview> {
  const res = await fetch(`${API_BASE_URL}/commands/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<PlanPreview>(res);
}

export async function approvePlan(planId: number): Promise<{ execution_id: number; rq_job_id: string }> {
  const res = await fetch(`${API_BASE_URL}/executions/approve/${planId}`, { method: "POST" });
  return handleResponse(res);
}

export async function fetchExecution(executionId: number): Promise<ExecutionDetail> {
  const res = await fetch(`${API_BASE_URL}/executions/${executionId}`, { cache: "no-store" });
  return handleResponse(res);
}

// ── Provider connect (Phase 3a) ──────────────────────────────────────────────

export async function connectVercel(token: string): Promise<VercelConnectResponse> {
  const res = await fetch(`${API_BASE_URL}/providers/vercel/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  return handleResponse<VercelConnectResponse>(res);
}

export async function connectRender(apiKey: string): Promise<RenderConnectResponse> {
  const res = await fetch(`${API_BASE_URL}/providers/render/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey }),
  });
  return handleResponse<RenderConnectResponse>(res);
}

// ── Demo mode (Phase 3d) ─────────────────────────────────────────────────────

export interface DemoPreset {
  name: string;
  description: string;
  source_type: string;
  deployment_platform: string;
  detected_stack: string;
}

export interface DemoSetupResult {
  project_id: number;
  name: string;
  detected_stack: string;
  deployment_platform: string;
  has_env_file: boolean;
  message: string;
}

export async function fetchDemoPresets(): Promise<{ presets: DemoPreset[] }> {
  const res = await fetch(`${API_BASE_URL}/demo/presets`, { cache: "no-store" });
  return handleResponse(res);
}

export async function setupDemoProject(presetIndex: number): Promise<DemoSetupResult> {
  const res = await fetch(`${API_BASE_URL}/demo/setup/${presetIndex}`, { method: "POST" });
  return handleResponse<DemoSetupResult>(res);
}

// ── Deploy status polling (Phase 3c) ─────────────────────────────────────────

export async function fetchDeployStatus(
  provider: string,
  deploymentId: string
): Promise<DeployStatusResponse> {
  const res = await fetch(
    `${API_BASE_URL}/deploy/status/${encodeURIComponent(provider)}/${encodeURIComponent(deploymentId)}`,
    { cache: "no-store" }
  );
  return handleResponse<DeployStatusResponse>(res);
}

// ── Chat / Conversation (Phase 2) ────────────────────────────────────────────

export async function createChatSession(projectId: number): Promise<ChatSession> {
  const res = await fetch(`${API_BASE_URL}/chat/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId }),
  });
  return handleResponse<ChatSession>(res);
}

export async function listChatSessions(projectId: number): Promise<ChatSession[]> {
  const res = await fetch(`${API_BASE_URL}/chat/sessions?project_id=${projectId}`, {
    cache: "no-store",
  });
  return handleResponse<ChatSession[]>(res);
}

export async function getChatMessages(sessionId: number): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`, {
    cache: "no-store",
  });
  return handleResponse<ChatMessage[]>(res);
}

export async function sendChatMessage(
  sessionId: number,
  content: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  return handleResponse<ChatResponse>(res);
}

// ── Analytics (Task 5.2) ────────────────────────────────────────────────────

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  const res = await fetch(`${API_BASE_URL}/analytics/summary`, { cache: "no-store" });
  return handleResponse<AnalyticsSummary>(res);
}
