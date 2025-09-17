/**
 * Admin Portal Styled Components
 *
 * High-density, professional components optimized for power users and
 * data-intensive admin interfaces. Emphasizes functionality over aesthetics.
 */

// Re-export primitives with admin theme context
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
  // Button from primitives (for compatibility)
  Button,
  Center,
  ChartContainer,
  Checkbox,
  ConfirmationModal,
  // Layout Components
  Container,
  chartUtils,
  createValidationRules,
  Dashboard,
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
  // Input Component
  Input,
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
  // Table Primitives (for custom implementations)
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
// Theme utilities
export { cn, createPortalTheme } from '../lib/utils';
export type { AdminButtonProps } from './Button';
// Button Components
export { AdminButton, adminButtonVariants } from './Button';
export type {
  AdminCardContentProps,
  AdminCardFooterProps,
  AdminCardHeaderProps,
  AdminCardProps,
} from './Card';
// Card Components
export {
  AdminCard,
  AdminCardContent,
  AdminCardDescription,
  AdminCardFooter,
  AdminCardHeader,
  AdminCardTitle,
} from './Card';
// export type { AdminDataTableProps } from './DataTable';
// Data Table Components - Disabled due to import issues
// export { AdminDataTable } from './DataTable';
export type { AdminInputProps } from './Input';
// Input Components
export { AdminInput, adminInputVariants } from './Input';

// Import the function explicitly for use
import { createPortalTheme } from '../lib/utils';

// Admin theme instance
export const adminTheme = createPortalTheme('admin');
