import { API_BASE_URL } from "./config";
import type { ExecutionDetail, PlanPreview, Project } from "./types";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }

  return res.json() as Promise<T>;
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE_URL}/projects`, { cache: "no-store" });
  if (res.status === 404) {
    return [];
  }
  return handleResponse<Project[]>(res);
}

export async function createProject(payload: {
  name: string;
  repo_path?: string | null;
  repo_url?: string | null;
}): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return handleResponse<Project>(res);
}

export async function parseCommand(payload: { project_id: number; text: string }): Promise<PlanPreview> {
  const res = await fetch(`${API_BASE_URL}/commands/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
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
