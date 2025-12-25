/**
 * Tenant Hook
 *
 * Multi-tenant context management
 */

"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useCallback, useEffect } from "react";
import { useCurrentUser } from "@/lib/hooks/api/use-auth";

interface Tenant {
  id: string;
  name: string;
  slug: string;
  status: "active" | "suspended" | "trial";
  plan: string;
}

interface TenantState {
  currentTenantId: string | null;
  tenants: Tenant[];
  setCurrentTenantId: (id: string) => void;
  setTenants: (tenants: Tenant[]) => void;
}

const useTenantStore = create<TenantState>()(
  persist(
    (set) => ({
      currentTenantId: null,
      tenants: [],
      setCurrentTenantId: (id) => set({ currentTenantId: id }),
      setTenants: (tenants) => set({ tenants }),
    }),
    {
      name: "dotmac-tenant",
    }
  )
);

interface UseTenantReturn {
  currentTenant: Tenant | null;
  tenants: Tenant[];
  switchTenant: (tenantId: string) => void;
  isLoading: boolean;
}

export function useTenant(): UseTenantReturn {
  const { data: user, isLoading } = useCurrentUser();
  const { currentTenantId, tenants, setCurrentTenantId, setTenants } =
    useTenantStore();

  // Sync tenant context from current user
  useEffect(() => {
    const activeOrg = user?.activeOrganization;
    if (activeOrg?.id && activeOrg?.name) {
      const derivedTenant: Tenant = {
        id: activeOrg.id,
        name: activeOrg.name,
        slug: activeOrg.slug ?? activeOrg.id,
        status: "active",
        plan: "standard",
      };
      setTenants([derivedTenant]);
      if (!currentTenantId) {
        setCurrentTenantId(derivedTenant.id);
      }
      return;
    }

    if (user?.tenantId) {
      const fallbackTenant: Tenant = {
        id: user.tenantId,
        name: "Tenant",
        slug: user.tenantId,
        status: "active",
        plan: "standard",
      };
      setTenants([fallbackTenant]);
      if (!currentTenantId) {
        setCurrentTenantId(fallbackTenant.id);
      }
    }
  }, [user, currentTenantId, setTenants, setCurrentTenantId]);

  const currentTenant =
    tenants.find((t) => t.id === currentTenantId) || null;

  const switchTenant = useCallback(
    (tenantId: string) => {
      const tenant = tenants.find((t) => t.id === tenantId);
      if (tenant) {
        setCurrentTenantId(tenantId);
        // Optionally trigger a page refresh or data refetch
        window.location.reload();
      }
    },
    [tenants, setCurrentTenantId]
  );

  return {
    currentTenant,
    tenants,
    switchTenant,
    isLoading,
  };
}

/**
 * Get current tenant ID for server components
 */
export async function getCurrentTenantId(): Promise<string | null> {
  // This would read from cookies or session on the server
  return null;
}
