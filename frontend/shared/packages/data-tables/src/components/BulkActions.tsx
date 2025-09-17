/**
 * BulkActions Component
 * Universal bulk operations for selected table rows with portal theming
 */

import React, { useState } from 'react';
import {
  Check,
  X,
  Trash2,
  Download,
  Edit,
  Archive,
  MoreHorizontal,
  AlertTriangle,
} from 'lucide-react';
import {
  Button,
  Checkbox,
  Badge,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@dotmac/primitives';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import type { BulkOperation, SelectionState, PortalVariant } from '../types';

const bulkActionsVariants = cva(
  'flex items-center gap-3 p-3 bg-white border-b transition-all duration-200',
  {
    variants: {
      portal: {
        admin: 'border-blue-200 bg-blue-50/50',
        customer: 'border-green-200 bg-green-50/50',
        reseller: 'border-purple-200 bg-purple-50/50',
        technician: 'border-orange-200 bg-orange-50/50',
        management: 'border-red-200 bg-red-50/50',
      },
      state: {
        visible: 'opacity-100 translate-y-0',
        hidden: 'opacity-0 -translate-y-2 pointer-events-none',
      },
    },
    defaultVariants: {
      portal: 'admin',
      state: 'visible',
    },
  }
);

const actionButtonVariants = cva(
  'inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
  {
    variants: {
      variant: {
        primary: '',
        secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
        danger: 'bg-red-100 text-red-700 hover:bg-red-200 focus:ring-red-500',
      },
      portal: {
        admin: {
          primary: 'bg-blue-100 text-blue-700 hover:bg-blue-200 focus:ring-blue-500',
        },
        customer: {
          primary: 'bg-green-100 text-green-700 hover:bg-green-200 focus:ring-green-500',
        },
        reseller: {
          primary: 'bg-purple-100 text-purple-700 hover:bg-purple-200 focus:ring-purple-500',
        },
        technician: {
          primary: 'bg-orange-100 text-orange-700 hover:bg-orange-200 focus:ring-orange-500',
        },
        management: {
          primary: 'bg-red-100 text-red-700 hover:bg-red-200 focus:ring-red-500',
        },
      },
    },
    defaultVariants: {
      variant: 'primary',
      portal: 'admin',
    },
  }
);

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'info',
}) => {
  if (!isOpen) return null;

  const iconMap = {
    danger: <Trash2 className='w-5 h-5 text-red-500' />,
    warning: <AlertTriangle className='w-5 h-5 text-orange-500' />,
    info: <Check className='w-5 h-5 text-blue-500' />,
  };

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center'>
      <div className='fixed inset-0 bg-black/50' onClick={onClose} />
      <div className='relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6'>
        <div className='flex items-start gap-3'>
          {iconMap[variant]}
          <div className='flex-1'>
            <h3 className='text-lg font-medium text-gray-900 mb-2'>{title}</h3>
            <p className='text-sm text-gray-600 mb-4'>{message}</p>
            <div className='flex gap-2 justify-end'>
              <Button variant='outline' onClick={onClose}>
                {cancelText}
              </Button>
              <Button
                variant={variant === 'danger' ? 'destructive' : 'default'}
                onClick={() => {
                  onConfirm();
                  onClose();
                }}
              >
                {confirmText}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface BulkActionsProps<TData = any> {
  selectedRows: TData[];
  totalRows: number;
  bulkOperations: BulkOperation<TData>[];
  onSelectAll: () => void;
  onDeselectAll: () => void;
  isAllSelected: boolean;
  isSomeSelected: boolean;
  portal?: PortalVariant;
  className?: string;
  maxVisibleActions?: number;
}

export const BulkActions = <TData extends any>({
  selectedRows,
  totalRows,
  bulkOperations,
  onSelectAll,
  onDeselectAll,
  isAllSelected,
  isSomeSelected,
  portal = 'admin',
  className,
  maxVisibleActions = 3,
}: BulkActionsProps<TData>) => {
  const [confirmationModal, setConfirmationModal] = useState<{
    isOpen: boolean;
    operation: BulkOperation<TData> | null;
    title: string;
    message: string;
  }>({
    isOpen: false,
    operation: null,
    title: '',
    message: '',
  });

  const selectedCount = selectedRows.length;
  const hasSelection = selectedCount > 0;

  // Filter operations based on selection constraints
  const availableOperations = bulkOperations.filter((op) => {
    if (op.minSelection && selectedCount < op.minSelection) return false;
    if (op.maxSelection && selectedCount > op.maxSelection) return false;
    return true;
  });

  // Split operations into primary and overflow
  const primaryOperations = availableOperations.slice(0, maxVisibleActions);
  const overflowOperations = availableOperations.slice(maxVisibleActions);

  // Handle bulk operation execution
  const executeBulkOperation = async (operation: BulkOperation<TData>) => {
    if (operation.requiresConfirmation) {
      const message =
        typeof operation.confirmationMessage === 'function'
          ? operation.confirmationMessage(selectedCount)
          : operation.confirmationMessage ||
            `Are you sure you want to ${operation.label.toLowerCase()} ${selectedCount} item${selectedCount > 1 ? 's' : ''}?`;

      setConfirmationModal({
        isOpen: true,
        operation,
        title: `Confirm ${operation.label}`,
        message,
      });
      return;
    }

    try {
      await operation.action(selectedRows);
    } catch (error) {
      console.error(`Bulk operation "${operation.label}" failed:`, error);
      // TODO: Add toast notification
    }
  };

  const handleConfirmation = async () => {
    if (confirmationModal.operation) {
      try {
        await confirmationModal.operation.action(selectedRows);
      } catch (error) {
        console.error(`Bulk operation "${confirmationModal.operation.label}" failed:`, error);
        // TODO: Add toast notification
      }
    }
  };

  return (
    <>
      <div
        className={clsx(
          bulkActionsVariants({
            portal,
            state: hasSelection ? 'visible' : 'hidden',
          }),
          className
        )}
      >
        {/* Selection controls */}
        <div className='flex items-center gap-3'>
          <Checkbox
            checked={isAllSelected}
            indeterminate={isSomeSelected && !isAllSelected}
            onChange={(e) => {
              if (e.target.checked) {
                onSelectAll();
              } else {
                onDeselectAll();
              }
            }}
            aria-label='Select all rows'
          />

          <div className='flex items-center gap-2'>
            <Badge variant='secondary' className='font-medium'>
              {selectedCount} selected
            </Badge>

            {selectedCount < totalRows && (
              <Button variant='link' size='sm' onClick={onSelectAll} className='h-auto p-0 text-sm'>
                Select all {totalRows}
              </Button>
            )}
          </div>
        </div>

        {/* Bulk actions */}
        {availableOperations.length > 0 && (
          <div className='flex items-center gap-2 ml-auto'>
            {/* Primary actions */}
            {primaryOperations.map((operation) => {
              const Icon = operation.icon;
              return (
                <Button
                  key={operation.id}
                  variant='outline'
                  size='sm'
                  onClick={() => executeBulkOperation(operation)}
                  disabled={operation.loading}
                  className={actionButtonVariants({
                    variant: operation.variant || 'primary',
                    portal,
                  })}
                  title={operation.tooltip}
                >
                  {Icon && <Icon className='w-4 h-4' />}
                  {operation.loading ? operation.loadingText || 'Loading...' : operation.label}
                  {operation.shortcut && (
                    <kbd className='ml-1 px-1 py-0.5 text-xs bg-gray-200 rounded'>
                      {operation.shortcut}
                    </kbd>
                  )}
                </Button>
              );
            })}

            {/* Overflow menu */}
            {overflowOperations.length > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant='outline' size='sm'>
                    <MoreHorizontal className='w-4 h-4' />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align='end'>
                  {overflowOperations.map((operation) => {
                    const Icon = operation.icon;
                    return (
                      <DropdownMenuItem
                        key={operation.id}
                        onClick={() => executeBulkOperation(operation)}
                        disabled={operation.loading}
                        className='flex items-center gap-2'
                      >
                        {Icon && <Icon className='w-4 h-4' />}
                        {operation.loading
                          ? operation.loadingText || 'Loading...'
                          : operation.label}
                        {operation.shortcut && (
                          <kbd className='ml-auto px-1 py-0.5 text-xs bg-gray-200 rounded'>
                            {operation.shortcut}
                          </kbd>
                        )}
                      </DropdownMenuItem>
                    );
                  })}
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {/* Clear selection */}
            <Button
              variant='ghost'
              size='sm'
              onClick={onDeselectAll}
              className='text-gray-500 hover:text-gray-700'
              title='Clear selection'
            >
              <X className='w-4 h-4' />
            </Button>
          </div>
        )}
      </div>

      {/* Confirmation modal */}
      <ConfirmationModal
        isOpen={confirmationModal.isOpen}
        onClose={() => setConfirmationModal((prev) => ({ ...prev, isOpen: false }))}
        onConfirm={handleConfirmation}
        title={confirmationModal.title}
        message={confirmationModal.message}
        variant={confirmationModal.operation?.variant === 'danger' ? 'danger' : 'info'}
      />
    </>
  );
};

export default BulkActions;
