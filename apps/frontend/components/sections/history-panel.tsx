import { Clock } from "lucide-react";

import { mockHistory } from "@/lib/mock-history";
import { StatusPill } from "../status-pill";

export function HistoryPanel() {
  return (
    <section className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
      <div className="flex items-center gap-3">
        <Clock className="h-5 w-5 text-accent-300" />
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">Latest Executions</p>
          <p className="text-white/70">Live data coming once /executions history endpoint lands.</p>
        </div>
      </div>
      <ol className="mt-6 space-y-5">
        {mockHistory.map((entry) => (
          <li key={entry.id} className="flex items-start gap-4">
            <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-black/30">
              <span className="text-sm text-white/80">#{entry.id}</span>
            </div>
            <div className="flex-1 space-y-1">
              <div className="flex flex-wrap items-center gap-3">
                <p className="font-display text-lg text-white">{entry.label}</p>
                <StatusPill status={entry.status} />
              </div>
              <p className="text-sm text-white/70">{entry.summary}</p>
              <p className="text-xs uppercase tracking-[0.3em] text-white/40">{entry.timestamp}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
