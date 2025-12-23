import type { Metadata } from "next";
import type { ReactNode } from "react";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { ThemeProvider } from "@/lib/dotmac/design-tokens";
import { ToastProvider, ToastViewport } from "@/lib/dotmac/core";

import { QueryProvider } from "@/lib/providers/query-provider";
import { AuthProvider } from "@/lib/providers/auth-provider";
import { CustomThemeProvider, themeScript } from "@/providers/theme-provider";

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
          dangerouslySetInnerHTML={{ __html: themeScript }}
        />
      </head>
      <body className="min-h-screen bg-surface antialiased">
        <ThemeProvider defaultVariant="admin">
          <CustomThemeProvider>
            <QueryProvider>
              <AuthProvider>
                <ToastProvider>
                  {children}
                  <ToastViewport />
                </ToastProvider>
              </AuthProvider>
            </QueryProvider>
          </CustomThemeProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
