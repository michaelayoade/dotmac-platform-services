'use client';

import { ReactNode, useState } from 'react';
import { ThemeProvider } from 'next-themes';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePathname } from 'next/navigation';
// import { UniversalProviders } from '@dotmac/providers';
// import { NotificationsProvider } from '@dotmac/notifications';
import { AppConfigProvider } from './AppConfigContext';
import { MSWProvider } from './MSWProvider';
import { platformConfig } from '@/lib/config';
import { TenantProvider } from '@/lib/contexts/tenant-context';
import { RBACProvider } from '@/contexts/RBACContext';
import { ToastContainer } from '@/components/ui/toast';

export function ClientProviders({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [queryClient] = useState(() => new QueryClient());

  const shouldWrapWithRBAC = pathname?.startsWith('/dashboard');

  const appProviders = (
    <AppConfigProvider value={platformConfig}>
      {children}
      <ToastContainer />
    </AppConfigProvider>
  );

  return (
    <MSWProvider>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <QueryClientProvider client={queryClient}>
          <TenantProvider>
            {shouldWrapWithRBAC ? (
              <RBACProvider>
                {appProviders}
              </RBACProvider>
            ) : (
              appProviders
            )}
          </TenantProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </MSWProvider>
  );
}
