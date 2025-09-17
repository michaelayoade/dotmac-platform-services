import { useMemo } from 'react';
import { PortalVariant, PortalTheme } from '../types';

/**
 * Portal-specific theme configurations
 * Each portal has its own color scheme and styling patterns
 */
const portalThemes: Record<PortalVariant, PortalTheme> = {
  'management-admin': {
    variant: 'management-admin',
    colors: {
      primary: '#4F46E5',
      secondary: '#6B7280',
      accent: '#F59E0B',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6',
    },
    spacing: {
      formGap: 'space-y-6',
      sectionGap: 'space-y-8',
      fieldGap: 'space-y-2',
    },
    typography: {
      formTitle: 'text-gray-900 font-semibold',
      sectionTitle: 'text-gray-800 font-medium',
      fieldLabel: 'text-gray-700 font-medium',
      helpText: 'text-gray-500',
    },
    components: {
      card: 'bg-white shadow-sm border border-gray-200 rounded-lg p-6',
      input: 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500',
      button: 'bg-indigo-600 hover:bg-indigo-700 text-white',
      label: 'text-gray-700 font-medium',
    },
  },

  customer: {
    variant: 'customer',
    colors: {
      primary: '#059669',
      secondary: '#6B7280',
      accent: '#0891B2',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#0891B2',
    },
    spacing: {
      formGap: 'space-y-5',
      sectionGap: 'space-y-6',
      fieldGap: 'space-y-1.5',
    },
    typography: {
      formTitle: 'text-gray-900 font-bold',
      sectionTitle: 'text-gray-800 font-semibold',
      fieldLabel: 'text-gray-700 font-medium',
      helpText: 'text-gray-600',
    },
    components: {
      card: 'bg-white shadow-md border border-gray-100 rounded-xl p-6',
      input: 'border-gray-300 focus:border-emerald-500 focus:ring-emerald-500',
      button: 'bg-emerald-600 hover:bg-emerald-700 text-white',
      label: 'text-gray-700 font-medium',
    },
  },

  admin: {
    variant: 'admin',
    colors: {
      primary: '#7C3AED',
      secondary: '#6B7280',
      accent: '#EC4899',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6',
    },
    spacing: {
      formGap: 'space-y-6',
      sectionGap: 'space-y-7',
      fieldGap: 'space-y-2',
    },
    typography: {
      formTitle: 'text-gray-900 font-bold',
      sectionTitle: 'text-gray-800 font-semibold',
      fieldLabel: 'text-gray-700 font-medium',
      helpText: 'text-gray-500',
    },
    components: {
      card: 'bg-white shadow border border-gray-200 rounded-lg p-6',
      input: 'border-gray-300 focus:border-purple-500 focus:ring-purple-500',
      button: 'bg-purple-600 hover:bg-purple-700 text-white',
      label: 'text-gray-700 font-medium',
    },
  },

  reseller: {
    variant: 'reseller',
    colors: {
      primary: '#DC2626',
      secondary: '#6B7280',
      accent: '#F59E0B',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6',
    },
    spacing: {
      formGap: 'space-y-5',
      sectionGap: 'space-y-6',
      fieldGap: 'space-y-2',
    },
    typography: {
      formTitle: 'text-gray-900 font-bold',
      sectionTitle: 'text-gray-800 font-semibold',
      fieldLabel: 'text-gray-700 font-medium',
      helpText: 'text-gray-500',
    },
    components: {
      card: 'bg-white shadow-sm border border-gray-200 rounded-lg p-5',
      input: 'border-gray-300 focus:border-red-500 focus:ring-red-500',
      button: 'bg-red-600 hover:bg-red-700 text-white',
      label: 'text-gray-700 font-medium',
    },
  },

  technician: {
    variant: 'technician',
    colors: {
      primary: '#0891B2',
      secondary: '#64748B',
      accent: '#F59E0B',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#0891B2',
    },
    spacing: {
      formGap: 'space-y-4',
      sectionGap: 'space-y-5',
      fieldGap: 'space-y-1.5',
    },
    typography: {
      formTitle: 'text-gray-900 font-bold text-lg',
      sectionTitle: 'text-gray-800 font-semibold',
      fieldLabel: 'text-gray-700 font-medium text-sm',
      helpText: 'text-gray-600 text-sm',
    },
    components: {
      card: 'bg-white shadow-lg border border-gray-100 rounded-xl p-4',
      input: 'border-gray-300 focus:border-cyan-500 focus:ring-cyan-500 text-base',
      button: 'bg-cyan-600 hover:bg-cyan-700 text-white font-medium',
      label: 'text-gray-700 font-medium text-sm',
    },
  },

  'management-reseller': {
    variant: 'management-reseller',
    colors: {
      primary: '#1D4ED8',
      secondary: '#6B7280',
      accent: '#7C2D12',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6',
    },
    spacing: {
      formGap: 'space-y-6',
      sectionGap: 'space-y-8',
      fieldGap: 'space-y-2',
    },
    typography: {
      formTitle: 'text-gray-900 font-bold',
      sectionTitle: 'text-gray-800 font-semibold',
      fieldLabel: 'text-gray-700 font-medium',
      helpText: 'text-gray-500',
    },
    components: {
      card: 'bg-white shadow border border-gray-200 rounded-lg p-6',
      input: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
      button: 'bg-blue-600 hover:bg-blue-700 text-white',
      label: 'text-gray-700 font-medium',
    },
  },

  'tenant-portal': {
    variant: 'tenant-portal',
    colors: {
      primary: '#059669',
      secondary: '#6B7280',
      accent: '#0D9488',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#0D9488',
    },
    spacing: {
      formGap: 'space-y-5',
      sectionGap: 'space-y-6',
      fieldGap: 'space-y-2',
    },
    typography: {
      formTitle: 'text-gray-900 font-semibold',
      sectionTitle: 'text-gray-800 font-medium',
      fieldLabel: 'text-gray-700 font-medium',
      helpText: 'text-gray-500',
    },
    components: {
      card: 'bg-white shadow-sm border border-gray-200 rounded-lg p-6',
      input: 'border-gray-300 focus:border-teal-500 focus:ring-teal-500',
      button: 'bg-teal-600 hover:bg-teal-700 text-white',
      label: 'text-gray-700 font-medium',
    },
  },
};

/**
 * Hook to get portal-specific theme configuration
 * @param portalVariant - The portal variant to get theme for
 * @returns Portal-specific theme configuration
 */
export function usePortalTheme(portalVariant: PortalVariant): PortalTheme {
  const theme = useMemo(() => {
    return portalThemes[portalVariant];
  }, [portalVariant]);

  if (!theme) {
    console.warn(`No theme found for portal variant: ${portalVariant}. Using default theme.`);
    return portalThemes['management-admin']; // Fallback to management-admin theme
  }

  return theme;
}

/**
 * Get portal theme without hook (for use outside React components)
 * @param portalVariant - The portal variant to get theme for
 * @returns Portal-specific theme configuration
 */
export function getPortalTheme(portalVariant: PortalVariant): PortalTheme {
  return portalThemes[portalVariant] || portalThemes['management-admin'];
}
