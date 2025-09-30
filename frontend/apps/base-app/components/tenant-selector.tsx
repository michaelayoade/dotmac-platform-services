'use client';

import React, { useState } from 'react';
import { useTenant, Tenant } from '@/lib/contexts/tenant-context';
import { ChevronDown, Building2, Check } from 'lucide-react';

// Sample tenants for demonstration - in production, this would come from an API
const AVAILABLE_TENANTS: Tenant[] = [
  { id: 'default-tenant', name: 'Default Tenant' },
  { id: 'acme-corp', name: 'Acme Corporation' },
  { id: 'tech-startup', name: 'Tech Startup Inc' },
  { id: 'enterprise-co', name: 'Enterprise Co' },
];

export function TenantSelector() {
  const { currentTenant, setTenant } = useTenant();
  const [isOpen, setIsOpen] = useState(false);

  const handleTenantChange = (tenant: Tenant) => {
    setTenant(tenant);
    setIsOpen(false);
    // Reload the page to apply the new tenant context
    window.location.reload();
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        <Building2 className="h-4 w-4" />
        <span>{currentTenant?.name || 'Select Tenant'}</span>
        <ChevronDown className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5">
          <div className="py-1" role="menu">
            {AVAILABLE_TENANTS.map((tenant) => (
              <button
                key={tenant.id}
                onClick={() => handleTenantChange(tenant)}
                className="flex items-center justify-between w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                role="menuitem"
              >
                <span>{tenant.name}</span>
                {currentTenant?.id === tenant.id && (
                  <Check className="h-4 w-4 text-indigo-600" />
                )}
              </button>
            ))}
          </div>
        </div>
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