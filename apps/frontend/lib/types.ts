export type PlanStatus =
  | "pending_approval"
  | "approved"
  | "running"
  | "failed"
  | "rolled_back"
  | "succeeded";

export type ExecutionStatus = "queued" | "running" | "failed" | "succeeded" | "rolled_back";

export interface Project {
  id: number;
  name: string;
  repo_path?: string | null;
  repo_url?: string | null;
}

export interface PlanPreview {
  plan_id: number;
  action: string;
  version?: string | null;
  environments: string[];
  post_steps: string[];
  warnings: string[];
  status: PlanStatus;
}

export interface ExecutionDetail {
  id: number;
  plan_id: number;
  status: ExecutionStatus | PlanStatus;
  logs: string;
}
