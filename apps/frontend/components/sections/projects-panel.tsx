"use client";

import { useCallback, useState } from "react";
import { FolderKanban, Plus, X } from "lucide-react";

import { fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ProjectRegistration } from "@/components/project-registration";

interface ProjectsPanelProps {
  projects: Project[];
  onProjectsUpdated?: (projects: Project[]) => void;
}

export function ProjectsPanel({ projects, onProjectsUpdated }: ProjectsPanelProps) {
  const [showWizard, setShowWizard] = useState(false);

  const refreshProjects = useCallback(async () => {
    const next = await fetchProjects();
    onProjectsUpdated?.(next);
  }, [onProjectsUpdated]);

  const handleSuccess = useCallback(async () => {
    await refreshProjects();
    setShowWizard(false);
  }, [refreshProjects]);

  return (
    <section className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FolderKanban className="h-5 w-5 text-accent-300" />
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-white/60">Projects</p>
            <p className="text-white/80">Synced from backend registry</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setShowWizard(true)}
          className="flex items-center gap-1.5 rounded-2xl bg-accent-500/20 px-3 py-2 text-xs font-semibold text-accent-300 transition hover:bg-accent-500/30"
        >
          <Plus className="h-3.5 w-3.5" />
          Register Project
        </button>
      </div>

      {/* Inline wizard (collapsible) */}
      {showWizard && (
        <div className="mt-6 rounded-2xl border border-accent-400/20 bg-black/30 p-5">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs uppercase tracking-widest text-white/50">New Project</p>
            <button
              type="button"
              onClick={() => setShowWizard(false)}
              className="text-white/30 hover:text-white/70"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <ProjectRegistration
            onSuccess={handleSuccess}
            onClose={() => setShowWizard(false)}
          />
        </div>
      )}

      {/* Project list */}
      <div className="mt-4 divide-y divide-white/5">
        {projects.length === 0 ? (
          <p className="py-6 text-sm text-white/60">
            No projects yet. Click <span className="text-accent-300">Register Project</span> to add one.
          </p>
        ) : (
          projects.map((project) => (
            <article key={project.id} className="py-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-lg font-display text-white">{project.name}</p>
                  {project.description && (
                    <p className="mt-0.5 text-xs text-white/50">{project.description}</p>
                  )}
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    <Badge>{project.detected_stack ?? "?"}</Badge>
                    {project.deployment_platform && (
                      <Badge accent>{project.deployment_platform}</Badge>
                    )}
                    {project.has_env_file && <Badge>env ✓</Badge>}
                  </div>
                </div>
                <div className="shrink-0 text-right text-xs text-white/60">
                  <p className="text-white/30">#{project.id}</p>
                  {project.repo_url ? (
                    <a
                      href={project.repo_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent-300 hover:text-accent-200"
                    >
                      repo ↗
                    </a>
                  ) : (
                    <span className="font-mono text-white/30">{project.repo_path ?? "local"}</span>
                  )}
                </div>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}

function Badge({ children, accent }: { children: React.ReactNode; accent?: boolean }) {
  return (
    <span
      className={cn(
        "rounded-lg px-2 py-0.5 text-xs",
        accent ? "bg-accent-500/15 text-accent-300" : "bg-white/5 text-white/50"
      )}
    >
      {children}
    </span>
  );
}
