/**
 * Config-driven matrices for the ProjectRegistration wizard.
 * Adding a new platform = one row in each matrix below. No other file changes.
 */

// Types defined locally — no external package dependency needed
export type SourceType = "local" | "github";
export type DeploymentPlatform = "local" | "docker" | "vercel" | "render";

export const PLATFORM_MATRIX: Record<SourceType, DeploymentPlatform[]> = {
    local: ["local", "docker"],
    github: ["local", "docker", "vercel", "render"],
};

/**
 * Required env vars per source × platform combination.
 * These are REAL runtime env vars (not paths — those come from Step 2).
 * Leave empty if no specific env vars are required to run.
 */
export const ENV_MATRIX: Partial<Record<`${SourceType}:${DeploymentPlatform}`, string[]>> = {
    "local:local": [],                        // No special env vars needed — just run it
    "local:docker": ["APP_PORT"],              // Port to expose from the container
    "github:local": [],
    "github:docker": ["APP_PORT"],
    "github:vercel": ["VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID"],
    "github:render": ["RENDER_API_KEY", "RENDER_SERVICE_ID"],
};

export const PLATFORM_LABELS: Record<DeploymentPlatform, { label: string; description: string; icon: string }> = {
    local: { label: "Local", description: "Run directly on this machine", icon: "🖥️" },
    docker: { label: "Docker", description: "Container-based local deployment", icon: "🐳" },
    vercel: { label: "Vercel", description: "Serverless edge deployment", icon: "▲" },
    render: { label: "Render", description: "Managed cloud hosting", icon: "☁️" },
};

export const SOURCE_LABELS: Record<SourceType, { label: string; description: string }> = {
    local: { label: "Local Path", description: "Project lives on this machine" },
    github: { label: "GitHub Repository", description: "Clone & deploy from GitHub" },
};

export const STEPS = [
    { id: 1, label: "Metadata" },
    { id: 2, label: "Source" },
    { id: 3, label: "Platform" },
    { id: 4, label: "Environment" },
    { id: 5, label: "Preview" },
] as const;

export function getRequiredEnvKeys(source: SourceType, platform: DeploymentPlatform): string[] {
    return ENV_MATRIX[`${source}:${platform}`] ?? [];
}

export function getAvailablePlatforms(source: SourceType): DeploymentPlatform[] {
    return PLATFORM_MATRIX[source] ?? [];
}
