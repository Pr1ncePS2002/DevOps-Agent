"use client";

import { useState } from "react";
import type { RegistrationFormValues } from "./types";
import { ProviderConnect } from "./provider-connect";
import type { DeploymentPlatform } from "./config";

const FIELD_HELP: Record<string, { label: string; placeholder: string; link?: string; linkLabel?: string }> = {
  APP_PORT: {
    label: "Application Port",
    placeholder: "3000",
  },
  VERCEL_TOKEN: {
    label: "Vercel API Token",
    placeholder: "xxxxxxxxxxxxxxxx",
    link: "https://vercel.com/account/tokens",
    linkLabel: "Get token",
  },
  VERCEL_ORG_ID: {
    label: "Vercel Team / Org ID",
    placeholder: "team_xxxxxxxx",
  },
  VERCEL_PROJECT_ID: {
    label: "Vercel Project ID",
    placeholder: "prj_xxxxxxxx",
  },
  RENDER_API_KEY: {
    label: "Render API Key",
    placeholder: "rnd_xxxxxxxx",
    link: "https://dashboard.render.com/settings#api-keys",
    linkLabel: "Get API key",
  },
  RENDER_SERVICE_ID: {
    label: "Render Service ID",
    placeholder: "srv-xxxxxxxx",
  },
};

