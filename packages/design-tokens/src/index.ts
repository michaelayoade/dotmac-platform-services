/**
 * @dotmac/design-tokens
 *
 * Design tokens, color palettes, typography, spacing, and theme system
 * for DotMac components
 *
 * @example
 * ```tsx
 * import { ThemeProvider, useTheme, colors, spacing } from '@dotmac/design-tokens';
 *
 * function App() {
 *   return (
 *     <ThemeProvider defaultVariant="admin">
 *       <MyComponent />
 *     </ThemeProvider>
 *   );
 * }
 *
 * function MyComponent() {
 *   const { theme, config } = useTheme();
 *   return <div style={{ color: theme.colors.primary[500] }}>Hello</div>;
 * }
 * ```
 */

// ============================================================================
// Colors
// ============================================================================

export {
  colors,
  semanticColors,
  statusColors,
  portalColors,
  gradients,
  gradientClasses,
  hexToHsl,
  hslToHex,
  generateColorScale,
  getPortalColors,
  type ColorScale,
  type PortalVariant,
  type PortalColorScheme,
} from "./colors";

// ============================================================================
// Typography
// ============================================================================

export {
  fontFamily,
  fontSize,
  fontWeight,
  textStyles,
  portalTypography,
  type FontSizeConfig,
  type PortalTypography,
  type PortalTypographyVariant,
} from "./typography";

// ============================================================================
// Spacing
// ============================================================================

export {
  spacing,
  semanticSpacing,
  portalSpacing,
  touchTargets,
  borderRadius,
  zIndex,
  breakpoints,
  containerWidths,
  aspectRatios,
  type DensityLevel,
  type DensitySpacing,
} from "./spacing";

// ============================================================================
// Motion
// ============================================================================

export {
  duration,
  easing,
  animations,
  keyframes,
  portalMotion,
  getAnimation,
  createTransition,
  type AnimationPreset,
  type PortalMotionVariant,
  type PortalMotionConfig,
} from "./motion";

// ============================================================================
// Shadows
// ============================================================================

export {
  shadows,
  elevation,
  focusRing,
  glow,
  componentShadows,
} from "./shadows";

// ============================================================================
// Theme System
// ============================================================================

export {
  ThemeProvider,
  useTheme,
  useThemeColors,
  useThemeSpacing,
  useThemeMotion,
  buildTheme,
  type ThemeProviderProps,
  type ThemeConfig,
  type Theme,
  type BrandConfig,
} from "./theme.js";

// ============================================================================
// Utilities
// ============================================================================

export {
  cn,
  getCSSVariable,
  setCSSVariable,
  removeCSSVariable,
  cssVar,
  hexToRgb,
  rgbToHex,
  getContrastColor,
  adjustBrightness,
  withAlpha,
  remToPx,
  pxToRem,
  isBrowser,
  prefersReducedMotion,
  prefersDarkMode,
  supportsHover,
  isTouchDevice,
  getTokenValue,
  tokensToCSSVariables,
} from "./utils";

// ============================================================================
// Version
// ============================================================================

export const version = "1.0.0";
