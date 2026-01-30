interface StatGridProps {
  projectsTracked: number;
  dryRunEnabled: boolean;
  approvalsThisWeek: number;
  incidentsBlocked: number;
}

const formatter = new Intl.NumberFormat("en-US");

export function StatGrid(props: StatGridProps) {
  const cards = [
    {
      title: "Projects under watch",
      value: formatter.format(props.projectsTracked),
      footnote: "Synced from backend registry"
    },
    {
      title: "Manual approvals",
      value: props.approvalsThisWeek,
      footnote: "This week",
      accent: "bg-accent-400/20 text-accent-200"
    },
    {
      title: "Dry-run policy",
      value: props.dryRunEnabled ? "ENABLED" : "DISABLED",
      footnote: props.dryRunEnabled ? "Safe mode enforced" : "Exec auth required"
    },
    {
      title: "Incidents intercepted",
      value: props.incidentsBlocked,
      footnote: "Past 30 days",
      accent: "bg-red-400/20 text-red-100"
    }
  ];

  return (
    <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <article
          key={card.title}
          className="rounded-3xl border border-white/5 bg-surface-800/60 p-5 shadow-card"
        >
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">{card.title}</p>
          <p className="mt-3 text-3xl font-display">
            <span className={card.accent ?? "text-white"}>{card.value}</span>
          </p>
          <p className="mt-1 text-xs text-white/50">{card.footnote}</p>
        </article>
      ))}
    </section>
  );
}
