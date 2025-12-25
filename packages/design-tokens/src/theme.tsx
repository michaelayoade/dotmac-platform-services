/**
 * @dotmac/design-tokens - Theme System
 *
 * Unified theme configuration combining all tokens
 * ThemeProvider bridge for downstream apps
 */

"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
  type ReactNode,
} from "react";

import {
  colors,
  portalColors,
  semanticColors,
  statusColors,
  gradients,
  generateColorScale,
  type PortalVariant,
  type PortalColorScheme,
  type ColorScale,
} from "./colors";
import { duration, easing, animations, portalMotion } from "./motion";
import { shadows, focusRing, componentShadows } from "./shadows";
import { spacing, semanticSpacing, portalSpacing, borderRadius, zIndex } from "./spacing";
import { fontFamily, fontSize, fontWeight, textStyles, portalTypography } from "./typography";

// ============================================================================
// Theme Configuration Types
// ============================================================================

export interface BrandConfig {
  name: string;
  primaryColor: string;
  accentColor?: string;
  logoUrl?: string;
  faviconUrl?: string;
  fontFamily?: string[];
  customCss?: string;
}

export interface ThemeConfig {
  variant: PortalVariant;
  density: "compact" | "comfortable" | "spacious";
  colorScheme: "light" | "dark" | "system";
  highContrast: boolean;
  reducedMotion: boolean;
  brand?: BrandConfig;
}

export interface FontFamily {
  sans: readonly string[] | string[];
  serif: readonly string[] | string[];
  mono: readonly string[] | string[];
}

export interface Theme {
  colors: {
    primary: ColorScale;
    secondary: ColorScale;
    neutral: ColorScale;
    success: ColorScale;
    warning: ColorScale;
    error: ColorScale;
    accent: string;
    background: string;
    surface: string;
    text: string;
  };
  typography: {
    fontFamily: FontFamily;
    fontSize: typeof fontSize;
    fontWeight: typeof fontWeight;
    textStyles: typeof textStyles;
  };
  spacing: typeof spacing;
  semanticSpacing: typeof semanticSpacing;
  borderRadius: typeof borderRadius;
  shadows: typeof shadows;
  focusRing: typeof focusRing;
  componentShadows: typeof componentShadows;
  zIndex: typeof zIndex;
  motion: {
    duration: typeof duration;
    easing: typeof easing;
    animations: typeof animations;
  };
}

// ============================================================================
// Default Theme Configuration
// ============================================================================

const defaultConfig: ThemeConfig = {
  variant: "admin",
  density: "comfortable",
  colorScheme: "light",
  highContrast: false,
  reducedMotion: false,
};

// ============================================================================
// Theme Builder
// ============================================================================

export function buildTheme(config: ThemeConfig): Theme {
  const portalScheme = portalColors[config.variant];
  const brandPrimary = config.brand?.primaryColor
    ? generateColorScale(config.brand.primaryColor)
    : portalScheme.primary;

  return {
    colors: {
      primary: brandPrimary,
      secondary: colors.secondary,
      neutral: colors.neutral,
      success: colors.network,
      warning: colors.alert,
      error: colors.critical,
      accent: portalScheme.accent,
      background: portalScheme.background,
      surface: portalScheme.surface,
      text: portalScheme.text,
    },
    typography: {
      fontFamily: config.brand?.fontFamily
        ? { ...fontFamily, sans: config.brand.fontFamily as unknown as typeof fontFamily.sans }
        : fontFamily,
      fontSize,
      fontWeight,
      textStyles,
    },
    spacing,
    semanticSpacing,
    borderRadius,
    shadows,
    focusRing,
    componentShadows,
    zIndex,
    motion: {
      duration,
      easing,
      animations,
    },
  };
}

// ============================================================================
// Theme Context
// ============================================================================