interface Props {
  form: RegistrationFormValues;
  requiredEnvKeys: string[];
  derivedEnv: Record<string, string>;
  updateEnvKey: (key: string, value: string) => void;
  addEnvKey: (key: string) => void;
  removeEnvKey: (key: string) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepEnv({
  form,
  requiredEnvKeys,
  derivedEnv,
  updateEnvKey,
  addEnvKey,
  removeEnvKey,
  onNext,
  onBack,
}: Props) {
  const [newKey, setNewKey] = useState("");
  const allKeys = [...new Set([...requiredEnvKeys, ...Object.keys(derivedEnv)])];
  const customKeys = allKeys.filter((k) => !requiredEnvKeys.includes(k));
  const isDocker = form.platform === "docker";
  const isVercel = form.platform === "vercel";
  const isRender = form.platform === "render";
  const showProviderConnect = isVercel || isRender;

  function handleAddKey() {
    const k = newKey.trim().toUpperCase().replace(/\s+/g, "_");
    if (k && !allKeys.includes(k)) {
      addEnvKey(k);
      setNewKey("");
    }
  }

  function handleVercelConnected(data: { token: string; teamId: string | null; projectId: string }) {
    updateEnvKey("VERCEL_TOKEN", data.token);
    if (data.teamId) updateEnvKey("VERCEL_ORG_ID", data.teamId);
    updateEnvKey("VERCEL_PROJECT_ID", data.projectId);
  }

  function handleRenderConnected(data: { apiKey: string; serviceId: string }) {
    updateEnvKey("RENDER_API_KEY", data.apiKey);
    updateEnvKey("RENDER_SERVICE_ID", data.serviceId);
  }

  // Client-side field validation
  function validateField(key: string, value: string): string | null {
    if (!value.trim()) return `${key} is required`;
    if (key === "APP_PORT" && (isNaN(Number(value)) || Number(value) < 1 || Number(value) > 65535)) {
      return "Port must be a number between 1 and 65535";
    }
    return null;
  }

  const hasValidationErrors = requiredEnvKeys.some((key) => {
    const val = derivedEnv[key] ?? "";
    return validateField(key, val) !== null;
  });

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-lg font-semibold text-white">Environment Variables</h3>
        <p className="mt-1 text-sm text-white/50">
          {isDocker && "Configure runtime environment for your Docker container."}
          {isVercel && "Connect your Vercel account or enter credentials manually."}
          {isRender && "Connect your Render account or enter credentials manually."}
          {!isDocker && !isVercel && !isRender && "Runtime environment variables for your deployed application."}
        </p>
      </div>

      {/* Dockerfile auto-gen notice */}
      {isDocker && (
        <div className="flex items-start gap-3 rounded-2xl border border-blue-500/20 bg-blue-500/10 px-4 py-3">
          <span className="text-lg">🐳</span>
          <div>
            <p className="text-sm font-medium text-blue-300">Dockerfile Auto-Generation</p>
            <p className="mt-0.5 text-xs text-blue-300/70">
              Don&apos;t have a Dockerfile? No problem — the backend will automatically detect your
              stack (Node.js / Python) and generate one for you during registration.
            </p>
          </div>
        </div>
      )}

      {/* Provider connect (Phase 3a) */}
      {showProviderConnect && (
        <ProviderConnect
          platform={form.platform as DeploymentPlatform}
          onVercelConnected={handleVercelConnected}
          onRenderConnected={handleRenderConnected}
        />
      )}

      {/* Required keys with guided labels and help links */}
      {requiredEnvKeys.length > 0 ? (
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-widest text-white/40">Required</p>
          {requiredEnvKeys.map((key) => {
            const help = FIELD_HELP[key];
            const val = derivedEnv[key] ?? "";
            const err = val ? validateField(key, val) : null;
            return (
              <div key={key} className="space-y-1">
                <div className="flex items-center gap-2">
                  <label className="w-44 shrink-0 space-y-0.5">
                    <span className="block rounded-lg bg-accent-500/10 px-3 py-2 text-xs font-mono text-accent-300">
                      {key}
                    </span>
                    {help && (
                      <span className="block px-1 text-[10px] text-white/40">{help.label}</span>
                    )}
                  </label>
                  <div className="flex flex-1 flex-col gap-1">
                    <input
                      type={key.includes("TOKEN") || key.includes("KEY") || key.includes("SECRET") ? "password" : "text"}
                      value={val}
                      onChange={(e) => updateEnvKey(key, e.target.value)}
                      placeholder={help?.placeholder ?? `Value for ${key}`}
                      className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-white placeholder:text-white/30 focus:border-accent-400 focus:outline-none"
                    />
                    {err && <span className="text-[10px] text-amber-400">{err}</span>}
                  </div>
                  {!val && (
                    <span
                      className="h-2 w-2 shrink-0 rounded-full bg-amber-400"
                      title="Fill before deploying"
                    />
                  )}
                </div>
                {help?.link && !val && (
                  <p className="pl-[11.5rem] text-[10px] text-white/30">
                    <a
                      href={help.link}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent-300/70 underline hover:text-accent-300"
                    >
                      {help.linkLabel ?? "Get value"} →
                    </a>
                  </p>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-2xl border border-white/5 bg-black/20 px-4 py-3 text-sm text-white/40">
          ✓ No required environment variables for this source × platform combination.
          You can add custom keys below if your app needs them.
        </div>
      )}

      {/* Custom (user-added) keys */}
      {customKeys.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-widest text-white/40">Custom</p>
          {customKeys.map((key) => (
            <div key={key} className="flex items-center gap-2">
              <span className="w-44 shrink-0 rounded-lg bg-white/5 px-3 py-2 text-xs font-mono text-white/70">
                {key}
              </span>
              <input
                type="text"
                value={derivedEnv[key] ?? ""}
                onChange={(e) => updateEnvKey(key, e.target.value)}
                className="flex-1 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-white focus:border-accent-400 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => removeEnvKey(key)}
                className="shrink-0 rounded-lg border border-red-500/30 px-2 py-2 text-xs text-red-400 hover:bg-red-500/10"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add custom key */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newKey}
          onChange={(e) => setNewKey(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAddKey()}
          placeholder="MY_CUSTOM_VAR"
          className="flex-1 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs font-mono text-white placeholder:text-white/30 focus:border-accent-400 focus:outline-none"
        />
        <button
          type="button"
          onClick={handleAddKey}
          className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/60 hover:text-white"
        >
          + Add
        </button>
      </div>

      {/* Live JSON preview */}
      {Object.keys(derivedEnv).length > 0 && (
        <div className="rounded-2xl border border-white/5 bg-black/40 p-4">
          <p className="mb-2 text-xs uppercase tracking-widest text-white/30">Preview</p>
          <pre className="max-h-28 overflow-auto text-xs text-white/60">
            {JSON.stringify(derivedEnv, null, 2)}
          </pre>
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 rounded-2xl border border-white/10 px-4 py-3 text-sm font-medium text-white/60 transition hover:text-white"
        >
          ← Back
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={hasValidationErrors}
          className="flex-1 rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 transition hover:bg-accent-400 disabled:opacity-50"
        >
          Review →
        </button>
      </div>
    </div>
  );
}
