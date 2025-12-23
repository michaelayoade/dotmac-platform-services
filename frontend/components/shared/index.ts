// Shared Components
// Reusable UI components used across the dashboard

export { PageHeader } from "./page-header";
export { StatusBadge, ActiveBadge, PendingBadge, ErrorBadge, ProcessingBadge } from "./status-badge";
export { EmptyState } from "./empty-state";
export {
  Skeleton,
  TableSkeleton,
  CardSkeleton,
  DashboardSkeleton,
  FormSkeleton
} from "./loading-skeleton";
export { ConfirmDialog, useConfirmDialog } from "./confirm-dialog";
export { SearchInput } from "./search-input";
export { Avatar, AvatarGroup } from "./avatar";
export { ThemeToggle, ThemeToggleSimple } from "./theme-toggle";
export {
  ErrorBoundary,
  ErrorFallback,
  QueryErrorFallback,
  InlineError,
} from "./error-boundary";
