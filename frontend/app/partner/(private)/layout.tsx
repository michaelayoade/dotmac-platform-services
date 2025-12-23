import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import type { ReactNode } from "react";

import { authOptions } from "@/lib/auth/config";
import { PortalShell } from "@/components/layout/portal-shell";
import { partnerPortalConfig } from "@/lib/config/partner-portal";

const ADMIN_ROLES = new Set(["admin", "platform_admin", "super_admin"]);

export default async function PartnerPrivateLayout({
  children,
}: {
  children: ReactNode;
}) {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/partner/login");
  }

  const roles = session.user?.roles ?? [];
  const permissions = session.user?.permissions ?? [];
  const hasPartnerRole =
    roles.some((role) => role.startsWith("partner_")) ||
    (session.user?.role ? session.user.role.startsWith("partner_") : false);
  const isAdminRole =
    roles.some((role) => ADMIN_ROLES.has(role)) ||
    (session.user?.role ? ADMIN_ROLES.has(session.user.role) : false);
  const hasPartnerPermission = permissions.some((permission) =>
    permission.startsWith("partner.")
  );
  const hasPartnerContext = Boolean(session.user?.partnerId);
  const isPlatformAdmin = Boolean(session.user?.isPlatformAdmin) || isAdminRole;

  if (!isPlatformAdmin && !hasPartnerContext && !hasPartnerRole && !hasPartnerPermission) {
    redirect("/partner/login?error=unauthorized");
  }

  return (
    <PortalShell session={session} config={partnerPortalConfig}>
      {children}
    </PortalShell>
  );
}
