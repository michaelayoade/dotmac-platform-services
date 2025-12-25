import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { getCurrentUserFromRequest } from "@/lib/auth/server";

export default async function AuthLayout({
  children,
}: {
  children: ReactNode;
}) {
  const user = await getCurrentUserFromRequest();

  // Redirect to dashboard if already logged in
  if (user) {
    redirect("/");
  }

  return <>{children}</>;
}
