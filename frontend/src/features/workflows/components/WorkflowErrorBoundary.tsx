"use client";

import React, { Component, ReactNode } from "react";
import { Button } from "@heroui/button";
import { RefreshCw, AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class WorkflowErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Workflow Error Boundary caught an error:", error, errorInfo);

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to error tracking service (Sentry, etc.)
    // if (window.Sentry) {
    //   window.Sentry.captureException(error, {
    //     contexts: { errorBoundary: errorInfo }
    //   });
    // }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="flex flex-col items-center justify-center space-y-4 py-12">
          <div className="flex items-center space-x-2 text-red-500">
            <AlertTriangle className="h-6 w-6" />
            <h3 className="text-lg font-medium">Workflow Error</h3>
          </div>

          <div className="space-y-2 text-center">
            <p className="max-w-md text-foreground-400">
              Something went wrong with the workflow component. Please try
              refreshing or contact support if this persists.
            </p>

            {this.state.error && (
              <details className="mt-4 text-xs text-foreground-300">
                <summary className="cursor-pointer hover:text-foreground-200">
                  Error Details
                </summary>
                <pre className="mt-2 max-w-md overflow-auto rounded bg-zinc-800 p-2 text-left">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
          </div>

          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="flat"
              onPress={this.handleRetry}
              startContent={<RefreshCw className="h-4 w-4" />}
            >
              Try Again
            </Button>

            <Button
              size="sm"
              variant="flat"
              onPress={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook version for functional components
export const useWorkflowErrorBoundary = () => {
  return (error: Error) => {
    throw error;
  };
};
