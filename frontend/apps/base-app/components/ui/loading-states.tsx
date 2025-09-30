/**
 * Consistent loading state components
 * Provides standardized loading indicators across the application
 */

import React from 'react';
import { Loader2, AlertCircle, CheckCircle, InfoIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  label?: string;
}

/**
 * Standard loading spinner
 */
export function LoadingSpinner({ size = 'md', className, label }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Loader2 className={cn('animate-spin text-sky-500', sizeClasses[size])} />
      {label && <span className="text-slate-400 text-sm">{label}</span>}
    </div>
  );
}

interface LoadingOverlayProps {
  show: boolean;
  message?: string;
  blur?: boolean;
}

/**
 * Full screen loading overlay
 */
export function LoadingOverlay({ show, message = 'Loading...', blur = true }: LoadingOverlayProps) {
  if (!show) return null;

  return (
    <div className={cn(
      'fixed inset-0 z-50 flex items-center justify-center',
      blur && 'backdrop-blur-sm'
    )}>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-slate-900 rounded-lg p-6 shadow-xl">
        <div className="flex flex-col items-center gap-3">
          <LoadingSpinner size="lg" />
          <p className="text-slate-300">{message}</p>
        </div>
      </div>
    </div>
  );
}

interface LoadingCardProps {
  lines?: number;
  showAvatar?: boolean;
  className?: string;
}

/**
 * Skeleton loading card
 */
export function LoadingCard({ lines = 3, showAvatar = false, className }: LoadingCardProps) {
  return (
    <div className={cn('bg-slate-900 rounded-lg p-6 animate-pulse', className)}>
      <div className="flex items-start gap-4">
        {showAvatar && (
          <div className="h-10 w-10 bg-slate-800 rounded-full" />
        )}
        <div className="flex-1 space-y-3">
          <div className="h-4 bg-slate-800 rounded w-3/4" />
          {Array.from({ length: lines - 1 }).map((_, i) => (
            <div key={i} className="h-4 bg-slate-800 rounded w-full" />
          ))}
        </div>
      </div>
    </div>
  );
}

interface LoadingTableProps {
  rows?: number;
  columns?: number;
  className?: string;
}

/**
 * Skeleton loading table
 */
export function LoadingTable({ rows = 5, columns = 4, className }: LoadingTableProps) {
  return (
    <div className={cn('bg-slate-900 rounded-lg overflow-hidden', className)}>
      {/* Header */}
      <div className="border-b border-slate-800 p-4">
        <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, i) => (
            <div key={i} className="h-4 bg-slate-800 rounded animate-pulse" />
          ))}
        </div>
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="border-b border-slate-800 p-4">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <div
                key={colIndex}
                className="h-4 bg-slate-800 rounded animate-pulse"
                style={{ width: `${Math.random() * 40 + 60}%` }}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

interface LoadingGridProps {
  items?: number;
  columns?: number;
  className?: string;
}

/**
 * Skeleton loading grid
 */
export function LoadingGrid({ items = 6, columns = 3, className }: LoadingGridProps) {
  return (
    <div
      className={cn('grid gap-6', className)}
      style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
    >
      {Array.from({ length: items }).map((_, i) => (
        <LoadingCard key={i} lines={2} />
      ))}
    </div>
  );
}

interface LoadingStateProps {
  loading: boolean;
  error?: Error | null;
  empty?: boolean;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
}

/**
 * Wrapper component for consistent loading states
 */
export function LoadingState({
  loading,
  error,
  empty,
  children,
  loadingComponent,
  errorComponent,
  emptyComponent,
  emptyMessage = 'No data available',
  emptyIcon
}: LoadingStateProps) {
  if (loading) {
    return <>{loadingComponent || <LoadingSpinner size="lg" className="mx-auto my-8" />}</>;
  }

  if (error) {
    return (
      <>
        {errorComponent || (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
            <p className="text-slate-300 mb-2">Something went wrong</p>
            <p className="text-slate-500 text-sm">{error?.message || 'Please try again later'}</p>
          </div>
        )}
      </>
    );
  }

  if (empty) {
    return (
      <>
        {emptyComponent || (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            {emptyIcon || <InfoIcon className="h-12 w-12 text-slate-500 mb-4" />}
            <p className="text-slate-400">{emptyMessage}</p>
          </div>
        )}
      </>
    );
  }

  return <>{children}</>;
}

interface AsyncStateProps<T> {
  data?: T;
  loading: boolean;
  error?: Error | null;
  children: (data: T) => React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  isEmpty?: (data: T) => boolean;
}

/**
 * Generic async state wrapper
 */
export function AsyncState<T>({
  data,
  loading,
  error,
  children,
  loadingComponent,
  errorComponent,
  emptyComponent,
  isEmpty
}: AsyncStateProps<T>) {
  const isEmptyData = data && isEmpty ? isEmpty(data) : !data;

  return (
    <LoadingState
      loading={loading}
      error={error}
      empty={isEmptyData}
      loadingComponent={loadingComponent}
      errorComponent={errorComponent}
      emptyComponent={emptyComponent}
    >
      {data && children(data)}
    </LoadingState>
  );
}

interface ButtonLoadingProps {
  loading?: boolean;
  children: React.ReactNode;
  loadingText?: string;
  className?: string;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
}

/**
 * Button with loading state
 */
export function ButtonLoading({
  loading,
  children,
  loadingText,
  className,
  onClick,
  type = 'button',
  variant = 'primary',
  disabled
}: ButtonLoadingProps) {
  const variantClasses = {
    primary: 'bg-sky-500 hover:bg-sky-600 text-white',
    secondary: 'bg-slate-700 hover:bg-slate-600 text-white',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={loading || disabled}
      className={cn(
        'px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2',
        variantClasses[variant],
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {loading && loadingText ? loadingText : children}
    </button>
  );
}

/**
 * Progress indicator for multi-step processes
 */
interface ProgressIndicatorProps {
  steps: Array<{ label: string; status: 'pending' | 'active' | 'completed' | 'error' }>;
  className?: string;
}

export function ProgressIndicator({ steps, className }: ProgressIndicatorProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {steps.map((step, index) => (
        <div key={index} className="flex items-center gap-3">
          <div className={cn(
            'h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium',
            {
              'bg-slate-700 text-slate-400': step.status === 'pending',
              'bg-sky-500 text-white': step.status === 'active',
              'bg-green-500 text-white': step.status === 'completed',
              'bg-red-500 text-white': step.status === 'error',
            }
          )}>
            {step.status === 'completed' ? (
              <CheckCircle className="h-4 w-4" />
            ) : step.status === 'error' ? (
              <AlertCircle className="h-4 w-4" />
            ) : step.status === 'active' ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              index + 1
            )}
          </div>
          <span className={cn('text-sm', {
            'text-slate-500': step.status === 'pending',
            'text-white font-medium': step.status === 'active',
            'text-slate-300': step.status === 'completed',
            'text-red-400': step.status === 'error',
          })}>
            {step.label}
          </span>
        </div>
      ))}
    </div>
  );
}