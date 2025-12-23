import {
  LayoutDashboard,
  Users,
  CreditCard,
  BarChart3,
  Settings,
  Building2,
} from "lucide-react";
import type { PortalConfig } from "@/components/layout";

export const tenantPortalConfig: PortalConfig = {
  title: "My Organization",
  subtitle: "DotMac Platform",
  logoIcon: Building2,
  baseHref: "/portal",
  helpHref: "/portal/help",
  navigation: [
    {
      items: [
        {
          label: "Dashboard",
          href: "/portal",
          icon: LayoutDashboard,
        },
      ],
    },
    {
      title: "Organization",
      items: [
        {
          label: "Team",
          href: "/portal/team",
          icon: Users,
        },
        {
          label: "Billing",
          href: "/portal/billing",
          icon: CreditCard,
        },
        {
          label: "Usage",
          href: "/portal/usage",
          icon: BarChart3,
        },
      ],
    },
    {
      title: "Account",
      items: [
        {
          label: "Settings",
          href: "/portal/settings",
          icon: Settings,
        },
      ],
    },
  ],
};
