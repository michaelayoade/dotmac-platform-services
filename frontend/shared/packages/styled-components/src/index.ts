/**
 * @dotmac/styled-components - Portal-specific styled components
 *
 * This package provides styled versions of @dotmac/primitives optimized for
 * different portal contexts: Admin, Customer, and Reseller interfaces.
 */

// Portal-specific exports
export * from './admin';
// Portal theme instances
export { adminTheme } from './admin';

// Common exports for backward compatibility
export { Button, Input, Card } from '@dotmac/primitives';
// Theme provider component
export { ThemeProvider } from './components/ThemeProvider';
export * from './customer';
export { customerTheme } from './customer';
// Utility functions
export {
  animationPresets,
  cn,
  createPortalTheme,
  createPortalVariants,
  focusRing,
  getPortalPrefix,
  getPortalVars,
  portalClass,
  radiusPresets,
  responsiveUtils,
  shadowPresets,
  typographyScale,
} from './lib/utils';
export * from './reseller';
export { resellerTheme } from './reseller';
export * from './shared';

// Version info
export const version = '1.0.0';

// Default portal themes
export const portalThemes = {
  admin: 'admin-portal',
  customer: 'customer-portal',
  reseller: 'reseller-portal',
} as const;

// Theme configuration
export const themeConfig = {
  admin: {
    name: 'Admin Portal',
    description: 'High-density interface for power users',
    density: 'compact',
    primary: 'hsl(217 91% 60%)',
    features: ['dark-mode', 'keyboard-shortcuts', 'bulk-actions'],
  },
  customer: {
    name: 'Customer Portal',
    description: 'Friendly interface for end users',
    density: 'comfortable',
    primary: 'hsl(239 84% 67%)',
    features: ['large-text', 'helpful-guidance', 'simple-navigation'],
  },
  reseller: {
    name: 'Reseller Portal',
    description: 'Professional interface for partners',
    density: 'balanced',
    primary: 'hsl(158 64% 52%)',
    features: ['brand-customization', 'commission-tracking', 'white-label'],
  },
} as const;
