"use client";

import { PLATFORM_LABELS } from "./config";
import type { DeploymentPlatform } from "./config";
import type { RegistrationFormValues } from "./types";

interface Props {
    form: RegistrationFormValues;
    availablePlatforms: DeploymentPlatform[];
    onPlatformChange: (v: DeploymentPlatform) => void;
    onNext: () => void;
    onBack: () => void;
}

export function StepPlatform({ form, availablePlatforms, onPlatformChange, onNext, onBack }: Props) {
    return (
        <div className="space-y-5">
            <div>
                <h3 className="text-lg font-semibold text-white">Deployment Platform</h3>
                <p className="mt-1 text-sm text-white/50">
                    Where should this project be deployed?
                    {form.sourceType === "local" && (
                        <span className="ml-1 text-white/30">(Local source limits options)</span>
                    )}
                </p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {availablePlatforms.map((platform) => {
                    const meta = PLATFORM_LABELS[platform];
                    const selected = form.platform === platform;
                    return (
                        <button
                            key={platform}
                            type="button"
                            onClick={() => onPlatformChange(platform)}
                            className={[
                                "flex items-start gap-3 rounded-2xl border p-4 text-left transition",
                                selected
                                    ? "border-accent-400/60 bg-accent-500/10 ring-1 ring-accent-400/30"
                                    : "border-white/10 bg-black/20 hover:border-white/20 hover:bg-black/30",
                            ].join(" ")}
                        >
                            <span className="mt-0.5 text-2xl leading-none">{meta.icon}</span>
                            <div>
                                <p className={["text-sm font-semibold", selected ? "text-accent-300" : "text-white"].join(" ")}>
                                    {meta.label}
                                </p>
                                <p className="mt-0.5 text-xs text-white/50">{meta.description}</p>
                            </div>
                            {selected && (
                                <span className="ml-auto text-accent-400">✓</span>
                            )}
                        </button>
                    );
                })}
            </div>

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
                    className="flex-1 rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 transition hover:bg-accent-400"
                >
                    Continue →
                </button>
            </div>
        </div>
    );
}
