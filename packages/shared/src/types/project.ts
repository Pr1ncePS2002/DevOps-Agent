/**
 * Shared DTOs for Project Registration — used by both frontend and backend
 * contract enforcement. These mirror the Pydantic schemas exactly.
 */

export type SourceType = "local" | "github";
export type DeploymentPlatform = "local" | "docker" | "vercel" | "render";

// ── Source configs ───────────────────────────────────────────────────────────

export interface LocalSourceConfig {
  path: string;
}

export interface GithubSourceConfig {
  repoUrl: string;
  branch: string;
  accessToken?: string;
}

export type SourceConfig = LocalSourceConfig | GithubSourceConfig;

// ── Deployment config ─────────────────────────────────────────────────────────

export interface DeploymentConfig {
  [key: string]: string;
}

// ── Main payload / result ─────────────────────────────────────────────────────

export interface ProjectRegistrationPayload {
  projectName: string;
  description: string;
  source: {
    type: SourceType;
    config: SourceConfig;
  };
  deployment: {
    platform: DeploymentPlatform;
    config: DeploymentConfig;
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

// ── Config-driven matrix (mirrors backend env_matrix.py and frontend config.ts) ──

export const PLATFORM_MATRIX: Record<SourceType, DeploymentPlatform[]> = {
  local: ["local", "docker"],
  github: ["local", "docker", "vercel", "render"],
};

export const ENV_MATRIX: Partial<Record<`${SourceType}:${DeploymentPlatform}`, string[]>> = {
  "local:local": [],
  "local:docker": ["APP_PORT"],
  "github:local": [],
  "github:docker": ["APP_PORT"],
  "github:vercel": ["VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID"],
  "github:render": ["RENDER_API_KEY", "RENDER_SERVICE_ID"],
};

export function getRequiredEnvKeys(
  sourceType: SourceType,
  platform: DeploymentPlatform
): string[] {
  return ENV_MATRIX[`${sourceType}:${platform}`] ?? [];
}

export function getAvailablePlatforms(sourceType: SourceType): DeploymentPlatform[] {
  return PLATFORM_MATRIX[sourceType] ?? [];
}
