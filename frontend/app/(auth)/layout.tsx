import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { getCurrentUserFromRequest } from "@/lib/auth/server";

export default async function AuthLayout({
  children,
}: {
  children: ReactNode;
}) {
  const user = await getCurrentUserFromRequest();
  const isTestMode =
    process.env.PLAYWRIGHT_TEST_MODE === "true" ||
    process.env.NEXT_PUBLIC_TEST_MODE === "true";

  // Redirect to dashboard if already logged in
  if (user && !isTestMode) {
    redirect("/");
  }

  return <>{children}</>;
}
