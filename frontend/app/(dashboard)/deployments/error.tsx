"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ErrorFallback } from "@/components/shared/error-boundary";

export default function DeploymentsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    console.error("Deployments error:", error);
  }, [error]);

  return (
    <ErrorFallback
      error={error}
      onRetry={reset}
      onGoHome={() => router.replace("/deployments")}
      title="Error Loading Deployments"
      description="We couldn't load the deployment data. Please try again."
    />
  );
}
