"use client";

import { SessionProvider } from "next-auth/react";
import { type ReactNode } from "react";

export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <SessionProvider
      // Refetch session every 5 minutes
      refetchInterval={5 * 60}
      // Refetch when window gains focus
      refetchOnWindowFocus={true}
    >
      {children}
    </SessionProvider>
  );
}
