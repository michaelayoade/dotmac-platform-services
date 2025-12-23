import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
  setResolvedTheme: (resolvedTheme: ResolvedTheme) => void;
}

function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "system",
      resolvedTheme: "dark", // Default to dark, will be updated on mount

      setTheme: (theme: Theme) => {
        const resolvedTheme = theme === "system" ? getSystemTheme() : theme;
        set({ theme, resolvedTheme });
      },

      setResolvedTheme: (resolvedTheme: ResolvedTheme) => {
        set({ resolvedTheme });
      },
    }),
    {
      name: "dotmac-theme",
      partialize: (state) => ({ theme: state.theme }), // Only persist theme preference
    }
  )
);

// Helper to get resolved theme based on preference
export function resolveTheme(theme: Theme): ResolvedTheme {
  if (theme === "system") {
    return getSystemTheme();
  }
  return theme;
}
