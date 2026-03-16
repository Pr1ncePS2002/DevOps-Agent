"use client";

import { useCallback, useMemo, useState } from "react";
import { registerProjectV2 } from "@/lib/api";
import type { ProjectRegistrationResult } from "@/lib/types";
import { buildRegistrationPayload, type RegistrationFormValues } from "./types";
import { getAvailablePlatforms, getRequiredEnvKeys } from "./config";
import type { DeploymentPlatform, SourceType } from "./config";

const DEFAULT_FORM: RegistrationFormValues = {
    projectName: "",
    description: "",
    sourceType: "local",
    localPath: "",
    githubRepoUrl: "",
    githubBranch: "main",
    githubAccessToken: "",
    platform: "docker",
    deploymentConfig: {},
    env: {},
};

export function useProjectRegistration(onSuccess?: (result: ProjectRegistrationResult) => void) {
    const [step, setStep] = useState(1);
    const [form, setForm] = useState<RegistrationFormValues>(DEFAULT_FORM);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<ProjectRegistrationResult | null>(null);

    // ── Derived values ──────────────────────────────────────────────────────────

    /** Which platforms are valid for the current source type */
    const availablePlatforms = useMemo(
        () => getAvailablePlatforms(form.sourceType as SourceType),
        [form.sourceType]
    );

    /** Required env keys for current source × platform combo */
    const requiredEnvKeys = useMemo(
        () => getRequiredEnvKeys(form.sourceType as SourceType, form.platform as DeploymentPlatform),
        [form.sourceType, form.platform]
    );

    /** Auto-generates the env object keeping only required keys + any user-added extras */
    const derivedEnv = useMemo(() => {
        const env: Record<string, string> = {};
        for (const key of requiredEnvKeys) {
            env[key] = form.env[key] ?? "";
        }
        // Carry over any extra keys the user manually added
        for (const entry of Object.entries(form.env)) {
            const k = entry[0] as string;
            const v = entry[1] as string;
            if (!(k in env)) env[k] = v;
        }
        return env;
    }, [requiredEnvKeys, form.env]);

    /** Final payload JSON for the preview panel */
    const previewPayload = useMemo(
        () => buildRegistrationPayload({ ...form, env: derivedEnv }),
        [form, derivedEnv]
    );

    // ── Field updaters ──────────────────────────────────────────────────────────

    const updateField = useCallback(<K extends keyof RegistrationFormValues>(
        key: K,
        value: RegistrationFormValues[K]
    ) => {
        setForm((prev: RegistrationFormValues) => {
            const next = { ...prev, [key]: value };

            // When source changes, reset platform to first allowed and clear env
            if (key === "sourceType") {
                const allowed = getAvailablePlatforms(value as SourceType);
                next.platform = (allowed[0] ?? "docker") as DeploymentPlatform;
                next.env = {};
            }

            // When platform changes, clear env (required keys will auto-generate)
            if (key === "platform") {
                next.env = {};
            }

            return next;
        });
    }, []);

    const updateEnvKey = useCallback((key: string, value: string) => {
        setForm((prev: RegistrationFormValues) => ({ ...prev, env: { ...prev.env, [key]: value } }));
    }, []);

    const addEnvKey = useCallback((key: string) => {
        setForm((prev: RegistrationFormValues) => ({ ...prev, env: { ...prev.env, [key]: "" } }));
    }, []);

    const removeEnvKey = useCallback((key: string) => {
        setForm((prev: RegistrationFormValues) => {
            const next = { ...prev.env };
            delete next[key];
            return { ...prev, env: next };
        });
    }, []);

    // ── Step navigation ─────────────────────────────────────────────────────────

    const goToStep = useCallback((s: number) => {
        setError(null);
        setStep(s);
    }, []);

    const next = useCallback(() => goToStep(step + 1), [step, goToStep]);
    const back = useCallback(() => goToStep(step - 1), [step, goToStep]);

    // ── Submit ──────────────────────────────────────────────────────────────────

    const submit = useCallback(async () => {
        setError(null);
        setSubmitting(true);
        try {
            const payload = buildRegistrationPayload({ ...form, env: derivedEnv });
            const res = await registerProjectV2(payload);
            setResult(res);
            onSuccess?.(res);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Registration failed");
        } finally {
            setSubmitting(false);
        }
    }, [form, derivedEnv, onSuccess]);

    const reset = useCallback(() => {
        setForm(DEFAULT_FORM);
        setStep(1);
        setError(null);
        setResult(null);
    }, []);

    return {
        step, form, submitting, error, result,
        availablePlatforms, requiredEnvKeys, derivedEnv, previewPayload,
        updateField, updateEnvKey, addEnvKey, removeEnvKey,
        goToStep, next, back, submit, reset,
    };
}
