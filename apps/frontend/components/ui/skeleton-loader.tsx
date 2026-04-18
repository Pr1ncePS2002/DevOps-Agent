"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn("animate-pulse rounded-xl bg-surface-700/50", className)} />
  );
}

export function StatGridSkeleton() {
  return (
    <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="rounded-3xl border border-white/5 bg-surface-800/60 p-5 shadow-card space-y-3">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-3 w-32" />
        </div>
      ))}
    </section>
  );
}

export function ChatPanelSkeleton() {
  return (
    <div className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card space-y-4 h-96">
      <Skeleton className="h-4 w-40" />
      <div className="space-y-3 flex-1">
        <div className="flex justify-end"><Skeleton className="h-10 w-48" /></div>
        <div className="flex justify-start"><Skeleton className="h-16 w-64" /></div>
        <div className="flex justify-end"><Skeleton className="h-10 w-36" /></div>
        <div className="flex justify-start"><Skeleton className="h-20 w-72" /></div>
      </div>
      <Skeleton className="h-10 w-full" />
    </div>
  );
}

export function HistoryPanelSkeleton() {
  return (
    <div className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card space-y-5">
      <Skeleton className="h-4 w-36" />
      {[...Array(4)].map((_, i) => (
        <div key={i} className="flex items-start gap-4">
          <Skeleton className="h-12 w-12 rounded-2xl" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-64" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ message, icon }: { message: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && <div className="text-white/20 mb-3">{icon}</div>}
      <p className="text-sm text-white/40">{message}</p>
    </div>
  );
}
