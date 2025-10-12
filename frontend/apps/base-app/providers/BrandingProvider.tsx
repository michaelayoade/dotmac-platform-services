'use client';

import { ReactNode, useEffect } from 'react';
import { useAppConfig } from './AppConfigContext';
import { applyBrandingConfig, applyThemeTokens } from '@/lib/theme';

interface BrandingProviderProps {
  children: ReactNode;
}

export function BrandingProvider({ children }: BrandingProviderProps) {
  const { branding, theme } = useAppConfig();

  useEffect(() => {
    applyThemeTokens(theme);
  }, [theme]);

  useEffect(() => {
    applyBrandingConfig(branding);
  }, [branding]);

  return <>{children}</>;
}
