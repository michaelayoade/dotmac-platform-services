/**
 * Enhanced Design System Components
 * Improved visual hierarchy and micro-interactions
 */

import { clsx } from 'clsx';
import React from 'react';

import { useReducedMotion } from './animations';

// Enhanced Button Component
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  // const id = useId(); // Removed - can't use hooks in objects
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className = '',
  disabled,
  ...props
}) => {
  const prefersReducedMotion = useReducedMotion();

  const baseClasses = clsx(
    'inline-flex items-center justify-center font-medium transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
    {
      'w-full': fullWidth,
      'transform hover:scale-105 active:scale-95': !prefersReducedMotion && !disabled,
    }
  );

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50 focus:ring-blue-500',
    ghost: 'text-blue-600 hover:bg-blue-50 focus:ring-blue-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };

  const sizeClasses = {
    sm: 'text-sm px-3 py-1.5 rounded-md',
    md: 'text-sm px-4 py-2 rounded-md',
    lg: 'text-base px-6 py-3 rounded-lg',
    xl: 'text-lg px-8 py-4 rounded-lg',
  };

  return (
    <button
      type='button'
      className={clsx(baseClasses, variantClasses[variant], sizeClasses[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          aria-label='icon'
          className='-ml-1 mr-2 h-4 w-4 animate-spin'
          fill='none'
          viewBox='0 0 24 24'
        >
          <title>Icon</title>
          <circle
            className='opacity-25'
            cx='12'
            cy='12'
            r='10'
            stroke='currentColor'
            strokeWidth='4'
          />
          <path
            className='opacity-75'
            fill='currentColor'
            d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z'
          />
        </svg>
      )}
      {!isLoading && leftIcon && <span className='mr-2'>{leftIcon}</span>}
      <span>{children}</span>
      {!isLoading && rightIcon && <span className='ml-2'>{rightIcon}</span>}
    </button>
  );
};

// Enhanced Card Component
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined' | 'ghost';
  padding?: 'sm' | 'md' | 'lg';
  interactive?: boolean;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  // const id = useId(); // Removed - can't use hooks in objects
  children,
  variant = 'default',
  padding = 'md',
  interactive = false,
  header,
  footer,
  className = '',
  ...props
}) => {
  const prefersReducedMotion = useReducedMotion();

  const baseClasses = clsx('bg-white rounded-lg transition-all duration-200', {
    'cursor-pointer transform hover:scale-[1.02] hover:shadow-lg':
      interactive && !prefersReducedMotion,
    'hover:shadow-md': interactive && prefersReducedMotion,
  });

  const variantClasses = {
    default: 'border border-gray-200 shadow-sm',
    elevated: 'shadow-md hover:shadow-lg',
    outlined: 'border-2 border-gray-200',
    ghost: 'hover:bg-gray-50',
  };

  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={clsx(
        baseClasses,
        variantClasses[variant],
        !header && !footer && paddingClasses[padding],
        className
      )}
      {...props}
    >
      {header && (
        <div
          className={clsx('mb-4 border-gray-200 border-b pb-4', paddingClasses[padding], 'pb-4')}
        >
          {header}
        </div>
      )}
      <div className={clsx(header || footer ? paddingClasses[padding] : '')}>{children}</div>
      {footer && (
        <div
          className={clsx('mt-4 border-gray-200 border-t pt-4', paddingClasses[padding], 'pt-4')}
        >
          {footer}
        </div>
      )}
    </div>
  );
};

// Enhanced Badge Component
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  // const id = useId(); // Removed - can't use hooks in objects
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  className = '',
  ...props
}) => {
  const baseClasses = 'inline-flex items-center font-medium rounded-full';

  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    primary: 'bg-blue-100 text-blue-800',
    secondary: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-sm',
  };

  const dotClasses = {
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
  };

  if (dot) {
    return (
      <span
        className={clsx(
          'inline-block rounded-full',
          variantClasses[variant].replace('text-', 'bg-').split(' ')[1],
          dotClasses[size],
          className
        )}
        {...props}
      />
    );
  }

  return (
    <span
      className={clsx(baseClasses, variantClasses[variant], sizeClasses[size], className)}
      {...props}
    >
      {children}
    </span>
  );
};

// Enhanced Input Component
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  inputSize?: 'sm' | 'md' | 'lg';
}

export const Input: React.FC<InputProps> = ({
  // const id = useId(); // Removed - can't use hooks in objects
  label,
  error,
  hint,
  leftIcon,
  rightIcon,
  inputSize = 'md',
  className = '',
  id,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  const baseClasses = clsx(
    'block w-full border border-gray-300 rounded-md shadow-sm',
    'focus:ring-blue-500 focus:border-blue-500',
    'transition-colors duration-200',
    {
      'border-red-300 focus:ring-red-500 focus:border-red-500': error,
      'pl-10': leftIcon,
      'pr-10': rightIcon,
    }
  );

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base',
  };

  return (
    <div className='space-y-1'>
      {label && (
        <label htmlFor={inputId} className='block font-medium text-gray-700 text-sm'>
          {label}
        </label>
      )}
      <div className='relative'>
        {leftIcon && (
          <div className='pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3'>
            <span className='text-gray-400'>{leftIcon}</span>
          </div>
        )}
        <input
          id={inputId}
          className={clsx(baseClasses, sizeClasses[inputSize], className)}
          {...props}
        />
        {rightIcon && (
          <div className='pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3'>
            <span className='text-gray-400'>{rightIcon}</span>
          </div>
        )}
      </div>
      {hint && !error && <p className='text-gray-500 text-sm'>{hint}</p>}
      {error && (
        <p className='text-red-600 text-sm' role='alert'>
          {error}
        </p>
      )}
    </div>
  );
};

