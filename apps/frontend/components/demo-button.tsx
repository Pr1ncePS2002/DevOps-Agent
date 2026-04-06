"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Play, Sparkles } from "lucide-react";
import { API_BASE_URL } from "@/lib/config";

interface DemoPreset {
  name: string;
  description: string;
  source_type: string;
  deployment_platform: string;
  detected_stack: string;
}

interface DemoFullResult {
  project_id: number;
  plan_id: number;
  execution_id: number;
  rq_job_id: string;
  name: string;
  detected_stack: string;
  message: string;
}

interface Props {
  onDemoStarted?: (executionId: number) => void;
  compact?: boolean;
}

export function DemoButton({ onDemoStarted, compact }: Props) {
  const [presets, setPresets] = useState<DemoPreset[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/demo/presets`, { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => setPresets(data.presets ?? []))
      .catch(() => setPresets([]));
  }, []);

  const handleFullDemo = useCallback(async () => {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const payload = {
        command: "Register the built-in demo app and deploy it locally on port 8080."
      };
      const res = await fetch(`${API_BASE_URL}/demo/run-full`, { 
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail || res.statusText);
      }
      const data: DemoFullResult = await res.json();
      setResult(data.message);
      onDemoStarted?.(data.execution_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo setup failed");
    } finally {
      setLoading(false);
    }
  }, [onDemoStarted]);

  if (presets.length === 0) return null;

  if (compact) {
    return (
      <button
        type="button"
        onClick={handleFullDemo}
        disabled={loading}
        className="inline-flex items-center gap-1.5 rounded-xl border border-accent-400/30 bg-accent-500/10 px-3 py-2 text-xs font-semibold text-accent-300 transition hover:bg-accent-500/20 disabled:opacity-50"
      >
        {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
        Launch Full Demo
      </button>
    );
  }

  const preset = presets[0];

  return (
    <div className="rounded-2xl border border-accent-400/20 bg-accent-500/5 p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-accent-300" />
        <h3 className="text-sm font-semibold text-accent-200">Try with a sample app</h3>
      </div>
      <p className="text-xs text-white/50">
        See the full deployment flow end-to-end. This registers a Node.js Express demo app, uploads a pre-filled .env,
        creates a deployment plan, approves it, and builds + runs in Docker — all in one click.
      </p>

      <div className="rounded-xl border border-white/5 bg-black/30 px-4 py-3 text-xs space-y-1">
        <p className="text-white/60"><span className="text-white/40 w-16 inline-block">App:</span> {preset?.name}</p>
        <p className="text-white/60"><span className="text-white/40 w-16 inline-block">Stack:</span> {preset?.detected_stack}</p>
        <p className="text-white/60"><span className="text-white/40 w-16 inline-block">Platform:</span> {preset?.deployment_platform}</p>
        <p className="text-white/60"><span className="text-white/40 w-16 inline-block">Flow:</span> Register → .env → Plan → Build → Run → Health check</p>
      </div>

      <button
        type="button"
        onClick={handleFullDemo}
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-2xl bg-accent-500 px-4 py-3 text-sm font-semibold text-surface-900 transition hover:bg-accent-400 disabled:opacity-50"
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
        {loading ? "Deploying…" : "Launch Full Demo"}
      </button>

      {result && (
        <p className="rounded-xl bg-green-500/10 border border-green-500/30 px-3 py-2 text-xs text-green-300">
          ✓ {result}
        </p>
      )}
      {error && (
        <p className="rounded-xl bg-red-500/10 border border-red-500/30 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
