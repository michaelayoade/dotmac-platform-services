import React from 'react';
import { useAccessControl } from '../hooks/useAccessControl';

interface PermissionAwareFormProps extends React.FormHTMLAttributes<HTMLFormElement> {
  permissions?: string | string[];
  roles?: string | string[];
  requireAll?: boolean;
  readOnlyIfNoAccess?: boolean;
  hideIfNoAccess?: boolean;
  fallback?: React.ReactNode;
  onAccessDenied?: () => void;
}

/**
 * Form component that handles permission-based read-only and visibility states
 */
export function PermissionAwareForm({
  children,
  permissions,
  roles,
  requireAll = false,
  readOnlyIfNoAccess = true,
  hideIfNoAccess = false,
  fallback = null,
  onAccessDenied,
  onSubmit,
  className = '',
  ...props
}: PermissionAwareFormProps) {
  const { checkAccess } = useAccessControl();

  const hasAccess = checkAccess(permissions, roles, requireAll);

  if (!hasAccess && hideIfNoAccess) {
    return <>{fallback}</>;
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    if (!hasAccess) {
      e.preventDefault();
      onAccessDenied?.();
      return;
    }
    onSubmit?.(e);
  };

  // Apply read-only styling if no access
  const formClassName = `${className} ${
    !hasAccess && readOnlyIfNoAccess ? 'pointer-events-none opacity-75' : ''
  }`.trim();

  return (
    <form {...props} onSubmit={handleSubmit} className={formClassName}>
      {children}
      {!hasAccess && readOnlyIfNoAccess && (
        <div className='absolute inset-0 bg-gray-200 bg-opacity-50 flex items-center justify-center pointer-events-none'>
          <span className='text-gray-600 font-medium'>Read-only: Insufficient permissions</span>
        </div>
      )}
    </form>
  );
}

interface PermissionAwareInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  permissions?: string | string[];
  roles?: string | string[];
  requireAll?: boolean;
  readOnlyIfNoAccess?: boolean;
}

/**
 * Input component that becomes read-only based on permissions
 */
export function PermissionAwareInput({
  permissions,
  roles,
  requireAll = false,
  readOnlyIfNoAccess = true,
  readOnly,
  className = '',
  ...props
}: PermissionAwareInputProps) {
  const { checkAccess } = useAccessControl();

  const hasAccess = checkAccess(permissions, roles, requireAll);
  const isReadOnly = readOnly || (!hasAccess && readOnlyIfNoAccess);

  const inputClassName = `${className} ${
    !hasAccess && readOnlyIfNoAccess ? 'bg-gray-100 cursor-not-allowed' : ''
  }`.trim();

  return (
    <input
      {...props}
      readOnly={isReadOnly}
      className={inputClassName}
      title={!hasAccess ? 'Read-only: Insufficient permissions' : props.title}
    />
  );
}

interface PermissionAwareSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  permissions?: string | string[];
  roles?: string | string[];
  requireAll?: boolean;
  disableIfNoAccess?: boolean;
}

/**
 * Select component that becomes disabled based on permissions
 */
export function PermissionAwareSelect({
  permissions,
  roles,
  requireAll = false,
  disableIfNoAccess = true,
  disabled,
  className = '',
  ...props
}: PermissionAwareSelectProps) {
  const { checkAccess } = useAccessControl();

  const hasAccess = checkAccess(permissions, roles, requireAll);
  const isDisabled = disabled || (!hasAccess && disableIfNoAccess);

  const selectClassName = `${className} ${
    !hasAccess && disableIfNoAccess ? 'bg-gray-100 cursor-not-allowed opacity-75' : ''
  }`.trim();

  return (
    <select
      {...props}
      disabled={isDisabled}
      className={selectClassName}
      title={!hasAccess ? 'Disabled: Insufficient permissions' : props.title}
    />
  );
}
