// ── Deployment status types ───────────────────────────────────────────────────

export type PlanStatus =
  | "pending_approval"
  | "approved"
  | "running"
  | "failed"
  | "rolled_back"
  | "succeeded";

export type ExecutionStatus = "queued" | "running" | "failed" | "succeeded" | "rolled_back";

// ── Project ───────────────────────────────────────────────────────────────────

export interface Project {
  id: number;
  name: string;
  description?: string;
  source_type?: string;
  repo_path?: string | null;
  repo_url?: string | null;
  branch?: string | null;
  workspace_path?: string | null;
  detected_stack?: string | null;
  dockerfile_path?: string | null;
  has_env_file?: boolean;
  last_known_good_tag?: string | null;
  deployment_platform?: string;
}

// ── Project Registration ──────────────────────────────────────────────────────

export type SourceType = "local" | "github";
export type DeploymentPlatform = "local" | "docker" | "vercel" | "render";

export interface ProjectRegistrationPayload {
  projectName: string;
  description: string;
  source: {
    type: SourceType;
    config: Record<string, string>;
  };
  deployment: {
    platform: DeploymentPlatform;
    config: Record<string, string>;
  };
  env: Record<string, string>;
}

export interface ProjectRegistrationResult {
  projectId: number;
  name: string;
  workspacePath: string;
  detectedStack: string;
  dockerfilePath: string | null;
  dockerfileGenerated: boolean;
  deploymentPlatform: DeploymentPlatform;
  envWarnings?: string[];
}

// ── Plans & Executions ────────────────────────────────────────────────────────

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

// ── Provider Connect (Phase 3a) ──────────────────────────────────────────────

export interface VercelProject {
  id: string;
  name: string;
  framework?: string | null;
  updated_at?: number | null;
}

export interface VercelConnectResponse {
  user: string;
  team_id: string | null;
  projects: VercelProject[];
}

export interface RenderService {
  id: string;
  name: string;
  type: string;
  url?: string | null;
}

export interface RenderConnectResponse {
  services: RenderService[];
}

// ── Deploy Status Polling (Phase 3c) ─────────────────────────────────────────

export type DeployNormalisedStatus = "queued" | "building" | "deploying" | "live" | "failed";

export interface DeployStatusResponse {
  provider: string;
  deployment_id: string;
  status: DeployNormalisedStatus;
  message: string;
  url: string | null;
  is_terminal: boolean;
}
