/**
 * Shared Styled Components
 *
 * Universal components that work across all portals with adaptive theming.
 * These components maintain consistent behavior while adapting their
 * appearance to the active portal's design language.
 */

// Re-export primitives for convenience
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
  // Form Components (including Button)
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
export type { AvatarGroupProps, AvatarProps } from './Avatar';
// Avatar Components
export { Avatar, AvatarGroup, avatarVariants } from './Avatar';
export type { BadgeProps } from './Badge';
// Badge Components
export { Badge, badgeVariants } from './Badge';
export type { QuickTooltipProps, TooltipContentProps, TooltipWithIconProps } from './Tooltip';
// Tooltip Components
export {
  QuickTooltip,
  Tooltip,
  TooltipContent,
  TooltipPortal,
  TooltipProvider,
  TooltipTrigger,
  TooltipWithIcon,
  tooltipVariants,
} from './Tooltip';
