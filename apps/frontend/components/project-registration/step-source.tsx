"use client";

import { SOURCE_LABELS } from "./config";
import type { SourceType } from "./config";
import type { RegistrationFormValues } from "./types";

interface Props {
    form: RegistrationFormValues;
    update: (k: keyof RegistrationFormValues, v: RegistrationFormValues[keyof RegistrationFormValues]) => void;
    onNext: () => void;
    onBack: () => void;
}

export function StepSource({ form, update, onNext, onBack }: Props) {
    const isLocal = form.sourceType === "local";

    const canContinue = isLocal
        ? (form.localPath ?? "").trim().length > 0
        : (form.githubRepoUrl ?? "").trim().length > 0;

    return (
        <div className="space-y-5">
            <div>
                <h3 className="text-lg font-semibold text-white">Project Source</h3>
                <p className="mt-1 text-sm text-white/50">Where does this project live?</p>
            </div>

            {/* Source tabs */}
            <div className="flex gap-2 rounded-2xl border border-white/10 bg-black/20 p-1">
                {(["local", "github"] as SourceType[]).map((type) => (
                    <button
                        key={type}
                        type="button"
                        onClick={() => update("sourceType", type)}
                        className={[
                            "flex-1 rounded-xl px-4 py-2.5 text-sm font-medium transition",
                            form.sourceType === type
                                ? "bg-accent-500/20 text-accent-300 shadow-inner"
                                : "text-white/50 hover:text-white/80",
                        ].join(" ")}
                    >
                        {SOURCE_LABELS[type].label}
                    </button>
                ))}
            </div>

            <p className="text-xs text-white/40">{SOURCE_LABELS[form.sourceType as SourceType].description}</p>

            {/* Conditional fields */}
            {isLocal ? (
                <div className="space-y-1.5">
                    <label className="text-xs font-medium uppercase tracking-widest text-white/60">
                        Local Path <span className="text-red-400">*</span>
                    </label>
                    <input
                        type="text"
                        value={form.localPath ?? ""}
                        onChange={(e) => update("localPath", e.target.value)}
                        placeholder="C:/projects/my-app  or  /home/user/projects/my-app"
                        className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-white/30 focus:border-accent-400 focus:outline-none"
                    />
                </div>
            ) : (
                <div className="space-y-3">
                    <div className="space-y-1.5">
                        <label className="text-xs font-medium uppercase tracking-widest text-white/60">
                            Repository URL <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="url"
                            value={form.githubRepoUrl ?? ""}
                            onChange={(e) => update("githubRepoUrl", e.target.value)}
                            placeholder="https://github.com/user/my-app"
                            className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-white/30 focus:border-accent-400 focus:outline-none"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1.5">
                            <label className="text-xs font-medium uppercase tracking-widest text-white/60">Branch</label>
                            <input
                                type="text"
                                value={form.githubBranch}
                                onChange={(e) => update("githubBranch", e.target.value)}
                                placeholder="main"
                                className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-white/30 focus:border-accent-400 focus:outline-none"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-medium uppercase tracking-widest text-white/60">
                                Access Token <span className="text-white/30">(optional)</span>
                            </label>
                            <input
                                type="password"
                                value={form.githubAccessToken ?? ""}
                                onChange={(e) => update("githubAccessToken", e.target.value)}
                                placeholder="ghp_…"
                                className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-white/30 focus:border-accent-400 focus:outline-none"
                            />
                        </div>
                    </div>
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
                    disabled={!canContinue}
                    className="flex-1 rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 transition hover:bg-accent-400 disabled:opacity-40"
                >
                    Continue →
                </button>
            </div>
        </div>
    );
}