// Enhanced Alert Component
interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'danger';
  title?: string;
  closable?: boolean;
  onClose?: () => void;
  icon?: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({
  // const id = useId(); // Removed - can't use hooks in objects
  children,
  variant = 'info',
  title,
  closable = false,
  onClose,
  icon,
  className = '',
  ...props
}) => {
  const [isVisible, setIsVisible] = React.useState(true);

  const handleClose = () => {
    setIsVisible(false);
    onClose?.();
  };

  const baseClasses = 'p-4 rounded-md border transition-all duration-200';

  const variantClasses = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    danger: 'bg-red-50 border-red-200 text-red-800',
  };

  const iconColors = {
    info: 'text-blue-400',
    success: 'text-green-400',
    warning: 'text-yellow-400',
    danger: 'text-red-400',
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className={clsx(baseClasses, variantClasses[variant], className)} role='alert' {...props}>
      <div className='flex'>
        {icon && (
          <div className='flex-shrink-0'>
            <span className={iconColors[variant]}>{icon}</span>
          </div>
        )}
        <div className={clsx('flex-1', icon && 'ml-3')}>
          {title && <h3 className='mb-1 font-medium text-sm'>{title}</h3>}
          <div className='text-sm'>{children}</div>
        </div>
        {closable && (
          <div className='ml-auto pl-3'>
            <button
              type='button'
              onClick={handleClose}
              onKeyDown={(e) => e.key === 'Enter' && handleClose}
              className={clsx(
                'inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2',
                iconColors[variant],
                'hover:bg-opacity-20'
              )}
              aria-label='Close alert'
            >
              <svg aria-label='icon' className='h-4 w-4' fill='currentColor' viewBox='0 0 20 20'>
                <title>Icon</title>
                <path
                  fillRule='evenodd'
                  d='M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z'
                  clipRule='evenodd'
                />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Progress Component
interface ProgressProps {
  value?: number;
  max?: number;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  showValue?: boolean;
  indeterminate?: boolean;
  className?: string;
}

export const Progress: React.FC<ProgressProps> = ({
  // const id = useId(); // Removed - can't use hooks in objects
  value = 0,
  max = 100,
  variant = 'default',
  size = 'md',
  label,
  showValue = false,
  indeterminate = false,
  className = '',
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const baseClasses = 'w-full bg-gray-200 rounded-full overflow-hidden';

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const variantClasses = {
    default: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    danger: 'bg-red-600',
  };

  return (
    <div className={clsx('space-y-1', className)}>
      {(label || showValue) && (
        <div className='flex justify-between text-sm'>
          {label && <span className='font-medium text-gray-700'>{label}</span>}
          {showValue && !indeterminate && (
            <span className='text-gray-500'>{Math.round(percentage)}%</span>
          )}
        </div>
      )}
      <div
        className={clsx(baseClasses, sizeClasses[size])}
        role='progressbar'
        aria-valuenow={indeterminate ? undefined : value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label}
      >
        <div
          className={clsx(
            sizeClasses[size],
            variantClasses[variant],
            'transition-all duration-300 ease-out',
            {
              'animate-pulse': indeterminate,
            }
          )}
          style={{
            width: indeterminate ? '100%' : `${percentage}%`,
            animation: indeterminate ? 'progressIndeterminate 2s ease-in-out infinite' : undefined,
          }}
        />
      </div>
    </div>
  );
};

// Enhanced Tooltip Component
interface TooltipProps {
  children: React.ReactNode;
  content: React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({
  // const id = useId(); // Removed - can't use hooks in objects
  children,
  content,
  placement = 'top',
  delay = 300,
  className = '',
}) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const [timeoutId, setTimeoutId] = React.useState<NodeJS.Timeout | null>(null);

  const showTooltip = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    const id = setTimeout(() => setIsVisible(true), delay);
    setTimeoutId(id);
  };

  const hideTooltip = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    setIsVisible(false);
  };

  const placementClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2',
  };

  return (
    <div
      className='relative inline-block'
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      {isVisible && (
        <div
          className={clsx(
            'absolute z-50 rounded bg-gray-900 px-2 py-1 text-sm text-white shadow-lg',
            'animate-fade-in',
            placementClasses[placement],
            className
          )}
          role='tooltip'
        >
          {content}
          <div
            className={clsx('absolute h-2 w-2 rotate-45 transform bg-gray-900', {
              '-translate-x-1/2 -mt-1 top-full left-1/2': placement === 'top',
              '-translate-x-1/2 -mb-1 bottom-full left-1/2': placement === 'bottom',
              '-translate-y-1/2 -ml-1 top-1/2 left-full': placement === 'left',
              '-translate-y-1/2 -mr-1 top-1/2 right-full': placement === 'right',
            })}
          />
        </div>
      )}
    </div>
  );
};
