export interface TourStep {
  id: string;
  target: string; // CSS selector
  title: string;
  description: string;
  position: "top" | "bottom" | "left" | "right";
}

export const TOUR_STEPS: TourStep[] = [
  {
    id: "welcome",
    target: "[data-tour='stat-grid']",
    title: "Welcome to AI DevOps Commander",
    description:
      "Your intelligent deployment assistant. This dashboard gives you real-time visibility into projects, deployments, and AI-powered insights.",
    position: "bottom",
  },
  {
    id: "projects",
    target: "[data-tour='projects-panel']",
    title: "Register Projects",
    description:
      "Add your projects here — local paths or GitHub repos. The system auto-detects your tech stack and generates Dockerfiles if needed.",
    position: "top",
  },
  {
    id: "chat",
    target: "[data-tour='tab-chat']",
    title: "AI Chat Interface",
    description:
      "Have a conversation with your DevOps AI. Ask questions, request deployments, check status — all in natural language powered by Gemini 2.5 Pro.",
    position: "bottom",
  },
  {
    id: "console",
    target: "[data-tour='tab-console']",
    title: "Command Console",
    description:
      "Type deployment commands in natural language. The AI parses them into structured plans with confidence scores and risk assessment.",
    position: "bottom",
  },
  {
    id: "analytics",
    target: "[data-tour='analytics']",
    title: "Deployment Analytics",
    description:
      "Track deployment metrics — success rates, average deploy time, rollback counts, and trends over time with interactive charts.",
    position: "top",
  },
  {
    id: "history",
    target: "[data-tour='history']",
    title: "Execution History",
    description:
      "View all past deployments with their status, logs, and AI-generated post-mortem summaries for failed deployments.",
    position: "top",
  },
  {
    id: "done",
    target: "[data-tour='stat-grid']",
    title: "You're All Set!",
    description:
      "Start by registering a project, then try the AI chat or command console to deploy. Every plan requires your approval before execution.",
    position: "bottom",
  },
];
