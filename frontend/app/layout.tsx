import type { Metadata } from "next";
import type { ReactNode } from "react";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import {
  ThemeProvider,
  ToastProvider,
  ToastViewport,
} from "@/lib/dotmac/core";
import { generateThemeScript } from "@dotmac/design-tokens";

import { QueryProvider } from "@/lib/providers/query-provider";
import { AuthProvider } from "@/lib/providers/auth-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "DotMac Platform",
    template: "%s | DotMac Platform",
  },
  description: "Multi-tenant SaaS Platform Administration",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${GeistSans.variable} ${GeistMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        {/* Inline script to prevent theme flash */}
        <script
          dangerouslySetInnerHTML={{ __html: generateThemeScript() }}
        />
      </head>
      <body className="min-h-screen bg-surface antialiased">
        <ThemeProvider
          defaultVariant="admin"
          manageColorScheme
          managePalette
        >
          <QueryProvider>
            <AuthProvider>
              <ToastProvider>
                {children}
                <ToastViewport />
              </ToastProvider>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
