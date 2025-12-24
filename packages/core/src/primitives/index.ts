/**
 * @dotmac/core/primitives
 *
 * Headless, unstyled UI primitives
 */

// Button
export {
  Button,
  ButtonGroup,
  buttonVariants,
  type ButtonProps,
  type ButtonGroupProps,
} from "./Button";

// Input
export {
  Input,
  InputGroup,
  inputVariants,
  type InputProps,
  type InputGroupProps,
} from "./Input";

// Card
export {
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
} from "./Card";

// Modal/Dialog
export {
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
} from "./Modal";

// Select
export {
  Select,
  SelectItem,
  type SelectProps,
  type SelectOption,
} from "./Select";

// Toast
export {
  ToastProvider,
  useToast,
  ToastViewport,
  type ToastMessage,
  type ToastVariant,
} from "./Toast";
