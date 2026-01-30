import { ArrowUpRight, Sparkles } from "lucide-react";

export function HeroBanner() {
  return (
    <section className="relative overflow-hidden rounded-[32px] border border-white/10 bg-surface-800/70 p-10 shadow-card">
      <div className="absolute inset-0 opacity-60" aria-hidden>
        <div className="h-full w-full bg-[radial-gradient(circle_at_top,_rgba(85,214,255,0.35),_transparent_60%)]" />
      </div>
      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.3em] text-white/70">
            <Sparkles className="h-4 w-4 text-accent-400" /> Local-first DevOps intelligence
          </div>
          <h1 className="font-display text-4xl font-semibold text-white lg:text-5xl">
            Command every deployment with <span className="text-accent-400">confidence</span>.
          </h1>
          <p className="max-w-2xl text-lg text-white/80">
            Preview AI plans, gate risky actions, and stream execution logs in one cockpit. Made for production-critical DevOps engineers.
          </p>
          <div className="flex flex-wrap gap-4 text-sm text-white/70">
            <span>Deterministic command parser</span>
            <span className="text-white/40">•</span>
            <span>Policy guardrail warnings</span>
            <span className="text-white/40">•</span>
            <span>Manual approval before run</span>
          </div>
        </div>
        <button className="group relative flex items-center gap-3 rounded-full border border-accent-400/40 px-6 py-3 text-sm font-semibold uppercase tracking-wide text-accent-300">
          Launch Runbook Studio
          <ArrowUpRight className="h-4 w-4 transition group-hover:translate-x-1 group-hover:-translate-y-1" />
        </button>
      </div>
    </section>
  );
}
