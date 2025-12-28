import {
  LayoutDashboard,
  Users,
  Users2,
  HandCoins,
  FileText,
  Settings,
  UserPlus,
  Handshake,
} from "lucide-react";
import type { PortalConfig } from "@/components/layout";

export const partnerPortalConfig: PortalConfig = {
  title: "Partner Portal",
  subtitle: "DotMac",
  logoIcon: Handshake,
  baseHref: "/partner",
  helpHref: "/partner/help",
  navigation: [
    {
      items: [
        {
          label: "Dashboard",
          href: "/partner",
          icon: LayoutDashboard,
        },
      ],
    },
    {
      title: "Business",
      items: [
        {
          label: "Referrals",
          href: "/partner/referrals",
          icon: UserPlus,
        },
        {
          label: "Tenants",
          href: "/partner/tenants",
          icon: Users,
        },
        {
          label: "Commissions",
          href: "/partner/commissions",
          icon: HandCoins,
        },
        {
          label: "Statements",
          href: "/partner/statements",
          icon: FileText,
        },
      ],
    },
    {
      title: "Account",
      items: [
        {
          label: "Team",
          href: "/partner/team",
          icon: Users2,
        },
        {
          label: "Settings",
          href: "/partner/settings",
          icon: Settings,
        },
      ],
    },
  ],
};
