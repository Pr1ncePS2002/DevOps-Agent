"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import type { ProjectRegistrationResult } from "@/lib/types";
import { STEPS } from "./config";
import { StepMetadata } from "./step-metadata";
import { StepSource } from "./step-source";
import { StepPlatform } from "./step-platform";
import { StepEnv } from "./step-env";
import { StepPreview } from "./step-preview";
import { useProjectRegistration } from "./use-project-registration";
import type { DeploymentPlatform } from "./config";
import type { RegistrationFormValues } from "./types";

interface Props {
    onSuccess?: (result: ProjectRegistrationResult) => void;
    onClose?: () => void;
}

export function ProjectRegistration({ onSuccess, onClose }: Props) {
    const {
        step, form, submitting, error, result,
        availablePlatforms, requiredEnvKeys, derivedEnv, previewPayload,
        updateField, updateEnvKey, addEnvKey, removeEnvKey,
        next, back, submit,
    } = useProjectRegistration(onSuccess);

    // Typed wrappers to avoid generic-in-JSX syntax issues
    function updateAny(k: keyof RegistrationFormValues, v: RegistrationFormValues[keyof RegistrationFormValues]) {
        updateField(k, v as never);
    }
    function updatePlatform(v: DeploymentPlatform) {
        updateField("platform", v);
    }
    function updateMetadata(k: "projectName" | "description", v: string) {
        updateField(k, v);
    }

    // ── Success state ─────────────────────────────────────────────────────────────
    if (result) {
        return (
            <div className="space-y-6 py-4 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-500/20">
                    <Check className="h-8 w-8 text-green-400" />
                </div>
                <div>
                    <h3 className="text-xl font-semibold text-white">Project Registered!</h3>
                    <p className="mt-1 text-sm text-white/60">
                        <span className="text-accent-300 font-medium">{result.name}</span> is ready on{" "}
                        <span className="text-accent-300 font-medium">{result.deploymentPlatform}</span> platform
                    </p>
                </div>
                <div className="rounded-2xl border border-white/5 bg-black/30 px-4 py-3 text-left text-xs text-white/50">
                    <p>Stack: <span className="text-white/80">{result.detectedStack}</span></p>
                    <p>Workspace: <span className="text-white/80 font-mono">{result.workspacePath}</span></p>
                    {result.dockerfilePath && (
                        <p>Dockerfile: <span className="text-white/80 font-mono">{result.dockerfilePath}</span></p>
                    )}
                </div>
                <button
                    type="button"
                    onClick={onClose}
                    className="w-full rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 hover:bg-accent-400"
                >
                    Done
                </button>
            </div>
        );
    }

    // ── Stepper header ────────────────────────────────────────────────────────────
    return (
        <div className="space-y-6">
            {/* Step indicator strip */}
            <div className="flex items-center gap-1">
                {STEPS.map(({ id, label }, i) => (
                    <div key={id} className="flex items-center gap-1">
                        <div
                            className={cn(
                                "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold",
                                step > id
                                    ? "bg-accent-500 text-surface-900"
                                    : step === id
                                        ? "border-2 border-accent-400 text-accent-300"
                                        : "border border-white/10 text-white/30"
                            )}
                        >
                            {step > id ? <Check className="h-3.5 w-3.5" /> : id}
                        </div>
                        <span
                            className={cn(
                                "hidden text-xs sm:block",
                                step === id ? "text-white/80" : "text-white/30"
                            )}
                        >
                            {label}
                        </span>
                        {i < STEPS.length - 1 && (
                            <div
                                className={cn(
                                    "mx-1 h-px w-6 flex-1",
                                    step > id ? "bg-accent-500" : "bg-white/10"
                                )}
                            />
                        )}
                    </div>
                ))}
            </div>

            {/* Step panels */}
            {step === 1 && (
                <StepMetadata
                    form={form}
                    update={updateMetadata}
                    onNext={next}
                />
            )}
            {step === 2 && (
                <StepSource
                    form={form}
                    update={updateAny}
                    onNext={next}
                    onBack={back}
                />
            )}
            {step === 3 && (
                <StepPlatform
                    form={form}
                    availablePlatforms={availablePlatforms}
                    onPlatformChange={(v) => updatePlatform(v)}
                    onNext={next}
                    onBack={back}
                />
            )}
            {step === 4 && (
                <StepEnv
                    form={form}
                    requiredEnvKeys={requiredEnvKeys}
                    derivedEnv={derivedEnv}
                    updateEnvKey={updateEnvKey}
                    addEnvKey={addEnvKey}
                    removeEnvKey={removeEnvKey}
                    onNext={next}
                    onBack={back}
                />
            )}
            {step === 5 && (
                <StepPreview
                    payload={previewPayload}
                    submitting={submitting}
                    error={error}
                    onSubmit={submit}
                    onBack={back}
                />
            )}
        </div>
    );
}
