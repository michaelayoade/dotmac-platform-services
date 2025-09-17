import './globals.css';
import type { Metadata } from 'next';
import { ReactNode } from 'react';

import { ClientProviders } from '@/providers/ClientProviders';

export const metadata: Metadata = {
  title: 'DotMac Base App',
  description: 'Starter Next.js application pre-integrated with DotMac platform services.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
