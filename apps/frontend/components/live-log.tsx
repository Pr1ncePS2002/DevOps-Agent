import { cn } from "@/lib/utils";

interface LiveLogProps {
  lines: string[];
  title?: string;
}

export function LiveLog({ lines, title = "Execution Feed" }: LiveLogProps) {
  return (
    <div className="rounded-2xl border border-white/5 bg-surface-800/70 p-4 shadow-card">
      <div className="flex items-center justify-between">
        <p className="text-sm uppercase tracking-[0.2em] text-white/60">{title}</p>
        <div className="h-[10px] w-[10px] animate-pulse rounded-full bg-accent-400" />
      </div>
      <div className="mt-4 h-48 overflow-y-auto rounded-xl bg-black/40 p-3 font-mono text-xs text-accent-400/90">
        {lines.length === 0 ? (
          <p className="text-white/50">Logs will stream here once an execution starts.</p>
        ) : (
          lines.map((line, idx) => (
            <p key={`${line}-${idx}`} className={cn("whitespace-pre-wrap", line.includes("ERROR") && "text-red-200")}>
              {line}
            </p>
          ))
        )}
      </div>
    </div>
  );
}
