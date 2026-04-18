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
  // AI interpretation metadata (Task 1.2)
  confidence?: number;
  reasoning?: string;
  suggested_confirmation?: string;
  interpretation_method?: string;
  // AI risk assessment metadata (Task 1.3)
  risk_level?: "low" | "medium" | "high" | "critical";
  risk_score?: number;
  recommendations?: string[];
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

// ── Chat / Conversation (Phase 2) ────────────────────────────────────────────

export interface ChatSession {
  id: number;
  project_id: number;
  created_at: string;
  last_message_at: string;
  status: "active" | "archived";
}

export interface ChatMessage {
  id: number;
  session_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  message_type: "text" | "plan_preview" | "execution_status" | "error";
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ChatResponse {
  response: string;
  type: "text" | "plan_generated" | "error";
  plan_id: number | null;
  metadata: Record<string, unknown>;
}

// ── Analytics (Task 5.2) ────────────────────────────────────────────────────

export interface DayBucket {
  date: string;
  count: number;
  successes: number;
  failures: number;
}

export interface TopProject {
  name: string;
  count: number;
}

export interface RecentActivity {
  timestamp: string;
  action: string;
  project: string;
  environment: string;
  status: string;
  duration_seconds: number | null;
}

export interface AnalyticsSummary {
  total_deployments: number;
  success_rate: number;
  average_deploy_time_seconds: number;
  rollback_count: number;
  deployments_by_day: DayBucket[];
  deployments_by_environment: Record<string, number>;
  most_deployed_project: TopProject | null;
  recent_activity: RecentActivity[];
}
