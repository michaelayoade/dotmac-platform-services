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

export function buildTheme(config: ThemeConfig, resolvedColorScheme: "light" | "dark" = "light"): Theme {
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
      background: portalScheme.background[resolvedColorScheme],
      surface: portalScheme.surface[resolvedColorScheme],
      text: portalScheme.text[resolvedColorScheme],
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
  manageColorScheme?: boolean;
  managePalette?: boolean;
}

export function ThemeProvider({
  children,
  defaultVariant = "admin",
  defaultColorScheme = "system",
  defaultDensity = "comfortable",
  brand,
  configEndpoint,
  tenantId,
  manageColorScheme = true,
  managePalette = false,
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
      if (!manageColorScheme) {
        return;
      }
      return;
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
      const isDark = e.matches;
      setResolvedColorScheme(isDark ? "dark" : "light");

      // Apply dark class to document
      if (manageColorScheme) {
        if (isDark) {
          document.documentElement.classList.add("dark");
        } else {
          document.documentElement.classList.remove("dark");
        }
      }
    };

    // Initial check
    handleChange(mediaQuery);

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [config.colorScheme, manageColorScheme]);

  // Apply color scheme class to document when it changes
  useEffect(() => {
    if (!manageColorScheme) return;
    const root = document.documentElement;
    const isDark =
      config.colorScheme === "dark" ||
      (config.colorScheme === "system" && resolvedColorScheme === "dark");

    // Add transition class for smooth theme change
    root.classList.add("theme-transition");

    // Remove both classes first, then add the appropriate one
    root.classList.remove("light", "dark");
    root.classList.add(isDark ? "dark" : "light");
    root.style.colorScheme = isDark ? "dark" : "light";

    // Remove transition class after animation completes
    const timeout = setTimeout(() => {
      root.classList.remove("theme-transition");
    }, 300);

    return () => clearTimeout(timeout);
  }, [config.colorScheme, resolvedColorScheme, manageColorScheme]);

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

  const theme = useMemo(() => buildTheme(config, resolvedColorScheme), [config, resolvedColorScheme]);
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

    // Primary color scale
    Object.entries(theme.colors.primary).forEach(([shade, value]) => {
      vars[`--color-primary-${shade}`] = toHslTriplet(value);
    });

    // Secondary color scale
    Object.entries(theme.colors.secondary).forEach(([shade, value]) => {
      vars[`--color-secondary-${shade}`] = toHslTriplet(value);
    });

    // Neutral color scale
    Object.entries(theme.colors.neutral).forEach(([shade, value]) => {
      vars[`--color-neutral-${shade}`] = toHslTriplet(value);
    });

    // Status color scales (success, warning, error)
    Object.entries(theme.colors.success).forEach(([shade, value]) => {
      vars[`--color-success-${shade}`] = toHslTriplet(value);
    });
    Object.entries(theme.colors.warning).forEach(([shade, value]) => {
      vars[`--color-warning-${shade}`] = toHslTriplet(value);
    });
    Object.entries(theme.colors.error).forEach(([shade, value]) => {
      vars[`--color-error-${shade}`] = toHslTriplet(value);
    });

    // Semantic colors
    const currentText = portalScheme.text[resolvedColorScheme];
    vars["--color-accent"] = toHslTriplet(theme.colors.accent);
    vars["--color-accent-hover"] = adjustLightness(
      theme.colors.accent,
      isDarkHsl(currentText) ? 8 : -8
    );
    vars["--color-accent-muted"] = adjustLightness(
      theme.colors.accent,
      isDarkHsl(currentText) ? -15 : 5
    );
    vars["--color-accent-subtle"] = `${toHslTriplet(theme.colors.accent)} / 0.15`;

    // Status semantic colors (using 500 shade as default)
    vars["--color-status-success"] = toHslTriplet(theme.colors.success[500]);
    vars["--color-status-warning"] = toHslTriplet(theme.colors.warning[500]);
    vars["--color-status-error"] = toHslTriplet(theme.colors.error[500]);
    vars["--color-status-info"] = toHslTriplet(theme.colors.primary[500]);

    // Portal colors
    vars["--color-portal-admin"] = toHslTriplet(portalColors.admin.primary[600]);
    vars["--color-portal-tenant"] = toHslTriplet(portalColors.tenant.primary[600]);
    vars["--color-portal-reseller"] = toHslTriplet(portalColors.reseller.primary[600]);
    vars["--color-portal-technician"] = toHslTriplet(portalColors.technician.primary[600]);
    vars["--color-portal-management"] = toHslTriplet(portalColors.management.primary[600]);

    if (managePalette) {
      const background = portalScheme.background[resolvedColorScheme];
      const surface = portalScheme.surface[resolvedColorScheme];
      const text = portalScheme.text[resolvedColorScheme];
      const darkMode = isDarkHsl(text);

      vars["--color-background"] = toHslTriplet(background);
      vars["--color-surface"] = toHslTriplet(surface);
      vars["--color-surface-elevated"] = adjustLightness(surface, darkMode ? 3 : -2);
      vars["--color-surface-overlay"] = adjustLightness(surface, darkMode ? 6 : -5);
      vars["--color-surface-subtle"] = adjustLightness(surface, darkMode ? 9 : -8);

      vars["--color-border"] = adjustLightness(surface, darkMode ? 12 : -12);
      vars["--color-border-subtle"] = adjustLightness(surface, darkMode ? 8 : -8);
      vars["--color-border-strong"] = adjustLightness(surface, darkMode ? 18 : -18);

      vars["--color-text-primary"] = toHslTriplet(text);
      vars["--color-text-secondary"] = adjustLightness(text, darkMode ? -20 : 20);
      vars["--color-text-muted"] = adjustLightness(text, darkMode ? -35 : 35);
      vars["--color-text-inverse"] = toHslTriplet(background);
    }

    // Typography variables
    vars["--font-family-sans"] = theme.typography.fontFamily.sans.join(", ");
    vars["--font-family-serif"] = theme.typography.fontFamily.serif.join(", ");
    vars["--font-family-mono"] = theme.typography.fontFamily.mono.join(", ");

    // Font sizes (each has size, lineHeight, letterSpacing)
    Object.entries(fontSize).forEach(([name, config]) => {
      vars[`--font-size-${name}`] = config.size;
      vars[`--line-height-${name}`] = config.lineHeight;
      vars[`--letter-spacing-${name}`] = config.letterSpacing;
    });

    // Border radius
    Object.entries(borderRadius).forEach(([name, value]) => {
      vars[`--radius-${name}`] = value;
    });

    // Shadows
    Object.entries(shadows).forEach(([name, value]) => {
      vars[`--shadow-${name}`] = value;
    });

    // Focus ring variants
    Object.entries(focusRing).forEach(([name, value]) => {
      vars[`--ring-${name}`] = value;
    });

    // Spacing based on density
    const densitySpacing = portalSpacing[config.density];
    vars["--spacing-component"] = densitySpacing.componentPadding;
    vars["--spacing-card"] = densitySpacing.cardPadding;
    vars["--spacing-gap"] = densitySpacing.listItemGap;
    vars["--height-input"] = densitySpacing.inputHeight;
    vars["--height-button"] = densitySpacing.buttonHeight;

    // Base spacing scale
    Object.entries(spacing).forEach(([name, value]) => {
      vars[`--spacing-${name}`] = value;
    });

    // Z-index scale
    Object.entries(zIndex).forEach(([name, value]) => {
      vars[`--z-${name}`] = String(value);
    });

    // Motion variables
    const motionConfig = portalMotion[config.variant as keyof typeof portalMotion];
    if (motionConfig && !config.reducedMotion) {
      vars["--duration-default"] = duration[motionConfig.defaultDuration];
      vars["--easing-default"] = easing[motionConfig.defaultEasing];
    } else {
      vars["--duration-default"] = duration.instant;
      vars["--easing-default"] = easing.linear;
    }

    // All duration values
    Object.entries(duration).forEach(([name, value]) => {
      vars[`--duration-${name}`] = value;
    });

    // All easing values
    Object.entries(easing).forEach(([name, value]) => {
      vars[`--easing-${name}`] = value;
    });

    return vars;
  }, [theme, config, managePalette, portalScheme, resolvedColorScheme]);

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

