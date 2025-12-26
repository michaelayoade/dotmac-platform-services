/**
 * @dotmac/design-tokens - Theme Storage
 *
 * Shared storage key and utilities for theme persistence.
 * Used by both the ThemeProvider and the inline flash-prevention script.
 */

/** localStorage key for theme persistence (matches Zustand persist config) */
export const THEME_STORAGE_KEY = "dotmac-theme";

export interface StoredThemeState {
  theme: "light" | "dark" | "system";
}

/**
 * Get stored theme preference from localStorage
 * Returns null if not available (SSR or no stored preference)
 */
export function getStoredTheme(): StoredThemeState | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (!stored) return null;
    const parsed = JSON.parse(stored);
    // Zustand persist wraps state in { state: { ... } }
    return { theme: parsed.state?.theme || "system" };
  } catch {
    return null;
  }
}

/**
 * Resolve theme preference to actual light/dark value
 */
export function resolveThemePreference(
  preference: "light" | "dark" | "system"
): "light" | "dark" {
  if (preference === "system") {
    if (typeof window === "undefined") return "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return preference;
}

/**
 * Generate inline script for flash prevention
 *
 * This script runs before React hydration to set the correct theme class
 * immediately, preventing flash of wrong theme colors.
 *
 * Usage in layout.tsx:
 * ```tsx
 * <script dangerouslySetInnerHTML={{ __html: generateThemeScript() }} />
 * ```
 */
export function generateThemeScript(): string {
  return `(function(){try{var s=localStorage.getItem('${THEME_STORAGE_KEY}');var t='dark';if(s){var p=JSON.parse(s);var pref=p.state?.theme||'system';t=pref==='system'?window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light':pref}document.documentElement.classList.remove('light','dark');document.documentElement.classList.add(t);document.documentElement.style.colorScheme=t}catch(e){document.documentElement.classList.add('dark')}})();`;
}

/**
 * Readable version of the theme script (for debugging)
 */
export const themeScriptReadable = `
(function() {
  try {
    var stored = localStorage.getItem('${THEME_STORAGE_KEY}');
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
