'use client';

import React, { useState } from 'react';
import { useTenant, Tenant } from '@/lib/contexts/tenant-context';
import { ChevronDown, Building2, Check, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export function TenantSelector() {
  const { currentTenant, availableTenants, setTenant, isLoading } = useTenant();
  const [isOpen, setIsOpen] = useState(false);

  const handleTenantChange = (tenant: Tenant) => {
    setTenant(tenant);
    setIsOpen(false);
    // Reload the page to apply the new tenant context
    window.location.reload();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/10 text-green-500 dark:bg-green-500/20';
      case 'trial':
        return 'bg-blue-500/10 text-blue-500 dark:bg-blue-500/20';
      case 'suspended':
        return 'bg-orange-500/10 text-orange-500 dark:bg-orange-500/20';
      case 'cancelled':
      case 'expired':
        return 'bg-red-500/10 text-red-500 dark:bg-red-500/20';
      default:
        return 'bg-slate-500/10 text-slate-500 dark:bg-slate-500/20';
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md hover:bg-slate-50 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Building2 className="h-4 w-4" />
        )}
        <span className="max-w-[150px] truncate">{currentTenant?.name || 'Select Tenant'}</span>
        <ChevronDown className="h-4 w-4" />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute z-20 mt-2 w-72 rounded-md shadow-lg bg-white dark:bg-slate-800 ring-1 ring-black dark:ring-slate-700 ring-opacity-5">
            <div className="py-1" role="menu">
              {availableTenants.length === 0 ? (
                <div className="px-4 py-3 text-sm text-slate-500 dark:text-slate-400 text-center">
                  No tenants available
                </div>
              ) : (
                availableTenants.map((tenant) => (
                  <button
                    key={tenant.id}
                    onClick={() => handleTenantChange(tenant)}
                    className="flex items-start justify-between w-full px-4 py-3 text-sm text-slate-900 dark:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                    role="menuitem"
                  >
                    <div className="flex-1 text-left">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{tenant.name}</span>
                        {currentTenant?.id === tenant.id && (
                          <Check className="h-4 w-4 text-sky-500" />
                        )}
                      </div>
                      {tenant.slug && (
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          @{tenant.slug}
                        </div>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <Badge
                          className={`text-xs px-1.5 py-0.5 ${getStatusColor(tenant.status)}`}
                        >
                          {tenant.status}
                        </Badge>
                        <Badge variant="outline" className="text-xs px-1.5 py-0.5">
                          {tenant.plan}
                        </Badge>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function TenantBadge() {
  const { currentTenant } = useTenant();

  if (!currentTenant) return null;

  return (
    <div className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-indigo-100 text-indigo-800 rounded-full">
      <Building2 className="h-3 w-3" />
      <span>{currentTenant.name}</span>
    </div>
  );
}