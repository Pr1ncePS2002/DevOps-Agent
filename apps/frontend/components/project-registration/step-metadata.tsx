"use client";

import type { RegistrationFormValues } from "./types";

interface Props {
    form: RegistrationFormValues;
    update: (k: "projectName" | "description", v: string) => void;
    onNext: () => void;
}

export function StepMetadata({ form, update, onNext }: Props) {
    const canContinue = form.projectName.trim().length > 0;

    return (
        <div className="space-y-5">
            <div>
                <h3 className="text-lg font-semibold text-white">Project Details</h3>
                <p className="mt-1 text-sm text-white/50">Give your project a name and optional description.</p>
            </div>

            <div className="space-y-3">
                <div className="space-y-1.5">
                    <label className="text-xs font-medium uppercase tracking-widest text-white/60">
                        Project Name <span className="text-red-400">*</span>
                    </label>
                    <input
                        type="text"
                        value={form.projectName}
                        onChange={(e) => update("projectName", e.target.value)}
                        placeholder="my-awesome-app"
                        className="w-full rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-white/30 focus:border-accent-400 focus:outline-none"
                    />
                </div>

                <div className="space-y-1.5">
                    <label className="text-xs font-medium uppercase tracking-widest text-white/60">
                        Description
                    </label>
                    <textarea
                        value={form.description}
                        onChange={(e) => update("description", e.target.value)}
                        rows={3}
                        placeholder="What does this project do?"
                        className="w-full resize-none rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white placeholder:text-white/30 focus:border-accent-400 focus:outline-none"
                    />
                </div>
            </div>

            <button
                type="button"
                onClick={onNext}
                disabled={!canContinue}
                className="w-full rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 transition hover:bg-accent-400 disabled:opacity-40"
            >
                Continue →
            </button>
        </div>
    );
}
