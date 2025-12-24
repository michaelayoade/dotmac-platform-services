/**
 * @dotmac/design-tokens - Utility Functions
 *
 * Helper functions for working with design tokens
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// ============================================================================
// Class Name Utilities
// ============================================================================

/**
 * Merge Tailwind CSS classes with clsx
 * Handles conditional classes and deduplication
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ============================================================================
// CSS Variable Utilities
// ============================================================================

/**
 * Get CSS variable value
 */
export function getCSSVariable(name: string): string {
  if (typeof window === "undefined") return "";
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/**
 * Set CSS variable value
 */
export function setCSSVariable(name: string, value: string): void {
  if (typeof window === "undefined") return;
  document.documentElement.style.setProperty(name, value);
}

/**
 * Remove CSS variable
 */
export function removeCSSVariable(name: string): void {
  if (typeof window === "undefined") return;
  document.documentElement.style.removeProperty(name);
}

/**
 * Create CSS variable reference
 */
export function cssVar(name: string, fallback?: string): string {
  return fallback ? `var(${name}, ${fallback})` : `var(${name})`;
}

// ============================================================================
// Color Utilities
// ============================================================================

/**
 * Convert hex to RGB values
 */
export function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

/**
 * Convert RGB to hex
 */
export function rgbToHex(r: number, g: number, b: number): string {
  return `#${((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)}`;
}

/**
 * Get contrasting text color (black or white) for a background
 */
export function getContrastColor(hexColor: string): "black" | "white" {
  const rgb = hexToRgb(hexColor);
  if (!rgb) return "black";

  // Calculate relative luminance
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
  return luminance > 0.5 ? "black" : "white";
}

/**
 * Adjust color brightness
 */
export function adjustBrightness(hexColor: string, percent: number): string {
  const rgb = hexToRgb(hexColor);
  if (!rgb) return hexColor;

  const adjust = (value: number) =>
    Math.min(255, Math.max(0, Math.round(value + (value * percent) / 100)));

  return rgbToHex(adjust(rgb.r), adjust(rgb.g), adjust(rgb.b));
}

/**
 * Create color with alpha
 */
export function withAlpha(hexColor: string, alpha: number): string {
  const rgb = hexToRgb(hexColor);
  if (!rgb) return hexColor;
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

// ============================================================================
// Spacing Utilities
// ============================================================================

/**
 * Convert rem to pixels (assuming 16px base)
 */
export function remToPx(rem: string): number {
  const value = parseFloat(rem);
  return value * 16;
}

/**
 * Convert pixels to rem (assuming 16px base)
 */
export function pxToRem(px: number): string {
  return `${px / 16}rem`;
}

// ============================================================================
// Media Query Utilities
// ============================================================================

/**
 * Check if we're in a browser environment
 */
export function isBrowser(): boolean {
  return typeof window !== "undefined";
}

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  if (!isBrowser()) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Check if user prefers dark color scheme
 */
export function prefersDarkMode(): boolean {
  if (!isBrowser()) return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/**
 * Check if device supports hover
 */
export function supportsHover(): boolean {
  if (!isBrowser()) return true;
  return window.matchMedia("(hover: hover)").matches;
}

/**
 * Check if device is touch-primary
 */
export function isTouchDevice(): boolean {
  if (!isBrowser()) return false;
  return window.matchMedia("(pointer: coarse)").matches;
}

// ============================================================================
// Token Access Utilities
// ============================================================================

/**
 * Get nested value from object by path
 */
export function getTokenValue<T>(tokens: Record<string, unknown>, path: string): T | undefined {
  const keys = path.split(".");
  let current: unknown = tokens;

  for (const key of keys) {
    if (current && typeof current === "object" && key in current) {
      current = (current as Record<string, unknown>)[key];
    } else {
      return undefined;
    }
  }

  return current as T;
}

/**
 * Flatten nested token object to CSS variables
 */
export function tokensToCSSVariables(
  tokens: Record<string, unknown>,
  prefix = "--"
): Record<string, string> {
  const result: Record<string, string> = {};

  function flatten(obj: Record<string, unknown>, path: string) {
    for (const [key, value] of Object.entries(obj)) {
      const newPath = path ? `${path}-${key}` : `${prefix}${key}`;

      if (value && typeof value === "object" && !Array.isArray(value)) {
        flatten(value as Record<string, unknown>, newPath);
      } else {
        result[newPath] = String(value);
      }
    }
  }

  flatten(tokens, "");
  return result;
}
