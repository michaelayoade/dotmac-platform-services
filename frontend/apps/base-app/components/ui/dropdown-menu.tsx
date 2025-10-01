import * as React from 'react';

interface DropdownMenuProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface DropdownMenuTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

interface DropdownMenuContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
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

export const DropdownMenu = ({ children, ...props }: DropdownMenuProps) => (
  <div {...props}>{children}</div>
);

export const DropdownMenuTrigger = ({ children, ...props }: DropdownMenuTriggerProps) => (
  <button {...props}>{children}</button>
);

export const DropdownMenuContent = ({ children, className = '', ...props }: DropdownMenuContentProps) => (
  <div className={`z-50 min-w-[8rem] overflow-hidden rounded-md border border-slate-700 bg-slate-800 p-1 shadow-md ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuItem = ({ children, className = '', ...props }: DropdownMenuItemProps) => (
  <div className={`relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm hover:bg-slate-700 ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuLabel = ({ children, className = '', ...props }: DropdownMenuLabelProps) => (
  <div className={`px-2 py-1.5 text-sm font-semibold ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuSeparator = ({ className = '', ...props }: DropdownMenuSeparatorProps) => (
  <div className={`-mx-1 my-1 h-px bg-slate-700 ${className}`} {...props} />
);

export const DropdownMenuGroup = ({ children, ...props }: DropdownMenuGroupProps) => (
  <div {...props}>{children}</div>
);
