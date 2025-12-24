/**
 * Tenant Hook
 *
 * Multi-tenant context management
 */

"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useSession } from "next-auth/react";
import { useCallback, useEffect } from "react";

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
  const { data: session, status } = useSession();
  const { currentTenantId, tenants, setCurrentTenantId, setTenants } =
    useTenantStore();

  // Sync tenants from session
  useEffect(() => {
    if (session?.user?.tenants) {
      setTenants(session.user.tenants as Tenant[]);

      // Set default tenant if none selected
      if (!currentTenantId && session.user.tenants.length > 0) {
        setCurrentTenantId((session.user.tenants[0] as Tenant).id);
      }
    }
  }, [session?.user?.tenants, currentTenantId, setTenants, setCurrentTenantId]);

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
    isLoading: status === "loading",
  };
}

/**
 * Get current tenant ID for server components
 */
export async function getCurrentTenantId(): Promise<string | null> {
  // This would read from cookies or session on the server
  return null;
}
