/**
 * Universal Currency Formatting for DotMac Framework
 *
 * Provides consistent multi-currency formatting across all frontend applications
 * with proper internationalization and locale support.
 */

// Supported currencies with their display information
export const CURRENCY_INFO = {
  USD: { symbol: '$', name: 'US Dollar', locale: 'en-US', decimals: 2 },
  EUR: { symbol: '€', name: 'Euro', locale: 'de-DE', decimals: 2 },
  GBP: { symbol: '£', name: 'British Pound', locale: 'en-GB', decimals: 2 },
  JPY: { symbol: '¥', name: 'Japanese Yen', locale: 'ja-JP', decimals: 0 },
  CAD: { symbol: 'C$', name: 'Canadian Dollar', locale: 'en-CA', decimals: 2 },
  AUD: { symbol: 'A$', name: 'Australian Dollar', locale: 'en-AU', decimals: 2 },
  CHF: { symbol: 'CHF', name: 'Swiss Franc', locale: 'de-CH', decimals: 2 },
  CNY: { symbol: '¥', name: 'Chinese Yuan', locale: 'zh-CN', decimals: 2 },
  INR: { symbol: '₹', name: 'Indian Rupee', locale: 'en-IN', decimals: 2 },
  BRL: { symbol: 'R$', name: 'Brazilian Real', locale: 'pt-BR', decimals: 2 },
  MXN: { symbol: '$', name: 'Mexican Peso', locale: 'es-MX', decimals: 2 },
  KRW: { symbol: '₩', name: 'South Korean Won', locale: 'ko-KR', decimals: 0 },
  SGD: { symbol: 'S$', name: 'Singapore Dollar', locale: 'en-SG', decimals: 2 },
  HKD: { symbol: 'HK$', name: 'Hong Kong Dollar', locale: 'zh-HK', decimals: 2 },
  SEK: { symbol: 'kr', name: 'Swedish Krona', locale: 'sv-SE', decimals: 2 },
  NOK: { symbol: 'kr', name: 'Norwegian Krone', locale: 'nb-NO', decimals: 2 },
  DKK: { symbol: 'kr', name: 'Danish Krone', locale: 'da-DK', decimals: 2 },
  PLN: { symbol: 'zł', name: 'Polish Zloty', locale: 'pl-PL', decimals: 2 },
  CZK: { symbol: 'Kč', name: 'Czech Koruna', locale: 'cs-CZ', decimals: 2 },
  HUF: { symbol: 'Ft', name: 'Hungarian Forint', locale: 'hu-HU', decimals: 0 },
  RUB: { symbol: '₽', name: 'Russian Ruble', locale: 'ru-RU', decimals: 2 },
  TRY: { symbol: '₺', name: 'Turkish Lira', locale: 'tr-TR', decimals: 2 },
  ZAR: { symbol: 'R', name: 'South African Rand', locale: 'en-ZA', decimals: 2 },
  NZD: { symbol: 'NZ$', name: 'New Zealand Dollar', locale: 'en-NZ', decimals: 2 },
  NGN: { symbol: '₦', name: 'Nigerian Naira', locale: 'en-NG', decimals: 2 },
} as const;

export type SupportedCurrency = keyof typeof CURRENCY_INFO;

export interface CurrencyFormatOptions {
  /** Currency code (ISO 4217) */
  currency?: SupportedCurrency;
  /** Locale for formatting */
  locale?: string;
  /** Show currency symbol */
  showSymbol?: boolean;
  /** Override decimal places */
  decimals?: number;
  /** Compact notation for large numbers (e.g., $1.2K) */
  compact?: boolean;
  /** Show plus sign for positive numbers */
  signDisplay?: 'auto' | 'never' | 'always' | 'exceptZero';
}

/**
 * Universal currency formatting function with full internationalization support.
 */
export function formatCurrency(amount: number, options: CurrencyFormatOptions = {}): string {
  const {
    currency = 'USD',
    locale,
    showSymbol = true,
    decimals,
    compact = false,
    signDisplay = 'auto',
  } = options;

  // Get currency info
  const currencyInfo = CURRENCY_INFO[currency];
  if (!currencyInfo) {
    console.warn(`Unsupported currency: ${currency}. Falling back to USD.`);
    return formatCurrency(amount, { ...options, currency: 'USD' });
  }

  // Determine locale
  const formatLocale = locale || currencyInfo.locale;

  // Determine decimal places
  const decimalPlaces = decimals !== undefined ? decimals : currencyInfo.decimals;

  // Create formatter options
  const formatOptions: Intl.NumberFormatOptions = {
    style: showSymbol ? 'currency' : 'decimal',
    currency: showSymbol ? currency : undefined,
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces,
    signDisplay,
  };

  // Add compact notation if requested
  if (compact && Math.abs(amount) >= 1000) {
    formatOptions.notation = 'compact';
    formatOptions.compactDisplay = 'short';
  }

  try {
    return new Intl.NumberFormat(formatLocale, formatOptions).format(amount);
  } catch (error) {
    // Fallback to en-US if locale is not supported
    console.warn(`Locale ${formatLocale} not supported. Falling back to en-US.`, error);
    return new Intl.NumberFormat('en-US', {
      ...formatOptions,
      currency: showSymbol ? currency : undefined,
    }).format(amount);
  }
}

/**
 * Get information about a supported currency.
 */
export function getCurrencyInfo(currency: SupportedCurrency) {
  return CURRENCY_INFO[currency];
}

/**
 * Validate if a currency code is supported.
 */
export function isSupportedCurrency(currency: string): currency is SupportedCurrency {
  return currency in CURRENCY_INFO;
}

/**
 * Get list of all supported currency codes.
 */
export function getSupportedCurrencies(): SupportedCurrency[] {
  return Object.keys(CURRENCY_INFO) as SupportedCurrency[];
}

/**
 * Format currency for display in compact form (e.g., $1.2K, $3.4M).
 */
export function formatCurrencyCompact(
  amount: number,
  currency: SupportedCurrency = 'USD',
  locale?: string
): string {
  return formatCurrency(amount, { currency, locale, compact: true });
}

/**
 * Format currency without symbol (numeric only).
 */
export function formatCurrencyNumeric(
  amount: number,
  currency: SupportedCurrency = 'USD',
  locale?: string
): string {
  return formatCurrency(amount, { currency, locale, showSymbol: false });
}

/**
 * Format currency with explicit positive sign.
 */
export function formatCurrencyWithSign(
  amount: number,
  currency: SupportedCurrency = 'USD',
  locale?: string
): string {
  return formatCurrency(amount, {
    currency,
    locale,
    signDisplay: amount >= 0 ? 'always' : 'auto',
  });
}

// Convenience functions for common currencies
export const formatUSD = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'USD' });

export const formatEUR = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'EUR' });

export const formatGBP = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'GBP' });

export const formatJPY = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'JPY' });

// Legacy compatibility - matches existing interface
export function formatPluginPrice(price?: number, currency: SupportedCurrency = 'USD'): string {
  if (!price || price === 0) {
    return 'Free';
  }
  return formatCurrency(price, { currency });
}

/**
 * Currency selector for UI components.
 */
export function getCurrencyOptions(): Array<{
  value: SupportedCurrency;
  label: string;
  symbol: string;
}> {
  return getSupportedCurrencies().map((code) => {
    const info = CURRENCY_INFO[code];
    return {
      value: code,
      label: `${code} - ${info.name}`,
      symbol: info.symbol,
    };
  });
}
