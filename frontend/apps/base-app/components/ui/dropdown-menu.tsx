import * as React from 'react';

interface DropdownMenuProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface DropdownMenuTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  asChild?: boolean;
}

interface DropdownMenuContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  align?: 'start' | 'center' | 'end';
}

interface DropdownMenuItemProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

interface DropdownMenuLabelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

interface DropdownMenuSeparatorProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

interface DropdownMenuGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface DropdownMenuCheckboxItemProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

export const DropdownMenu = ({ children, ...props }: DropdownMenuProps) => (
  <div {...props}>{children}</div>
);

export const DropdownMenuTrigger = ({ children, ...props }: DropdownMenuTriggerProps) => (
  <button {...props}>{children}</button>
);

export const DropdownMenuContent = ({ children, className = '', ...props }: DropdownMenuContentProps) => (
  <div className={`z-50 min-w-[8rem] overflow-hidden rounded-md border border-border bg-white dark:border-border dark:bg-muted p-1 shadow-md ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuItem = ({ children, className = '', ...props }: DropdownMenuItemProps) => (
  <div className={`relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm text-foreground dark:text-white hover:bg-accent dark:hover:bg-muted ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuCheckboxItem = ({ children, className = '', checked, onCheckedChange, ...props }: DropdownMenuCheckboxItemProps) => (
  <div
    className={`relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm text-foreground dark:text-white hover:bg-accent dark:hover:bg-muted ${className}`}
    onClick={() => onCheckedChange?.(!checked)}
    {...props}
  >
    <span className="mr-2">{checked ? '✓' : ''}</span>
    {children}
  </div>
);

export const DropdownMenuLabel = ({ children, className = '', ...props }: DropdownMenuLabelProps) => (
  <div className={`px-2 py-1.5 text-sm font-semibold text-foreground dark:text-white ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuSeparator = ({ className = '', ...props }: DropdownMenuSeparatorProps) => (
  <div className={`-mx-1 my-1 h-px bg-muted ${className}`} {...props} />
);

export const DropdownMenuGroup = ({ children, ...props }: DropdownMenuGroupProps) => (
  <div {...props}>{children}</div>
);
