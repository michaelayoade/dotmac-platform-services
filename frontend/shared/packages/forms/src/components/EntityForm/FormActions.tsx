'use client';

import React from 'react';
import { Save, X, Copy, Trash2, Loader2 } from 'lucide-react';
import { FormMode, PortalVariant, PortalTheme, EntityFormConfig } from '../../types';
import { cn } from '../../utils/cn';

interface FormActionsProps {
  config?: EntityFormConfig['actions'];
  mode: FormMode;
  portalVariant: PortalVariant;
  theme: PortalTheme;
  onCancel?: () => void;
  isLoading: boolean;
  isValid: boolean;
  isDirty: boolean;
  className?: string;
}

export function FormActions({
  config,
  mode,
  portalVariant,
  theme,
  onCancel,
  isLoading,
  isValid,
  isDirty,
  className,
}: FormActionsProps) {
  // Default action configurations
  const defaultActions = {
    primary: {
      label: mode === 'create' ? 'Create' : mode === 'edit' ? 'Save Changes' : 'Save',
      variant: 'primary' as const,
    },
    secondary: [
      {
        label: 'Cancel',
        variant: 'secondary' as const,
        action: 'cancel' as const,
      },
    ],
  };

  const actions = config || defaultActions;
  const primaryAction = actions.primary || defaultActions.primary;
  const secondaryActions = actions.secondary || defaultActions.secondary;

  const handleSecondaryAction = (action: any) => {
    switch (action.action) {
      case 'cancel':
        onCancel?.();
        break;
      case 'reset':
        // Form reset is handled by react-hook-form
        break;
      case 'duplicate':
        // Custom duplicate logic would be handled by parent
        break;
      case 'delete':
        // Custom delete logic would be handled by parent
        break;
      default:
        // Custom action
        action.onClick?.();
        break;
    }
  };

  const getButtonIcon = (action: any) => {
    switch (action.action) {
      case 'cancel':
        return <X className='h-4 w-4' />;
      case 'duplicate':
        return <Copy className='h-4 w-4' />;
      case 'delete':
        return <Trash2 className='h-4 w-4' />;
      default:
        return null;
    }
  };

  const getButtonStyles = (variant: string) => {
    const baseStyles =
      'inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';

    switch (variant) {
      case 'primary':
        return cn(
          baseStyles,
          'text-white shadow-sm',
          theme.components.button,
          isLoading && 'opacity-50 cursor-not-allowed',
          !isValid && 'opacity-50 cursor-not-allowed'
        );

      case 'secondary':
        return cn(
          baseStyles,
          'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
          'focus:ring-gray-500',
          isLoading && 'opacity-50 cursor-not-allowed'
        );

      case 'danger':
        return cn(
          baseStyles,
          'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
          isLoading && 'opacity-50 cursor-not-allowed'
        );

      default:
        return cn(
          baseStyles,
          'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
          'focus:ring-gray-500'
        );
    }
  };

  // Don't show actions in view mode unless explicitly configured
  if (mode === 'view' && !config) {
    return null;
  }

  return (
    <div
      className={cn('flex items-center justify-end gap-3 pt-6 border-t border-gray-200', className)}
    >
      {/* Secondary Actions */}
      {secondaryActions.map((action, index) => {
        const Icon = getButtonIcon(action);

        return (
          <button
            key={index}
            type='button'
            onClick={() => handleSecondaryAction(action)}
            disabled={isLoading}
            className={getButtonStyles(action.variant)}
          >
            {Icon}
            {action.label}
          </button>
        );
      })}

      {/* Primary Action */}
      <button
        type='submit'
        disabled={isLoading || !isValid || (mode === 'edit' && !isDirty)}
        className={getButtonStyles(primaryAction.variant)}
      >
        {isLoading ? <Loader2 className='h-4 w-4 animate-spin' /> : <Save className='h-4 w-4' />}
        {primaryAction.label}
      </button>

      {/* Save Status Indicator */}
      {mode === 'edit' && !isLoading && (
        <div className='text-sm text-gray-500'>
          {!isDirty && isValid ? (
            <span className='text-green-600'>✓ All changes saved</span>
          ) : isDirty ? (
            <span className='text-amber-600'>• Unsaved changes</span>
          ) : null}
        </div>
      )}
    </div>
  );
}
