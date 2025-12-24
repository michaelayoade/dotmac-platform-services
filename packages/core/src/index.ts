/**
 * @dotmac/core
 *
 * Core UI components - headless primitives and styled components
 *
 * @example
 * ```tsx
 * // Use primitives for custom styling
 * import { Button, Card, Input } from '@dotmac/core/primitives';
 *
 * // Use styled components for quick implementation
 * import { StyledButton, MetricCard, SearchInput } from '@dotmac/core/styled';
 *
 * // Or import everything
 * import { Button, StyledButton, Card, MetricCard } from '@dotmac/core';
 * ```
 */

// ============================================================================
// Primitives (Headless)
// ============================================================================

export {
  // Button
  Button,
  ButtonGroup,
  buttonVariants,
  type ButtonProps,
  type ButtonGroupProps,

  // Input
  Input,
  InputGroup,
  inputVariants,
  type InputProps,
  type InputGroupProps,

  // Card
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  cardVariants,
  type CardProps,
  type CardHeaderProps,
  type CardTitleProps,
  type CardDescriptionProps,
  type CardContentProps,
  type CardFooterProps,

  // Modal/Dialog
  Dialog,
  DialogTrigger,
  DialogPortal,
  DialogClose,
  DialogOverlay,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  Modal,
  type DialogContentProps,
  type ModalProps,

  // Select
  Select,
  SelectItem,
  type SelectProps,
  type SelectOption,

  // Toast
  ToastProvider,
  ToastViewport,
  useToast,
  type ToastMessage,
  type ToastVariant,
} from "./primitives";

// ============================================================================
// Styled Components
// ============================================================================

export {
  // Button
  StyledButton,
  PortalButton,
  IconButton,
  type PortalButtonProps,
  type IconButtonProps,

  // Input
  StyledInput,
  SearchInput,
  PasswordInput,
  type SearchInputProps,
  type PasswordInputProps,

  // Card
  StyledCard,
  MetricCard,
  StatusCard,
  type MetricCardProps,
  type StatusCardProps,
} from "./styled";

// ============================================================================
// Utilities
// ============================================================================

export { cn } from "./utils/cn";

// ============================================================================
// Re-export design tokens for convenience
// ============================================================================

export {
  ThemeProvider,
  useTheme,
  useThemeColors,
  useThemeSpacing,
  colors,
  spacing,
  fontFamily,
  fontSize,
  shadows,
} from "@dotmac/design-tokens";

// ============================================================================
// Version
// ============================================================================

export const version = "1.0.0";
