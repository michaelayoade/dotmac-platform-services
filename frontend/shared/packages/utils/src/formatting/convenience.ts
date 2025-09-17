/**
 * Convenience functions for commonly requested currencies
 */
import { formatCurrency, type CurrencyFormatOptions } from './currency';

// Popular African currencies
export const formatNGN = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'NGN' });

export const formatZAR = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'ZAR' });

// Popular Asian currencies
export const formatCNY = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'CNY' });

export const formatINR = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'INR' });

export const formatKRW = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'KRW' });

// Popular Latin American currencies
export const formatBRL = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'BRL' });

export const formatMXN = (amount: number, options?: Omit<CurrencyFormatOptions, 'currency'>) =>
  formatCurrency(amount, { ...options, currency: 'MXN' });
