'use client';

import { ReactNode, useState } from 'react';
import { ThemeProvider } from 'next-themes';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
// import { UniversalProviders } from '@dotmac/providers';
// import { NotificationsProvider } from '@dotmac/notifications';
import { AppConfigProvider } from './AppConfigContext';
import { platformConfig } from '@/lib/config';

export function ClientProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>
        <AppConfigProvider value={platformConfig}>
          {children}
        </AppConfigProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
