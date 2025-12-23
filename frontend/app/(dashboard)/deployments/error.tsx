"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/shared/error-boundary";

export default function DeploymentsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Deployments error:", error);
  }, [error]);

  return (
    <ErrorFallback
      error={error}
      onRetry={reset}
      onGoHome={() => (window.location.href = "/deployments")}
      title="Error Loading Deployments"
      description="We couldn't load the deployment data. Please try again."
    />
  );
}
