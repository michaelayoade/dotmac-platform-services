/**
 * Theme Provider Component
 *
 * Manages portal theme switching and provides theme context to all
 * styled components. Handles theme persistence, dark mode, and animations.
 */

import * as React from 'react';

import { cn } from '../lib/utils';

/**
 * Portal theme types
 */
export type PortalTheme = 'admin' | 'customer' | 'reseller';
export type ColorScheme = 'light' | 'dark' | 'system';

/**
 * Theme context value
 */
interface ThemeContextValue {
  portal: PortalTheme;
  colorScheme: ColorScheme;
  isDark: boolean;
  setPortal: (portal: PortalTheme) => void;
  setColorScheme: (scheme: ColorScheme) => void;
  toggleColorScheme: () => void;
}

/**
 * Theme context
 */
const ThemeContext = React.createContext<ThemeContextValue | undefined>(undefined);

/**
 * Theme provider props
 */
export interface ThemeProviderProps {
  children: React.ReactNode;
  /**
   * Default portal theme
   */
  defaultPortal?: PortalTheme;
  /**
   * Default color scheme
   */
  defaultColorScheme?: ColorScheme;
  /**
   * Storage key for persisting theme
   */
  storageKey?: string;
  /**
   * Attribute to set on document element
   */
  attribute?: string;
  /**
   * Whether to disable theme transitions during changes
   */
  disableTransitionOnChange?: boolean;
  /**
   * Back-compat alias for defaultPortal used by apps
   */
  portal?: PortalTheme;
}

/**
 * Theme Provider Component
 *
 * Provides portal theme context and manages theme switching across the application.
 * Handles persistence, system preference detection, and smooth theme transitions.
 *
 * @example
 * ```tsx
 * function App() {
 *   return (
 *     <ThemeProvider defaultPortal="customer" defaultColorScheme="system">
 *       <CustomerPortalApp />
 *     </ThemeProvider>
 *   );
 * }
 *
 * // Or for admin portal
 * function AdminApp() {
 *   return (
 *     <ThemeProvider defaultPortal="admin" defaultColorScheme="dark">
 *       <AdminPortalApp />
 *     </ThemeProvider>
 *   );
 * }
 * ```
 */
export function ThemeProvider({
  children,
  defaultPortal = 'customer',
  defaultColorScheme = 'system',
  storageKey = 'dotmac-theme',
  disableTransitionOnChange = false,
  portal: portalProp,
}: ThemeProviderProps) {
  const [portal, setPortalState] = React.useState<PortalTheme>(portalProp ?? defaultPortal);
  const [colorScheme, setColorSchemeState] = React.useState<ColorScheme>(defaultColorScheme);
  const [isDark, setIsDark] = React.useState(false);

  // Initialize theme from storage and system preferences
  React.useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const { portal: storedPortal, colorScheme: storedScheme } = JSON.parse(stored);
        if (storedPortal) {
          setPortalState(storedPortal);
        }
        if (storedScheme) {
          setColorSchemeState(storedScheme);
        }
      }
    } catch {
      // Ignore storage errors
    }
  }, [storageKey]);

  // Handle system color scheme detection
  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const updateSystemScheme = () => {
      if (colorScheme === 'system') {
        setIsDark(mediaQuery.matches);
      }
    };

    updateSystemScheme();
    mediaQuery.addEventListener('change', updateSystemScheme);

    return () => mediaQuery.removeEventListener('change', updateSystemScheme);
  }, [colorScheme]);

  // Update isDark when colorScheme changes
  React.useEffect(() => {
    if (colorScheme === 'system') {
      setIsDark(window.matchMedia('(prefers-color-scheme: dark)').matches);
    } else {
      setIsDark(colorScheme === 'dark');
    }
  }, [colorScheme]);

  // Apply theme classes to document
  React.useEffect(() => {
    const root = window.document.documentElement;

    // Disable transitions during theme change
    if (disableTransitionOnChange) {
      root.classList.add('theme-transition-disabled');
    }

    // Remove existing portal classes
    root.classList.remove('admin-portal', 'customer-portal', 'reseller-portal');

    // Remove existing color scheme classes
    root.classList.remove('dark', 'light');

    // Add new classes
    root.classList.add(`${portal}-portal`);
    root.classList.add(isDark ? 'dark' : 'light');

    // Re-enable transitions
    if (disableTransitionOnChange) {
      setTimeout(() => {
        root.classList.remove('theme-transition-disabled');
      }, 0);
    }
  }, [portal, isDark, disableTransitionOnChange]);

  // Persist theme to storage
  React.useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify({ portal, colorScheme }));
    } catch {
      // Ignore storage errors
    }
  }, [portal, colorScheme, storageKey]);

  const setPortal = React.useCallback((newPortal: PortalTheme) => {
    setPortalState(newPortal);
  }, []);

  const setColorScheme = React.useCallback((newScheme: ColorScheme) => {
    setColorSchemeState(newScheme);
  }, []);

  const toggleColorScheme = React.useCallback(() => {
    if (colorScheme === 'system') {
      const systemIsDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setColorScheme(systemIsDark ? 'light' : 'dark');
    } else {
      setColorScheme(colorScheme === 'light' ? 'dark' : 'light');
    }
  }, [colorScheme, setColorScheme]);

  const value = React.useMemo(
    () => ({
      portal,
      colorScheme,
      isDark,
      setPortal,
      setColorScheme,
      toggleColorScheme,
    }),
    [portal, colorScheme, isDark, setPortal, setColorScheme, toggleColorScheme]
  );

  return (
    <ThemeContext.Provider value={value}>
      <div className={cn(`${portal}-portal`, isDark ? 'dark' : 'light')}>{children}</div>
    </ThemeContext.Provider>
  );
}

