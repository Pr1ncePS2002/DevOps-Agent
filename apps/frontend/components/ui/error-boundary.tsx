"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6 text-center">
          <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-3" />
          <h3 className="text-sm font-medium text-red-300 mb-1">
            {this.props.fallbackTitle ?? "Something went wrong"}
          </h3>
          <p className="text-xs text-white/40 mb-4">
            {this.state.error?.message ?? "An unexpected error occurred"}
          </p>
          <button
            onClick={this.handleRetry}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-white/60 hover:text-white transition"
          >
            <RotateCcw className="h-3 w-3" />
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
