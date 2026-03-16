import type { DeploymentPlatform, SourceType } from "./config";

// ── Form value types (plain TypeScript — no Zod runtime needed) ───────────────

export interface RegistrationFormValues {
    projectName: string;
    description: string;
    sourceType: SourceType;
    localPath?: string;
    githubRepoUrl?: string;
    githubBranch: string;
    githubAccessToken?: string;
    platform: DeploymentPlatform;
    deploymentConfig: Record<string, string>;
    env: Record<string, string>;
}

// ── Payload builder ───────────────────────────────────────────────────────────

export function buildRegistrationPayload(form: RegistrationFormValues) {
    const sourceConfig: Record<string, string> =
        form.sourceType === "local"
            ? { path: form.localPath ?? "" }
            : {
                repoUrl: form.githubRepoUrl ?? "",
                branch: form.githubBranch,
                ...(form.githubAccessToken ? { accessToken: form.githubAccessToken } : {}),
            };

    return {
        projectName: form.projectName,
        description: form.description,
        source: { type: form.sourceType, config: sourceConfig },
        deployment: { platform: form.platform, config: form.deploymentConfig },
        env: form.env,
    };
}