function toHslTriplet(value: string): string {
  const hex = value.trim();
  if (!hex.startsWith("#")) {
    return value;
  }
  const normalized = hex.length === 4
    ? `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}`
    : hex;
  const parsed = normalized.replace("#", "");
  if (parsed.length !== 6) {
    return value;
  }
  const r = parseInt(parsed.slice(0, 2), 16) / 255;
  const g = parseInt(parsed.slice(2, 4), 16) / 255;
  const b = parseInt(parsed.slice(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const delta = max - min;
  let h = 0;
  if (delta !== 0) {
    if (max === r) {
      h = ((g - b) / delta) % 6;
    } else if (max === g) {
      h = (b - r) / delta + 2;
    } else {
      h = (r - g) / delta + 4;
    }
    h = Math.round(h * 60);
    if (h < 0) h += 360;
  }
  const l = (max + min) / 2;
  const s = delta === 0 ? 0 : delta / (1 - Math.abs(2 * l - 1));

  const hRounded = Math.round(h);
  const sRounded = Math.round(s * 100);
  const lRounded = Math.round(l * 100);
  return `${hRounded} ${sRounded}% ${lRounded}%`;
}

function parseTriplet(value: string): { h: number; s: number; l: number } | null {
  const match = value.trim().match(/^(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)%\s+(\d+(?:\.\d+)?)%$/);
  if (!match) {
    return null;
  }
  return {
    h: Number(match[1]),
    s: Number(match[2]),
    l: Number(match[3]),
  };
}

function toHsl(value: string): { h: number; s: number; l: number } | null {
  const triplet = parseTriplet(value);
  if (triplet) {
    return triplet;
  }
  if (!value.trim().startsWith("#")) {
    return null;
  }
  const normalized = value.length === 4
    ? `#${value[1]}${value[1]}${value[2]}${value[2]}${value[3]}${value[3]}`
    : value;
  const parsed = normalized.replace("#", "");
  if (parsed.length !== 6) {
    return null;
  }
  const r = parseInt(parsed.slice(0, 2), 16) / 255;
  const g = parseInt(parsed.slice(2, 4), 16) / 255;
  const b = parseInt(parsed.slice(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const delta = max - min;
  let h = 0;
  if (delta !== 0) {
    if (max === r) {
      h = ((g - b) / delta) % 6;
    } else if (max === g) {
      h = (b - r) / delta + 2;
    } else {
      h = (r - g) / delta + 4;
    }
    h = h * 60;
    if (h < 0) h += 360;
  }
  const l = (max + min) / 2;
  const s = delta === 0 ? 0 : delta / (1 - Math.abs(2 * l - 1));

  return {
    h: Math.round(h),
    s: Math.round(s * 100),
    l: Math.round(l * 100),
  };
}

function adjustLightness(value: string, delta: number): string {
  const hsl = toHsl(value);
  if (!hsl) {
    return value;
  }
  const nextL = Math.max(0, Math.min(100, hsl.l + delta));
  return `${hsl.h} ${hsl.s}% ${nextL}%`;
}

function isDarkHsl(value: string): boolean {
  const hsl = toHsl(value);
  if (!hsl) {
    return false;
  }
  return hsl.l < 55;
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
