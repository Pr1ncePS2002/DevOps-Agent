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
  source_type?: string;
  repo_path?: string | null;
  repo_url?: string | null;
  workspace_path?: string | null;
  detected_stack?: string | null;
  dockerfile_path?: string | null;
  has_env_file?: boolean;
  last_known_good_tag?: string | null;
}

export interface PlanPreview {
  plan_id: number;
  action: string;
  version?: string | null;
  environments: string[];
  post_steps: string[];
  warnings: string[];
  status: PlanStatus;
  project_id?: number;
  repo_path?: string | null;
  detected_stack?: string | null;
  dockerfile_path?: string | null;
  image_tag?: string | null;
  ports?: string[];
  env_injected?: boolean;
}

export interface ExecutionDetail {
  id: number;
  plan_id: number;
  status: ExecutionStatus | PlanStatus;
  logs: string;
}
