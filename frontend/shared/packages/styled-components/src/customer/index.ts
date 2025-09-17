/**
 * Customer Portal Styled Components
 *
 * Friendly, accessible components optimized for end-users and customer
 * self-service interfaces. Emphasizes clarity and ease of use.
 */

// Re-export primitives with customer theme context (excluding conflicting Card)
export {
  Alert,
  AlertDescription,
  AlertTitle,
  ARIA_ROLES,
  AreaChart,
  BarChart,
  BottomSheet,
  Breadcrumb,
  BreadcrumbEllipsis,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  Center,
  ChartContainer,
  Checkbox,
  ConfirmationModal,
  // Layout Components
  Container,
  chartUtils,
  createValidationRules,
  Dashboard,
  // Table Components
  DataTable,
  Divider,
  Drawer,
  // Form Components
  Form,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormModal,
  Grid,
  GridItem,
  HStack,
  // Utility Functions
  isBrowser,
  isServer,
  KEYS,
  // Chart Components
  LineChart,
  Loading,
  LoadingSkeleton,
  MetricCard,
  // Modal Components
  Modal,
  ModalBody,
  ModalClose,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  ModalPortal,
  ModalProvider,
  ModalTitle,
  ModalTrigger,
  Navbar,
  NavigationItem,
  NavigationLink,
  NavigationMenu,
  // Navigation Components
  NavigationProvider,
  PieChart,
  Progress,
  Radio,
  RadioGroup,
  Section,
  Select,
  Sidebar,
  Spacer,
  Stack,
  StatusIndicator,
  TabItem,
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
  TabNavigation,
  Textarea,
  Toast,
  ToastAction,
  ToastClose,
  ToastContent,
  ToastDescription,
  // Feedback Components
  ToastProvider,
  ToastTitle,
  ToastViewport,
  useAriaExpanded,
  useAriaSelection,
  useClientEffect,
  useFocusTrap,
  useFormContext,
  useId,
  useIsHydrated,
  useKeyboardNavigation,
  useLocalStorage,
  useMediaQuery,
  useModal,
  useModalContext,
  useNavigation,
  usePrefersReducedMotion,
  useScreenReaderAnnouncement,
  useSessionStorage,
  useToast,
  useUserPreferences,
  VStack,
  validationPatterns,
} from '@dotmac/primitives';

// Also export the Card from primitives as PrimitiveCard for compatibility
export { Card as PrimitiveCard } from '@dotmac/primitives';

// Export component aliases for easier importing
export { CustomerButton as Button } from './Button';
export { CustomerCard as Card } from './Card';
export { CustomerInput as Input } from './Input';

// Note: Avatar component not available in primitives yet
// Theme utilities
export { cn, createPortalTheme } from '../lib/utils';
export type { CustomerButtonProps } from './Button';
// Button Components
export { CustomerButton, customerButtonVariants } from './Button';
export type {
  CustomerCardContentProps,
  CustomerCardFooterProps,
  CustomerCardHeaderProps,
  CustomerCardProps,
} from './Card';
// Card Components
export {
  CustomerCard,
  CustomerCardContent,
  CustomerCardDescription,
  CustomerCardFooter,
  CustomerCardHeader,
  CustomerCardTitle,
} from './Card';
export type { CustomerInputProps } from './Input';
// Input Components
export { CustomerInput, customerInputVariants } from './Input';

// Import the function explicitly for use
import { createPortalTheme } from '../lib/utils';

// Customer theme instance
export const customerTheme = createPortalTheme('customer');
