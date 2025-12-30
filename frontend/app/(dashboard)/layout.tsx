import { redirect } from "next/navigation";
import type { ReactNode } from "react";

export const dynamic = "force-dynamic";

import { DashboardShell } from "@/components/layout/dashboard-shell";
import { getCurrentUserFromRequest } from "@/lib/auth/server";

export default async function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  const user = await getCurrentUserFromRequest();

  if (!user) {
    redirect("/login");
  }

  return <DashboardShell user={user}>{children}</DashboardShell>;
}
