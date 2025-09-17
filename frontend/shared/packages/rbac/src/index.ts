// Main exports for the RBAC package

// Core components
export {
  ProtectedComponent,
  AdminOnly,
  ManagerOnly,
  AuthenticatedOnly,
} from './components/ProtectedComponent';
export { ConditionalRender, ShowIfAny, ShowIfAll, HideIf } from './components/ConditionalRender';

// Permission-aware UI components
export {
  PermissionAwareButton,
  CreateButton,
  EditButton,
  DeleteButton,
  AdminButton,
} from './components/PermissionAwareButton';
export {
  PermissionAwareForm,
  PermissionAwareInput,
  PermissionAwareSelect,
} from './components/PermissionAwareForm';

// Routing components
export {
  ProtectedRoute,
  AdminRoute,
  ManagerRoute,
  AuthenticatedRoute,
  withRouteProtection,
} from './routing/ProtectedRoute';
export {
  RouteGuardProvider,
  routeGuardManager,
  useRouteGuard,
  routeGuards,
} from './routing/RouteGuard';

// Hooks
export { usePermissions } from './hooks/usePermissions';
export { useAccessControl } from './hooks/useAccessControl';

// Decorators and HOCs
export {
  withAccessControl,
  accessControlDecorators,
  requiresPermission,
  withMethodProtection,
} from './decorators/withAccessControl';
export {
  createProtected,
  createResourceProtected,
  decoratorUtils,
  commonDecorators,
} from './decorators/PermissionDecorators';

// Utilities
export {
  defaultPortalRoles,
  matchesPermissionPattern,
  getEffectivePermissions,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  getPortalPermissions,
  groupPermissionsByResource,
  isValidRole,
  getUserRoleLevel,
  compareRoleLevels,
  suggestPermissions,
} from './utils/permissionUtils';

// Types
export type {
  AccessControlProps,
  RouteGuardProps,
  PermissionContextValue,
  WithAccessControlOptions,
  AccessControlDecoratorOptions,
  PortalRoleConfig,
  PermissionCheck,
  AccessRule,
  User,
  UserRole,
  Permission,
  PermissionType,
  PortalType,
} from './types';

// Re-export commonly used auth types for convenience
export type { User, UserRole, Permission, PermissionType, PortalType } from '@dotmac/auth';
