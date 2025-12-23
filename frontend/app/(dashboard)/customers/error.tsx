"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/shared/error-boundary";

export default function CustomersError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Customers error:", error);
  }, [error]);

  return (
    <ErrorFallback
      error={error}
      onRetry={reset}
      onGoHome={() => (window.location.href = "/customers")}
      title="Error Loading Customers"
      description="We couldn't load the customer data. Please try again."
    />
  );
}