interface ThemeContextValue {
  config: ThemeConfig;
  theme: Theme;
  portalScheme: PortalColorScheme;
  /** The actual resolved color scheme (light or dark), accounting for system preference */
  resolvedColorScheme: "light" | "dark";
  /** Whether dark mode is currently active */
  isDarkMode: boolean;
  updateConfig: (updates: Partial<ThemeConfig>) => void;
  setVariant: (variant: PortalVariant) => void;
  setColorScheme: (scheme: "light" | "dark" | "system") => void;
  setDensity: (density: "compact" | "comfortable" | "spacious") => void;
  getCSSVariables: () => Record<string, string>;
  getThemeClasses: () => string;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

// ============================================================================
// Theme Provider
// ============================================================================

export interface ThemeProviderProps {
  children: ReactNode;
  defaultVariant?: PortalVariant;
  defaultColorScheme?: "light" | "dark" | "system";
  defaultDensity?: "compact" | "comfortable" | "spacious";
  brand?: BrandConfig;
  configEndpoint?: string;
  tenantId?: string;
}

export function ThemeProvider({
  children,
  defaultVariant = "admin",
  defaultColorScheme = "light",
  defaultDensity = "comfortable",
  brand,
  configEndpoint,
  tenantId,
}: ThemeProviderProps) {
  const [config, setConfig] = useState<ThemeConfig>({
    ...defaultConfig,
    variant: defaultVariant,
    colorScheme: defaultColorScheme,
    density: defaultDensity,
    brand,
  });
  const customCssRef = useRef<HTMLStyleElement | null>(null);

  // Track the resolved color scheme (light/dark) when system is selected
  const [resolvedColorScheme, setResolvedColorScheme] = useState<"light" | "dark">("light");

  // Detect and respond to system color scheme preference
  useEffect(() => {
    if (config.colorScheme !== "system") {
      // If not system, use the explicit setting
      setResolvedColorScheme(config.colorScheme === "dark" ? "dark" : "light");
      return;
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
      const isDark = e.matches;
      setResolvedColorScheme(isDark ? "dark" : "light");

      // Apply dark class to document
      if (isDark) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    };

    // Initial check
    handleChange(mediaQuery);

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [config.colorScheme]);

  // Apply color scheme class to document when it changes
  useEffect(() => {
    if (config.colorScheme === "dark" || (config.colorScheme === "system" && resolvedColorScheme === "dark")) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [config.colorScheme, resolvedColorScheme]);

  // Detect reduced motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handleChange = () => {
      setConfig((prev) => ({ ...prev, reducedMotion: mediaQuery.matches }));
    };

    handleChange();
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  // Load remote theme configuration
  useEffect(() => {
    if (!configEndpoint) return;

    const loadRemoteTheme = async () => {
      try {
        const url = new URL(configEndpoint);
        if (tenantId) url.searchParams.set("tenant", tenantId);
        url.searchParams.set("portal", config.variant);

        const response = await fetch(url.toString());
        const data = await response.json();

        if (data.success && data.theme) {
          setConfig((prev) => ({
            ...prev,
            brand: data.theme.brand,
          }));
        }
      } catch {
        // Silently fail, use default theme
      }
    };

    loadRemoteTheme();
  }, [configEndpoint, tenantId, config.variant]);

  const theme = useMemo(() => buildTheme(config), [config]);
  const portalScheme = portalColors[config.variant];

  const updateConfig = useCallback((updates: Partial<ThemeConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  }, []);

  const setVariant = useCallback((variant: PortalVariant) => {
    setConfig((prev) => ({ ...prev, variant }));
  }, []);

  const setColorScheme = useCallback((colorScheme: "light" | "dark" | "system") => {
    setConfig((prev) => ({ ...prev, colorScheme }));
  }, []);

  const setDensity = useCallback((density: "compact" | "comfortable" | "spacious") => {
    setConfig((prev) => ({ ...prev, density }));
  }, []);

  const getCSSVariables = useCallback((): Record<string, string> => {
    const vars: Record<string, string> = {};

    // Color variables
    Object.entries(theme.colors.primary).forEach(([shade, value]) => {
      vars[`--color-primary-${shade}`] = value;
    });
    Object.entries(theme.colors.neutral).forEach(([shade, value]) => {
      vars[`--color-neutral-${shade}`] = value;
    });

    vars["--color-accent"] = theme.colors.accent;
    vars["--color-background"] = theme.colors.background;
    vars["--color-surface"] = theme.colors.surface;
    vars["--color-text"] = theme.colors.text;

    // Typography variables
    vars["--font-family-sans"] = theme.typography.fontFamily.sans.join(", ");
    vars["--font-family-mono"] = theme.typography.fontFamily.mono.join(", ");

    // Spacing based on density
    const densitySpacing = portalSpacing[config.density];
    vars["--spacing-component"] = densitySpacing.componentPadding;
    vars["--spacing-card"] = densitySpacing.cardPadding;
    vars["--spacing-gap"] = densitySpacing.listItemGap;
    vars["--height-input"] = densitySpacing.inputHeight;
    vars["--height-button"] = densitySpacing.buttonHeight;

    // Motion variables
    const motionConfig = portalMotion[config.variant as keyof typeof portalMotion];
    if (motionConfig && !config.reducedMotion) {
      vars["--duration-default"] = duration[motionConfig.defaultDuration];
      vars["--easing-default"] = easing[motionConfig.defaultEasing];
    } else {
      vars["--duration-default"] = duration.instant;
      vars["--easing-default"] = easing.linear;
    }

    return vars;
  }, [theme, config]);

  const getThemeClasses = useCallback((): string => {
    const classes = [
      `theme-${config.variant}`,
      `density-${config.density}`,
      `color-${config.colorScheme}`,
    ];

    if (config.highContrast) classes.push("high-contrast");
    if (config.reducedMotion) classes.push("reduced-motion");

    return classes.join(" ");
  }, [config]);

  // Apply CSS variables to document root
  useEffect(() => {
    const root = document.documentElement;
    const vars = getCSSVariables();

    Object.entries(vars).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });

    return () => {
      // Clean up CSS variables
      Object.keys(vars).forEach((property) => {
        root.style.removeProperty(property);
      });
    };
  }, [getCSSVariables]);