/**
 * Hook to use theme context
 */
export function useTheme() {
  const context = React.useContext(ThemeContext);

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}

/**
 * Theme Switcher Component
 */
export interface ThemeSwitcherProps {
  className?: string;
  showPortalSwitcher?: boolean;
  showColorSchemeSwitcher?: boolean;
}

/**
 * Theme Switcher Component
 *
 * Provides UI controls for switching between portal themes and color schemes.
 *
 * @example
 * ```tsx
 * // Full theme switcher
 * <ThemeSwitcher showPortalSwitcher showColorSchemeSwitcher />
 *
 * // Color scheme only
 * <ThemeSwitcher showColorSchemeSwitcher />
 * ```
 */
export function ThemeSwitcher({
  className,
  showPortalSwitcher = false,
  showColorSchemeSwitcher = true,
}: ThemeSwitcherProps) {
  const { portal, colorScheme, setPortal, toggleColorScheme } = useTheme();

  return (
    <div className={cn('flex items-center space-x-2', className)}>
      {showPortalSwitcher && (
        <select
          value={portal}
          onChange={(e) => setPortal(e.target.value as PortalTheme)}
          className='portal-switcher'
        >
          <option value='admin'>Admin Portal</option>
          <option value='customer'>Customer Portal</option>
          <option value='reseller'>Reseller Portal</option>
        </select>
      )}

      {showColorSchemeSwitcher && (
        <div className='flex items-center'>
          <button
            type='button'
            onClick={toggleColorScheme}
            onKeyDown={(e) => e.key === 'Enter' && toggleColorScheme()}
            className='theme-toggle'
            aria-label='Toggle theme'
          >
            {colorScheme === 'dark' ||
            (colorScheme === 'system' &&
              window.matchMedia('(prefers-color-scheme: dark)').matches) ? (
              <svg
                aria-label='icon'
                className='h-4 w-4'
                fill='none'
                stroke='currentColor'
                viewBox='0 0 24 24'
              >
                <title>Icon</title>
                <path
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth={2}
                  d='M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z'
                />
              </svg>
            ) : (
              <svg
                aria-label='icon'
                className='h-4 w-4'
                fill='none'
                stroke='currentColor'
                viewBox='0 0 24 24'
              >
                <title>Icon</title>
                <path
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth={2}
                  d='M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z'
                />
              </svg>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

ThemeProvider.displayName = 'ThemeProvider';
ThemeSwitcher.displayName = 'ThemeSwitcher';

export type { ThemeContextValue };
