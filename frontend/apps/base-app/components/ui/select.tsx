import * as React from 'react';

interface SelectProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  className?: string;
}

interface SelectValueProps extends React.HTMLAttributes<HTMLSpanElement> {
  placeholder?: string;
}

interface SelectContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface SelectItemProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface SelectGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface SelectLabelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const Select = ({ children, ...props }: SelectProps) => (
  <div {...props}>{children}</div>
);

export const SelectTrigger = ({ children, className = '', ...props }: SelectTriggerProps) => (
  <button
    className={`flex h-10 w-full items-center justify-between rounded-md border border-border bg-muted px-3 py-2 text-sm ${className}`}
    {...props}
  >
    {children}
  </button>
);

export const SelectValue = ({ placeholder, ...props }: SelectValueProps) => (
  <span {...props}>{placeholder}</span>
);

export const SelectContent = ({ children, ...props }: SelectContentProps) => (
  <div className="absolute z-50 min-w-[8rem] overflow-hidden rounded-md border border-border bg-muted" {...props}>
    {children}
  </div>
);

export const SelectItem = ({ children, ...props }: SelectItemProps) => (
  <div className="relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm hover:bg-muted" {...props}>
    {children}
  </div>
);

export const SelectGroup = ({ children, ...props }: SelectGroupProps) => (
  <div {...props}>{children}</div>
);

export const SelectLabel = ({ children, className = '', ...props }: SelectLabelProps) => (
  <div className={`py-1.5 pl-8 pr-2 text-sm font-semibold ${className}`} {...props}>
    {children}
  </div>
);
