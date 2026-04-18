"use client";

import { useCallback, useMemo, useState } from "react";
import { Compass } from "lucide-react";

import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { AnalyticsPanel } from "./sections/analytics-panel";
import { ChatPanel } from "./chat/chat-panel";
import { CommandConsole } from "./command-console";
import { DeploymentWizard } from "./deployment-wizard";
import { HistoryPanel } from "./sections/history-panel";
import { GuidedTour } from "./onboarding/guided-tour";
import { TOUR_STEPS } from "./onboarding/tour-steps";
import { ProjectsPanel } from "./sections/projects-panel";
import { StatGrid } from "./sections/stat-grid";

type ActiveTab = "chat" | "console";

interface DashboardClientProps {
  initialProjects: Project[];
  dryRunEnabled: boolean;
}

export function DashboardClient({ initialProjects, dryRunEnabled }: DashboardClientProps) {
  const [projects, setProjects] = useState<Project[]>(initialProjects);
  const [activeTab, setActiveTab] = useState<ActiveTab>("chat");
  const [showTour, setShowTour] = useState(false);

  const handleProjectsUpdated = useCallback((nextProjects: Project[]) => {
    setProjects(nextProjects);
  }, []);

  const approvalsThisWeek = useMemo(() => Math.max(projects.length - 1, 0), [projects.length]);
  const incidentsBlocked = useMemo(() => projects.length * 2, [projects.length]);

  return (
    <>
      {/* Tour trigger */}
      <div className="flex justify-end -mb-2">
        <button
          onClick={() => setShowTour(true)}
          className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-surface-800/50 px-3 py-1.5 text-xs text-white/50 hover:text-accent-300 hover:border-accent-500/30 transition"
        >
          <Compass className="h-3.5 w-3.5" />
          Take a Tour
        </button>
      </div>

      {showTour && (
        <GuidedTour steps={TOUR_STEPS} onComplete={() => setShowTour(false)} />
      )}

      <div data-tour="stat-grid">
        <StatGrid
          projectsTracked={projects.length}
          dryRunEnabled={dryRunEnabled}
          approvalsThisWeek={approvalsThisWeek}
          incidentsBlocked={incidentsBlocked}
        />
      </div>

      <DeploymentWizard />

      {/* Tab switcher */}
      <div className="flex items-center gap-1 rounded-2xl border border-white/5 bg-surface-800/50 p-1 w-fit">
        {(["chat", "console"] as ActiveTab[]).map((tab) => (
          <button
            key={tab}
            type="button"
            data-tour={`tab-${tab}`}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "rounded-xl px-4 py-2 text-sm font-medium transition",
              activeTab === tab
                ? "bg-accent-500/20 text-accent-300 border border-accent-500/30"
                : "text-white/40 hover:text-white/70"
            )}
          >
            {tab === "chat" ? "AI Chat" : "Command Console"}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "chat" ? (
        <ChatPanel projects={projects} />
      ) : (
        <CommandConsole projects={projects} />
      )}

      <div data-tour="analytics">
        <AnalyticsPanel />
      </div>

      <section className="grid gap-6 lg:grid-cols-2">
        <div data-tour="projects-panel">
          <ProjectsPanel projects={projects} onProjectsUpdated={handleProjectsUpdated} />
        </div>
        <div data-tour="history">
          <HistoryPanel />
        </div>
      </section>
    </>
  );
}
