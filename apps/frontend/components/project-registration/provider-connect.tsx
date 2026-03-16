"use client";

import { useState } from "react";
import { connectVercel, connectRender } from "@/lib/api";
import type { VercelProject, RenderService } from "@/lib/types";
import type { DeploymentPlatform } from "./config";

interface Props {
  platform: DeploymentPlatform;
  onVercelConnected: (data: { token: string; teamId: string | null; projectId: string; projectName: string }) => void;
  onRenderConnected: (data: { apiKey: string; serviceId: string; serviceName: string }) => void;
}

export function ProviderConnect({ platform, onVercelConnected, onRenderConnected }: Props) {
  const [token, setToken] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [vercelProjects, setVercelProjects] = useState<VercelProject[]>([]);
  const [vercelTeamId, setVercelTeamId] = useState<string | null>(null);
  const [renderServices, setRenderServices] = useState<RenderService[]>([]);
  const [connected, setConnected] = useState(false);

  async function handleConnect() {
    if (!token.trim()) return;
    setError(null);
    setConnecting(true);

    try {
      if (platform === "vercel") {
        const res = await connectVercel(token.trim());
        setVercelProjects(res.projects);
        setVercelTeamId(res.team_id);
        setConnected(true);
      } else if (platform === "render") {
        const res = await connectRender(token.trim());
        setRenderServices(res.services);
        setConnected(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setConnecting(false);
    }
  }

  if (platform === "vercel") {
    return (
      <div className="space-y-3 rounded-2xl border border-purple-500/20 bg-purple-500/5 p-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">▲</span>
          <h4 className="text-sm font-semibold text-purple-200">Connect Vercel</h4>
        </div>

        {!connected ? (
          <>
            <p className="text-xs text-purple-300/60">
              Enter your Vercel API token to auto-populate project settings.{" "}
              <a
                href="https://vercel.com/account/tokens"
                target="_blank"
                rel="noreferrer"
                className="text-purple-300 underline hover:text-purple-200"
              >
                Get token →
              </a>
            </p>
            <div className="flex gap-2">
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Vercel API Token"
                className="flex-1 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-white placeholder:text-white/30 focus:border-purple-400 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleConnect}
                disabled={connecting || !token.trim()}
                className="rounded-xl bg-purple-500/20 px-4 py-2 text-xs font-semibold text-purple-200 transition hover:bg-purple-500/30 disabled:opacity-50"
              >
                {connecting ? "Connecting…" : "Connect"}
              </button>
            </div>
            {error && <p className="text-xs text-red-400">{error}</p>}
          </>
        ) : (
          <>
            <p className="text-xs text-green-400">✓ Connected — select a project:</p>
            <select
              onChange={(e) => {
                const proj = vercelProjects.find((p) => p.id === e.target.value);
                if (proj) {
                  onVercelConnected({
                    token: token.trim(),
                    teamId: vercelTeamId,
                    projectId: proj.id,
                    projectName: proj.name,
                  });
                }
              }}
              defaultValue=""
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-white focus:border-purple-400 focus:outline-none"
            >
              <option value="" disabled>
                Choose a Vercel project…
              </option>
              {vercelProjects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.framework ? `(${p.framework})` : ""}
                </option>
              ))}
            </select>
          </>
        )}
      </div>
    );
  }

  if (platform === "render") {
    return (
      <div className="space-y-3 rounded-2xl border border-teal-500/20 bg-teal-500/5 p-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">☁️</span>
          <h4 className="text-sm font-semibold text-teal-200">Connect Render</h4>
        </div>

        {!connected ? (
          <>
            <p className="text-xs text-teal-300/60">
              Enter your Render API key to auto-populate service settings.{" "}
              <a
                href="https://dashboard.render.com/settings#api-keys"
                target="_blank"
                rel="noreferrer"
                className="text-teal-300 underline hover:text-teal-200"
              >
                Get API key →
              </a>
            </p>
            <div className="flex gap-2">
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Render API Key"
                className="flex-1 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-white placeholder:text-white/30 focus:border-teal-400 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleConnect}
                disabled={connecting || !token.trim()}
                className="rounded-xl bg-teal-500/20 px-4 py-2 text-xs font-semibold text-teal-200 transition hover:bg-teal-500/30 disabled:opacity-50"
              >
                {connecting ? "Connecting…" : "Connect"}
              </button>
            </div>
            {error && <p className="text-xs text-red-400">{error}</p>}
          </>
        ) : (
          <>
            <p className="text-xs text-green-400">✓ Connected — select a service:</p>
            <select
              onChange={(e) => {
                const svc = renderServices.find((s) => s.id === e.target.value);
                if (svc) {
                  onRenderConnected({
                    apiKey: token.trim(),
                    serviceId: svc.id,
                    serviceName: svc.name,
                  });
                }
              }}
              defaultValue=""
              className="w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-white focus:border-teal-400 focus:outline-none"
            >
              <option value="" disabled>
                Choose a Render service…
              </option>
              {renderServices.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.type})
                </option>
              ))}
            </select>
          </>
        )}
      </div>
    );
  }

  return null;
}
