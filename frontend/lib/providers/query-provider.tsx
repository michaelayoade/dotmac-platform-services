"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState, Component, type ReactNode } from "react";

// Error boundary for query-related errors
class QueryErrorBoundary extends Component<
  { children: ReactNode; fallback?: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Query provider error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="min-h-screen flex items-center justify-center bg-surface">
            <div className="text-center space-y-4 p-8">
              <h1 className="text-xl font-semibold text-text-primary">
                Something went wrong
              </h1>
              <p className="text-text-secondary">
                Please refresh the page to try again.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-accent text-text-inverse rounded-md hover:bg-accent/90"
              >
                Refresh page
              </button>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Disable refetching on window focus for less aggressive updates
            refetchOnWindowFocus: false,
            // Keep data fresh for 30 seconds
            staleTime: 30 * 1000,
            // Retry failed requests once
            retry: 1,
            // Retry after 1 second
            retryDelay: 1000,
          },
          mutations: {
            // Retry mutations once on failure
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryErrorBoundary>
      <QueryClientProvider client={queryClient}>
        {children}
        {process.env.NODE_ENV === "development" && (
          <ReactQueryDevtools initialIsOpen={false} position="bottom" />
        )}
      </QueryClientProvider>
    </QueryErrorBoundary>
  );
}
