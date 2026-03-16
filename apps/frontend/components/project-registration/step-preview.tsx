"use client";

import type { ProjectRegistrationPayload } from "@/lib/types";

interface Props {
    payload: ProjectRegistrationPayload;
    submitting: boolean;
    error: string | null;
    onSubmit: () => void;
    onBack: () => void;
}

export function StepPreview({ payload, submitting, error, onSubmit, onBack }: Props) {
    return (
        <div className="space-y-5">
            <div>
                <h3 className="text-lg font-semibold text-white">Review & Register</h3>
                <p className="mt-1 text-sm text-white/50">
                    Confirm the configuration below before submitting.
                </p>
            </div>

            {/* Config preview */}
            <div className="rounded-2xl border border-white/5 bg-black/40">
                <div className="flex items-center justify-between border-b border-white/5 px-4 py-2">
                    <p className="text-xs uppercase tracking-widest text-white/30">Final Config</p>
                    <span className="rounded-lg bg-accent-500/20 px-2 py-0.5 text-xs text-accent-300">JSON</span>
                </div>
                <pre className="max-h-64 overflow-auto p-4 text-xs leading-relaxed text-white/70">
                    {JSON.stringify(payload, null, 2)}
                </pre>
            </div>

            {/* Summary chips */}
            <div className="flex flex-wrap gap-2">
                <Chip label="Name" value={payload.projectName} />
                <Chip label="Source" value={payload.source.type} accent />
                <Chip label="Platform" value={payload.deployment.platform} accent />
                <Chip label="Env keys" value={String(Object.keys(payload.env).length)} />
            </div>

            {error && (
                <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                    {error}
                </div>
            )}

            <div className="flex gap-3">
                <button
                    type="button"
                    onClick={onBack}
                    disabled={submitting}
                    className="flex-1 rounded-2xl border border-white/10 px-4 py-3 text-sm font-medium text-white/60 transition hover:text-white disabled:opacity-40"
                >
                    ← Back
                </button>
                <button
                    type="button"
                    onClick={onSubmit}
                    disabled={submitting}
                    className="flex-1 rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 transition hover:bg-accent-400 disabled:opacity-50"
                >
                    {submitting ? (
                        <span className="flex items-center justify-center gap-2">
                            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 000 16v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
                            </svg>
                            Registering…
                        </span>
                    ) : (
                        "🚀 Register Project"
                    )}
                </button>
            </div>
        </div>
    );
}

function Chip({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
    return (
        <span className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs">
            <span className="text-white/40">{label}:</span>
            <span className={accent ? "text-accent-300 font-medium" : "text-white/70"}>{value}</span>
        </span>
    );
}
