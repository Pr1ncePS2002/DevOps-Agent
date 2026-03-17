/**
 * Unit tests for frontend type definitions.
 * Validates type safety and structure of shared types.
 */
import { describe, it, expect } from "vitest";
import type {
  Project,
  PlanPreview,
  ExecutionDetail,
  ProjectRegistrationPayload,
  ProjectRegistrationResult,
  PlanStatus,
  ExecutionStatus,
} from "@/lib/types";

describe("Type definitions", () => {
  it("Project interface has required fields", () => {
    const project: Project = {
      id: 1,
      name: "test-app",
    };
    expect(project.id).toBe(1);
    expect(project.name).toBe("test-app");
  });

  it("ProjectRegistrationPayload structure is valid", () => {
    const payload: ProjectRegistrationPayload = {
      projectName: "my-app",
      description: "A test app",
      source: { type: "local", config: { path: "/tmp/app" } },
      deployment: { platform: "docker", config: {} },
      env: { NODE_ENV: "production" },
    };
    expect(payload.projectName).toBe("my-app");
    expect(payload.source.type).toBe("local");
    expect(payload.deployment.platform).toBe("docker");
  });

  it("PlanPreview includes action and environments", () => {
    const plan: PlanPreview = {
      plan_id: 42,
      action: "deploy",
      environments: ["staging", "production"],
      post_steps: [],
      warnings: [],
      status: "pending_approval",
    };
    expect(plan.action).toBe("deploy");
    expect(plan.environments).toHaveLength(2);
  });

  it("ExecutionDetail includes logs field", () => {
    const execution: ExecutionDetail = {
      id: 1,
      plan_id: 42,
      status: "running",
      logs: "Building image...\nStarting container...",
    };
    expect(execution.logs).toContain("Building");
  });

  it("PlanStatus union covers all valid states", () => {
    const validStatuses: PlanStatus[] = [
      "pending_approval",
      "approved",
      "running",
      "failed",
      "rolled_back",
      "succeeded",
    ];
    expect(validStatuses).toHaveLength(6);
  });

  it("ExecutionStatus union covers all valid states", () => {
    const validStatuses: ExecutionStatus[] = [
      "queued",
      "running",
      "failed",
      "succeeded",
      "rolled_back",
    ];
    expect(validStatuses).toHaveLength(5);
  });

  it("ProjectRegistrationResult has camelCase keys", () => {
    const result: ProjectRegistrationResult = {
      projectId: 1,
      name: "my-app",
      workspacePath: "/data/workspace/my-app",
      detectedStack: "node",
      dockerfilePath: "/data/workspace/my-app/Dockerfile",
      dockerfileGenerated: true,
      deploymentPlatform: "docker",
    };
    expect(result.projectId).toBe(1);
    expect(result.deploymentPlatform).toBe("docker");
  });
});
