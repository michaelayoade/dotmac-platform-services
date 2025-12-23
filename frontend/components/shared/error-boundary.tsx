"use client";

import { Component, type ReactNode, type ErrorInfo } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "@dotmac/core";
import { ApiClientError } from "@/lib/api/errors";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  handleGoHome = () => {
    window.location.href = "/";
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorFallback
          error={this.state.error}
          onRetry={this.handleRetry}
          onGoHome={this.handleGoHome}
        />
      );
    }

    return this.props.children;
  }
}

// Error fallback UI component
interface ErrorFallbackProps {
  error: Error | null;
  onRetry?: () => void;
  onGoHome?: () => void;
  title?: string;
  description?: string;
}

export function ErrorFallback({
  error,
  onRetry,
  onGoHome,
  title,
  description,
}: ErrorFallbackProps) {
  const isApiError = error instanceof ApiClientError;
  const errorTitle =
    title ||
    (isApiError ? "Something went wrong" : "An unexpected error occurred");
  const errorDescription =
    description ||
    (isApiError
      ? (error as ApiClientError).getUserMessage()
      : error?.message || "Please try again or contact support if the problem persists.");

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
      {/* Icon */}
      <div className="w-16 h-16 rounded-full bg-status-error/15 flex items-center justify-center mb-6">
        <AlertTriangle className="w-8 h-8 text-status-error" />
      </div>

      {/* Content */}
      <h2 className="text-xl font-semibold text-text-primary mb-2">
        {errorTitle}
      </h2>
      <p className="text-sm text-text-muted max-w-md mb-6">{errorDescription}</p>

      {/* Error details (development only) */}
      {process.env.NODE_ENV === "development" && error && (
        <div className="w-full max-w-lg mb-6">
          <details className="text-left">
            <summary className="text-sm text-text-muted cursor-pointer hover:text-text-secondary">
              Technical details
            </summary>
            <pre className="mt-2 p-4 bg-surface-overlay rounded-lg text-xs text-text-secondary overflow-auto max-h-40">
              {error.stack || error.message}
            </pre>
          </details>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-3">
        {onGoHome && (
          <Button variant="outline" onClick={onGoHome}>
            <Home className="w-4 h-4 mr-2" />
            Go Home
          </Button>
        )}
        {onRetry && (
          <Button onClick={onRetry}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        )}
      </div>
    </div>
  );
}

// Query error fallback for React Query
interface QueryErrorFallbackProps {
  error: Error;
  resetErrorBoundary?: () => void;
}

export function QueryErrorFallback({
  error,
  resetErrorBoundary,
}: QueryErrorFallbackProps) {
  const isApiError = error instanceof ApiClientError;

  // Handle specific error types
  if (isApiError) {
    const apiError = error as ApiClientError;

    // Auth errors - redirect to login
    if (apiError.isAuthError()) {
      return (
        <ErrorFallback
          error={error}
          title="Session Expired"
          description="Your session has expired. Please sign in again."
          onGoHome={() => (window.location.href = "/login")}
        />
      );
    }

    // Rate limit errors
    if (apiError.isRateLimitError()) {
      return (
        <ErrorFallback
          error={error}
          title="Too Many Requests"
          description="Please wait a moment before trying again."
          onRetry={resetErrorBoundary}
        />
      );
    }
  }

  return (
    <ErrorFallback
      error={error}
      onRetry={resetErrorBoundary}
      onGoHome={() => (window.location.href = "/")}
    />
  );
}

// Inline error display for smaller components
interface InlineErrorProps {
  error: Error | null;
  onRetry?: () => void;
}

export function InlineError({ error, onRetry }: InlineErrorProps) {
  if (!error) return null;

  const isApiError = error instanceof ApiClientError;
  const message = isApiError
    ? (error as ApiClientError).getUserMessage()
    : error.message || "An error occurred";

  return (
    <div className="flex items-center justify-between p-4 rounded-lg bg-status-error/10 border border-status-error/30">
      <div className="flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 text-status-error flex-shrink-0" />
        <p className="text-sm text-status-error">{message}</p>
      </div>
      {onRetry && (
        <Button variant="ghost" size="sm" onClick={onRetry}>
          <RefreshCw className="w-4 h-4" />
        </Button>
      )}
    </div>
  );
}
