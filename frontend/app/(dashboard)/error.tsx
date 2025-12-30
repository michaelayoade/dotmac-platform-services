"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ErrorFallback } from "@/components/shared/error-boundary";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  useEffect(() => {
    console.error("Dashboard error:", error);
  }, [error]);

  return (
    <ErrorFallback
      error={error}
      onRetry={reset}
      onGoHome={() => router.replace("/")}
      title="Dashboard Error"
      description="Something went wrong loading this page. Please try again."
    />
  );
}
