import { Sparkles } from "lucide-react";

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
            <span className="text-white/40">&bull;</span>
            <span>Policy guardrail warnings</span>
            <span className="text-white/40">&bull;</span>
            <span>Manual approval before run</span>
          </div>
        </div>
        <div className="shrink-0 rounded-2xl border border-accent-400/20 bg-accent-500/10 px-5 py-4 text-center">
          <p className="text-xs uppercase tracking-widest text-accent-300/60">Quick start</p>
          <p className="mt-1 text-sm text-white/70">Use the <span className="text-accent-300 font-semibold">Launch Full Demo</span> button below</p>
        </div>
      </div>
    </section>
  );
}
