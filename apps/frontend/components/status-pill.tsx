import { cn } from "@/lib/utils";
import type { ExecutionStatus, PlanStatus } from "@/lib/types";

const COLOR_MAP: Record<PlanStatus | ExecutionStatus, string> = {
  pending_approval: "bg-yellow-500/20 text-yellow-200 border-yellow-400/50",
  approved: "bg-slate-500/20 text-slate-100 border-slate-400/40",
  running: "bg-sky-500/20 text-sky-100 border-sky-400/60",
  failed: "bg-red-500/10 text-red-100 border-red-400/40",
  succeeded: "bg-emerald-500/15 text-emerald-100 border-emerald-400/50",
  rolled_back: "bg-orange-500/15 text-orange-100 border-orange-400/40",
  queued: "bg-purple-500/20 text-purple-100 border-purple-400/40"
};

export function StatusPill({ status }: { status: PlanStatus | ExecutionStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-wide",
        COLOR_MAP[status]
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