  const customCss = config.brand?.customCss;

  useEffect(() => {
    if (!customCss) {
      if (customCssRef.current) {
        customCssRef.current.remove();
        customCssRef.current = null;
      }
      return;
    }

    if (!customCssRef.current) {
      const styleEl = document.createElement("style");
      styleEl.setAttribute("data-dotmac-theme", "custom");
      document.head.appendChild(styleEl);
      customCssRef.current = styleEl;
    }

    customCssRef.current.textContent = customCss;
  }, [customCss]);

  useEffect(() => {
    return () => {
      if (customCssRef.current) {
        customCssRef.current.remove();
        customCssRef.current = null;
      }
    };
  }, []);

  const isDarkMode = resolvedColorScheme === "dark";

  const value = useMemo<ThemeContextValue>(
    () => ({
      config,
      theme,
      portalScheme,
      resolvedColorScheme,
      isDarkMode,
      updateConfig,
      setVariant,
      setColorScheme,
      setDensity,
      getCSSVariables,
      getThemeClasses,
    }),
    [
      config,
      theme,
      portalScheme,
      resolvedColorScheme,
      isDarkMode,
      updateConfig,
      setVariant,
      setColorScheme,
      setDensity,
      getCSSVariables,
      getThemeClasses,
    ]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

// ============================================================================
// Theme Hook
// ============================================================================

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

// ============================================================================
// Utility Hooks
// ============================================================================

export function useThemeColors() {
  const { theme } = useTheme();
  return theme.colors;
}

export function useThemeSpacing() {
  const { theme, config } = useTheme();
  return {
    ...theme.spacing,
    density: portalSpacing[config.density],
  };
}

export function useThemeMotion() {
  const { theme, config } = useTheme();
  return {
    ...theme.motion,
    reducedMotion: config.reducedMotion,
  };
}

// ============================================================================
// Re-exports for convenience
// ============================================================================

export { colors, portalColors, semanticColors, statusColors, gradients };
export { fontFamily, fontSize, fontWeight, textStyles, portalTypography };
export { spacing, semanticSpacing, portalSpacing, borderRadius, zIndex };
export { shadows, focusRing, componentShadows };
export { duration, easing, animations, keyframes } from "./motion";
export type { PortalVariant, PortalColorScheme, ColorScale };
