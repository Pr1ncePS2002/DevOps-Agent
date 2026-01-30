import type { ExecutionStatus } from "./types";

export interface HistoryEntry {
  id: number;
  label: string;
  status: ExecutionStatus;
  summary: string;
  timestamp: string;
}

export const mockHistory: HistoryEntry[] = [
  {
    id: 4423,
    label: "Deploy api-edge to prod",
    status: "succeeded",
    summary: "Blue/green swap followed by synthetic probe validation.",
    timestamp: "12:22 UTC"
  },
  {
    id: 4422,
    label: "Rollback payments migration",
    status: "rolled_back",
    summary: "Policy guard triggered due to schema drift.",
    timestamp: "10:08 UTC"
  },
  {
    id: 4418,
    label: "Staging smoke pack",
    status: "failed",
    summary: "E2E suite timed out waiting for checkout pod.",
    timestamp: "Yesterday"
  }
];
