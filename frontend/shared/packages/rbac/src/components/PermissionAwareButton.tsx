import React from 'react';
import { useAccessControl } from '../hooks/useAccessControl';

interface PermissionAwareButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  permissions?: string | string[];
  roles?: string | string[];
  requireAll?: boolean;
  hideIfNoAccess?: boolean;
  disableIfNoAccess?: boolean;
  fallbackText?: string;
  onAccessDenied?: () => void;
}

/**
 * Button component that automatically handles permission-based visibility and disabled states
 *
 * @example
 * <PermissionAwareButton
 *   permissions="users:delete"
 *   disableIfNoAccess={true}
 *   onClick={deleteUser}
 * >
 *   Delete User
 * </PermissionAwareButton>
 */
export function PermissionAwareButton({
  children,
  permissions,
  roles,
  requireAll = false,
  hideIfNoAccess = false,
  disableIfNoAccess = true,
  fallbackText,
  onAccessDenied,
  onClick,
  disabled,
  className = '',
  ...props
}: PermissionAwareButtonProps) {
  const { checkAccess } = useAccessControl();

  const hasAccess = checkAccess(permissions, roles, requireAll);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!hasAccess) {
      onAccessDenied?.();
      return;
    }
    onClick?.(e);
  };

  // Hide button if no access and hideIfNoAccess is true
  if (!hasAccess && hideIfNoAccess) {
    return null;
  }

  // Determine if button should be disabled
  const isDisabled = disabled || (!hasAccess && disableIfNoAccess);

  // Apply visual styling for disabled state due to permissions
  const buttonClassName = `${className} ${
    !hasAccess && disableIfNoAccess ? 'opacity-50 cursor-not-allowed' : ''
  }`.trim();

  return (
    <button
      {...props}
      disabled={isDisabled}
      onClick={handleClick}
      className={buttonClassName}
      title={!hasAccess ? 'Insufficient permissions' : props.title}
    >
      {!hasAccess && fallbackText ? fallbackText : children}
    </button>
  );
}

/**
 * Specialized buttons for common actions
 */
export const CreateButton = (
  props: Omit<PermissionAwareButtonProps, 'permissions'> & { resource: string }
) => (
  <PermissionAwareButton
    {...props}
    permissions={`${props.resource}:create`}
    className={`bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded ${props.className || ''}`}
  />
);

export const EditButton = (
  props: Omit<PermissionAwareButtonProps, 'permissions'> & { resource: string }
) => (
  <PermissionAwareButton
    {...props}
    permissions={`${props.resource}:update`}
    className={`bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded ${props.className || ''}`}
  />
);

export const DeleteButton = (
  props: Omit<PermissionAwareButtonProps, 'permissions'> & { resource: string }
) => (
  <PermissionAwareButton
    {...props}
    permissions={`${props.resource}:delete`}
    className={`bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded ${props.className || ''}`}
  />
);

export const AdminButton = (props: Omit<PermissionAwareButtonProps, 'roles'>) => (
  <PermissionAwareButton
    {...props}
    roles='admin'
    className={`bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded ${props.className || ''}`}
  />
);
