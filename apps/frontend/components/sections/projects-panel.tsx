"use client";

import { useCallback, useMemo, useState } from "react";
import { FolderKanban, Plus } from "lucide-react";

import { createProject, fetchProjects } from "@/lib/api";
import type { Project } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ProjectsPanelProps {
  projects: Project[];
  onProjectsUpdated?: (projects: Project[]) => void;
}

export function ProjectsPanel({ projects, onProjectsUpdated }: ProjectsPanelProps) {
  const [name, setName] = useState("");
  const [repoPath, setRepoPath] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const canSubmit = useMemo(() => {
    if (!name.trim()) return false;
    if (!!repoPath.trim() && !!repoUrl.trim()) return false;
    return !!repoPath.trim() || !!repoUrl.trim();
  }, [name, repoPath, repoUrl]);

  const refreshProjects = useCallback(async () => {
    const next = await fetchProjects();
    onProjectsUpdated?.(next);
  }, [onProjectsUpdated]);

  const handleSubmit = useCallback(async () => {
    setError(null);

    if (!name.trim()) {
      setError("Project name is required.");
      return;
    }

    if (!!repoPath.trim() && !!repoUrl.trim()) {
      setError("Provide either repo path OR repo URL (not both).");
      return;
    }

    if (!repoPath.trim() && !repoUrl.trim()) {
      setError("Provide a local repo path or a repo URL.");
      return;
    }

    setIsSaving(true);
    try {
      await createProject({
        name: name.trim(),
        repo_path: repoPath.trim() || null,
        repo_url: repoUrl.trim() || null
      });

      setName("");
      setRepoPath("");
      setRepoUrl("");

      await refreshProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    } finally {
      setIsSaving(false);
    }
  }, [name, repoPath, repoUrl, refreshProjects]);

  return (
    <section className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 shadow-card">
      <div className="flex items-center gap-3">
        <FolderKanban className="h-5 w-5 text-accent-300" />
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">Projects</p>
          <p className="text-white/80">Synced from backend SQLite registry</p>
        </div>
      </div>

      <div className="mt-6 rounded-2xl border border-white/5 bg-black/25 p-4">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">Add project</p>
        <div className="mt-3 grid gap-3">
          <input
            value={name}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => setName(event.target.value)}
            placeholder="Project name"
            className="w-full rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white/90 focus:border-accent-400 focus:outline-none"
          />
          <input
            value={repoPath}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => setRepoPath(event.target.value)}
            placeholder="Local repo path (e.g. C:\\projects\\my-service)"
            className="w-full rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white/90 focus:border-accent-400 focus:outline-none"
          />
          <input
            value={repoUrl}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => setRepoUrl(event.target.value)}
            placeholder="Repo URL (e.g. https://github.com/org/repo.git)"
            className="w-full rounded-2xl border border-white/10 bg-black/30 p-3 text-sm text-white/90 focus:border-accent-400 focus:outline-none"
          />
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-white/50">Provide either a local path OR a repo URL.</p>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!canSubmit || isSaving}
              className={cn(
                "inline-flex items-center justify-center gap-2 rounded-2xl bg-accent-500/80 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-surface-900 transition hover:bg-accent-500",
                (!canSubmit || isSaving) && "opacity-40"
              )}
            >
              <Plus className="h-4 w-4" /> {isSaving ? "Saving…" : "Add project"}
            </button>
          </div>
          {error ? <p className="text-sm text-red-300">{error}</p> : null}
        </div>
      </div>

      <div className="mt-4 divide-y divide-white/5">
        {projects.length === 0 ? (
          <p className="py-6 text-sm text-white/60">Add a project via the backend API to see it here.</p>
        ) : (
          projects.map((project) => (
            <article key={project.id} className="py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-display text-white">{project.name}</p>
                  <p className="text-xs uppercase tracking-[0.3em] text-white/40">ID #{project.id}</p>
                </div>
                <div className="text-right text-xs text-white/60">
                  {project.repo_url ? (
                    <a
                      href={project.repo_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent-300 hover:text-accent-200"
                    >
                      repo
                    </a>
                  ) : (
                    <span>{project.repo_path ?? "Local only"}</span>
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
