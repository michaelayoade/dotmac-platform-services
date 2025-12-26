/**
 * @dotmac/core/styled
 *
 * Pre-styled UI components with DotMac design system
 */

// Button
export {
  StyledButton,
  PortalButton,
  IconButton,
  buttonVariants,
  type ButtonProps,
  type PortalButtonProps,
  type IconButtonProps,
} from "./Button";

// Input
export {
  StyledInput,
  SearchInput,
  PasswordInput,
  inputVariants,
  type InputProps,
  type SearchInputProps,
  type PasswordInputProps,
} from "./Input";

// Card
export {
  StyledCard,
  MetricCard,
  StatusCard,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  cardVariants,
  type CardProps,
  type MetricCardProps,
  type StatusCardProps,
} from "./Card";

// EmptyState
export { EmptyState, type EmptyStateProps } from "./EmptyState";

// ErrorState
export { ErrorState, type ErrorStateProps } from "./ErrorState";

// StatusBadge
export {
  StatusBadge,
  ActiveBadge,
  InactiveBadge,
  PendingBadge,
  ErrorBadge,
  type StatusBadgeProps,
  type StatusVariant,
  type StatusSize,
  type PresetStatusBadgeProps,
} from "./StatusBadge";
