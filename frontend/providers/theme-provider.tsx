"use client";

import { useEffect, type ReactNode } from "react";
import { useThemeStore, resolveTheme, type Theme } from "@/lib/stores/theme-store";

interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
}

export function CustomThemeProvider({
  children,
  defaultTheme = "system",
}: ThemeProviderProps) {
  const { theme, setTheme, setResolvedTheme } = useThemeStore();

  // Initialize theme on mount
  useEffect(() => {
    // Get stored theme or use default
    const storedTheme = useThemeStore.getState().theme;
    const initialTheme = storedTheme || defaultTheme;

    // Set initial resolved theme
    const resolved = resolveTheme(initialTheme);
    setResolvedTheme(resolved);

    // Apply to document without transition on initial load
    applyTheme(resolved, false);
  }, [defaultTheme, setResolvedTheme]);

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent) => {
      const currentTheme = useThemeStore.getState().theme;
      if (currentTheme === "system") {
        const resolved = e.matches ? "dark" : "light";
        setResolvedTheme(resolved);
        applyTheme(resolved);
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [setResolvedTheme]);

  // Apply theme whenever it changes
  useEffect(() => {
    const resolved = resolveTheme(theme);
    setResolvedTheme(resolved);
    applyTheme(resolved);
  }, [theme, setResolvedTheme]);

  return <>{children}</>;
}

function applyTheme(theme: "light" | "dark", withTransition = true) {
  const root = document.documentElement;

  // Enable transition class for smooth theme change
  if (withTransition) {
    root.classList.add("theme-transition");
  }

  // Remove both classes first
  root.classList.remove("light", "dark");

  // Add the appropriate class
  root.classList.add(theme);

  // Update color-scheme for native elements
  root.style.colorScheme = theme;

  // Remove transition class after animation completes
  if (withTransition) {
    setTimeout(() => {
      root.classList.remove("theme-transition");
    }, 300);
  }
}

// Inline script to prevent flash of wrong theme
// This should be added to the <head> of the document
export const themeScript = `
  (function() {
    try {
      var stored = localStorage.getItem('dotmac-theme');
      var theme = 'dark';

      if (stored) {
        var parsed = JSON.parse(stored);
        var preference = parsed.state?.theme || 'system';

        if (preference === 'system') {
          theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        } else {
          theme = preference;
        }
      }

      document.documentElement.classList.remove('light', 'dark');
      document.documentElement.classList.add(theme);
      document.documentElement.style.colorScheme = theme;
    } catch (e) {
      document.documentElement.classList.add('dark');
    }
  })();
`;
