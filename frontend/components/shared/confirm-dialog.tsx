"use client";

import { useRef, useState, type ElementType } from "react";
import { AlertTriangle, Trash2, Info, CheckCircle } from "lucide-react";
import { Button, Modal } from "@dotmac/core";
import { cn } from "@/lib/utils";

type DialogVariant = "danger" | "warning" | "info" | "success";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  variant?: DialogVariant;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
  destructive?: boolean;
}

const variantConfig: Record<
  DialogVariant,
  {
    icon: ElementType;
    iconClass: string;
    bgClass: string;
  }
> = {
  danger: {
    icon: Trash2,
    iconClass: "text-status-error",
    bgClass: "bg-status-error/15",
  },
  warning: {
    icon: AlertTriangle,
    iconClass: "text-status-warning",
    bgClass: "bg-status-warning/15",
  },
  info: {
    icon: Info,
    iconClass: "text-status-info",
    bgClass: "bg-status-info/15",
  },
  success: {
    icon: CheckCircle,
    iconClass: "text-status-success",
    bgClass: "bg-status-success/15",
  },
};

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  variant = "danger",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
  loading = false,
  destructive = false,
}: ConfirmDialogProps) {
  const [isLoading, setIsLoading] = useState(false);
  const config = variantConfig[variant];
  const Icon = config.icon;

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    onCancel?.();
    onOpenChange(false);
  };

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <div className="p-6 max-w-md">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div
            className={cn(
              "w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0",
              config.bgClass
            )}
          >
            <Icon className={cn("w-6 h-6", config.iconClass)} />
          </div>

          {/* Content */}
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              {title}
            </h3>
            <p className="text-sm text-text-muted">{description}</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 mt-6">
          <Button
            variant="ghost"
            onClick={handleCancel}
            disabled={isLoading || loading}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={destructive || variant === "danger" ? "destructive" : "default"}
            onClick={handleConfirm}
            disabled={isLoading || loading}
          >
            {isLoading || loading ? "Processing..." : confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// Hook for easier usage
export function useConfirmDialog() {
  const [state, setState] = useState<{
    open: boolean;
    title: string;
    description: string;
    variant: DialogVariant;
    onConfirm: () => void | Promise<void>;
  }>({
    open: false,
    title: "",
    description: "",
    variant: "danger",
    onConfirm: () => {},
  });

  const resolveRef = useRef<((value: boolean) => void) | null>(null);

  const settle = (value: boolean) => {
    const resolve = resolveRef.current;
    if (!resolve) return;
    resolveRef.current = null;
    resolve(value);
  };

  const confirm = (options: {
    title: string;
    description: string;
    variant?: DialogVariant;
  }): Promise<boolean> => {
    return new Promise((resolve) => {
      if (resolveRef.current) {
        resolveRef.current(false);
        resolveRef.current = null;
      }

      resolveRef.current = resolve;
      setState({
        open: true,
        title: options.title,
        description: options.description,
        variant: options.variant || "danger",
        onConfirm: () => settle(true),
      });
    });
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      settle(false);
    }
    setState((s) => ({ ...s, open }));
  };

  const dialog = (
    <ConfirmDialog
      open={state.open}
      onOpenChange={handleOpenChange}
      title={state.title}
      description={state.description}
      variant={state.variant}
      onConfirm={state.onConfirm}
    />
  );

  return { confirm, dialog };
}
