"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import { Activity, BarChart3, Clock, RotateCcw, TrendingUp } from "lucide-react";

import { fetchAnalyticsSummary } from "@/lib/api";
import type { AnalyticsSummary, RecentActivity } from "@/lib/types";
import { StatusPill } from "../status-pill";

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

function timeAgo(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const ENV_COLORS: Record<string, string> = {
  production: "#ef4444",
  staging: "#f59e0b",
  dev: "#22c55e",
  default: "#6366f1",
};

function envColor(env: string): string {
  return ENV_COLORS[env.toLowerCase()] ?? ENV_COLORS.default;
}

export function AnalyticsPanel() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const summary = await fetchAnalyticsSummary();
      setData(summary);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <section className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
        <div className="flex items-center gap-3 mb-6">
          <BarChart3 className="h-5 w-5 text-accent-300" />
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">Deployment Analytics</p>
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-2xl bg-surface-700/50 animate-pulse" />
          ))}
        </div>
        <div className="mt-6 h-48 rounded-2xl bg-surface-700/50 animate-pulse" />
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
        <div className="flex items-center gap-3">
          <BarChart3 className="h-5 w-5 text-red-400" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      </section>
    );
  }

  if (!data) return null;

  const pieData = Object.entries(data.deployments_by_environment).map(([name, value]) => ({
    name,
    value,
    fill: envColor(name),
  }));

  return (
    <section className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <BarChart3 className="h-5 w-5 text-accent-300" />
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">Deployment Analytics</p>
          <p className="text-sm text-white/40">Real-time metrics from execution history</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<Activity className="h-4 w-4" />}
          title="Total Deployments"
          value={String(data.total_deployments)}
          accent="text-accent-300"
        />
        <StatCard
          icon={<TrendingUp className="h-4 w-4" />}
          title="Success Rate"
          value={`${data.success_rate}%`}
          accent={data.success_rate >= 80 ? "text-green-400" : data.success_rate >= 50 ? "text-yellow-400" : "text-red-400"}
        />
        <StatCard
          icon={<Clock className="h-4 w-4" />}
          title="Avg Deploy Time"
          value={formatDuration(data.average_deploy_time_seconds)}
          accent="text-blue-400"
        />
        <StatCard
          icon={<RotateCcw className="h-4 w-4" />}
          title="Rollbacks"
          value={String(data.rollback_count)}
          accent={data.rollback_count > 0 ? "text-red-400" : "text-green-400"}
        />
      </div>

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Deployments by day chart */}
        <div className="lg:col-span-2 rounded-2xl border border-white/5 bg-black/20 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-white/50 mb-4">Deployments Over Time</p>
          {data.deployments_by_day.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data.deployments_by_day} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                  tickFormatter={(v: string) => v.slice(5)}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                />
                <YAxis
                  tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a2e",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 12,
                    color: "#fff",
                  }}
                />
                <Bar dataKey="successes" stackId="a" fill="#22c55e" radius={[0, 0, 0, 0]} name="Success" />
                <Bar dataKey="failures" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} name="Failed" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-white/30 text-center py-12">No deployment data yet</p>
          )}
        </div>

        {/* Environment breakdown */}
        <div className="rounded-2xl border border-white/5 bg-black/20 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-white/50 mb-4">By Environment</p>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={60}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1a2e",
                      border: "1px solid rgba(255,255,255,0.1)",
                      borderRadius: 12,
                      color: "#fff",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-2 space-y-1">
                {pieData.map((e) => (
                  <div key={e.name} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: e.fill }} />
                      <span className="text-white/60 capitalize">{e.name}</span>
                    </span>
                    <span className="text-white/80 font-medium">{e.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-white/30 text-center py-12">No data</p>
          )}
        </div>
      </div>

      {/* Recent activity */}
      {data.recent_activity.length > 0 && (
        <div className="rounded-2xl border border-white/5 bg-black/20 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-white/50 mb-4">Recent Activity</p>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {data.recent_activity.map((a, i) => (
              <ActivityRow key={i} activity={a} />
            ))}
          </div>
        </div>
      )}

      {data.most_deployed_project && (
        <p className="text-xs text-white/30 text-center">
          Most active project: <span className="text-accent-300">{data.most_deployed_project.name}</span>{" "}
          ({data.most_deployed_project.count} deployments)
        </p>
      )}
    </section>
  );
}

function StatCard({ icon, title, value, accent }: { icon: React.ReactNode; title: string; value: string; accent: string }) {
  return (
    <div className="rounded-2xl border border-white/5 bg-black/20 p-4">
      <div className="flex items-center gap-2 text-white/40 mb-2">
        {icon}
        <span className="text-[10px] uppercase tracking-[0.2em]">{title}</span>
      </div>
      <p className={`text-2xl font-display ${accent}`}>{value}</p>
    </div>
  );
}

function ActivityRow({ activity: a }: { activity: RecentActivity }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="flex-1 flex items-center gap-3 min-w-0">
        <span className="text-white/80 font-medium truncate">{a.project}</span>
        <span className="text-white/40 capitalize">{a.action}</span>
        <span className="text-xs text-white/30 border border-white/10 rounded px-1.5 py-0.5">{a.environment}</span>
      </div>
      <StatusPill status={a.status as "succeeded" | "failed" | "running" | "queued" | "rolled_back"} />
      {a.duration_seconds != null && (
        <span className="text-xs text-white/30 w-16 text-right">{formatDuration(a.duration_seconds)}</span>
      )}
      <span className="text-xs text-white/30 w-16 text-right">{timeAgo(a.timestamp)}</span>
    </div>
  );
}
