"use client";

import { useCallback, useMemo, useState } from "react";

import type { Project } from "@/lib/types";
import { CommandConsole } from "./command-console";
import { HistoryPanel } from "./sections/history-panel";
import { ProjectsPanel } from "./sections/projects-panel";
import { StatGrid } from "./sections/stat-grid";

interface DashboardClientProps {
  initialProjects: Project[];
  dryRunEnabled: boolean;
}

export function DashboardClient({ initialProjects, dryRunEnabled }: DashboardClientProps) {
  const [projects, setProjects] = useState<Project[]>(initialProjects);

  const handleProjectsUpdated = useCallback((nextProjects: Project[]) => {
    setProjects(nextProjects);
  }, []);

  const approvalsThisWeek = useMemo(() => Math.max(projects.length - 1, 0), [projects.length]);
  const incidentsBlocked = useMemo(() => projects.length * 2, [projects.length]);

  return (
    <>
      <StatGrid
        projectsTracked={projects.length}
        dryRunEnabled={dryRunEnabled}
        approvalsThisWeek={approvalsThisWeek}
        incidentsBlocked={incidentsBlocked}
      />
      <CommandConsole projects={projects} />
      <section className="grid gap-6 lg:grid-cols-2">
        <ProjectsPanel projects={projects} onProjectsUpdated={handleProjectsUpdated} />
        <HistoryPanel />
      </section>
    </>
  );
}
