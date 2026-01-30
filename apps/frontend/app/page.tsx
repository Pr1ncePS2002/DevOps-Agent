import { Suspense } from "react";

import { DashboardClient } from "@/components/dashboard-client";
import { HeroBanner } from "@/components/sections/hero-banner";
import { fetchProjects } from "@/lib/api";

export default async function Page() {
  let projects: Awaited<ReturnType<typeof fetchProjects>> = [];
  try {
    projects = await fetchProjects();
  } catch (error) {
    console.error("Unable to reach backend", error);
  }

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-10 lg:px-6">
      <HeroBanner />
      <Suspense fallback={<div className="rounded-3xl border border-white/5 bg-surface-800/70 p-6 text-white/70">Loading dashboard…</div>}>
        <DashboardClient initialProjects={projects} dryRunEnabled={process.env.NEXT_PUBLIC_DRY_RUN === "true"} />
      </Suspense>
    </main>
  );
}
