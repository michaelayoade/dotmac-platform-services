'use client';

import { useAppConfig } from '@/providers/AppConfigContext';

export function useBranding() {
  const { branding, theme } = useAppConfig();

  return {
    branding,
    theme,
  };
}
