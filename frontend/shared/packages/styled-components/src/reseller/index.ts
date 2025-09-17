/**
 * Reseller Portal Styled Components
 *
 * Professional, brandable components optimized for partner/reseller
 * interfaces. Balances business aesthetics with customization flexibility.
 */

// Re-export primitives with reseller theme context
export {
  // Core Components
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  Input,

  // Layout Components
  Container,
  Grid,
  GridItem,
  Stack,
  VStack,
  HStack,
  Center,
  Spacer,

  // Form Components
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
  Checkbox,
  Radio,
  RadioGroup,
  Select,
  Textarea,

  // Feedback Components
  Alert,
  AlertDescription,
  AlertTitle,
  Loading,
  Progress,
  Toast,
  ToastProvider,
  ToastTitle,
  ToastContent,
  ToastDescription,

  // Navigation Components
  Navbar,
  Sidebar,

  // Modal Components
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalBody,
  ModalFooter,
  ModalClose,
  ModalProvider,

  // Chart Components
  AreaChart,
  BarChart,
  LineChart,
  PieChart,

  // Utility Functions
  clsx,

  // Hooks
  useModal,
  useToast,
  useLocalStorage,
  useMediaQuery,
} from '@dotmac/primitives';

// Re-export shared components
export { Avatar } from '../shared';
// Theme utilities
export { cn, createPortalTheme } from '../lib/utils';
export type { ResellerButtonProps } from './Button';
// Button Components
export { ResellerButton, resellerButtonVariants } from './Button';
export type {
  ResellerCardContentProps,
  ResellerCardFooterProps,
  ResellerCardHeaderProps,
  ResellerCardProps,
} from './Card';
// Card Components
export {
  ResellerCard,
  ResellerCardContent,
  ResellerCardDescription,
  ResellerCardFooter,
  ResellerCardHeader,
  ResellerCardTitle,
} from './Card';
export type { ResellerInputProps } from './Input';
// Input Components
export { ResellerInput, resellerInputVariants } from './Input';

// Import the function explicitly for use
import { createPortalTheme } from '../lib/utils';

// Reseller theme instance
export const resellerTheme = createPortalTheme('reseller');
