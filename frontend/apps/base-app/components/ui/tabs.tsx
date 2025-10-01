import * as React from 'react';

interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  className?: string;
}

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  value?: string;
}

export const Tabs = ({ children, ...props }: TabsProps) => (
  <div {...props}>{children}</div>
);

export const TabsList = ({ children, className = '', ...props }: TabsListProps) => (
  <div className={`inline-flex h-10 items-center justify-center rounded-md bg-slate-800 p-1 ${className}`} {...props}>
    {children}
  </div>
);

export const TabsTrigger = ({ children, className = '', ...props }: TabsTriggerProps) => (
  <button
    className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-slate-700 data-[state=active]:text-white ${className}`}
    {...props}
  >
    {children}
  </button>
);

export const TabsContent = ({ children, className = '', value, ...props }: TabsContentProps) => (
  <div className={`mt-2 ${className}`} data-value={value} {...props}>
    {children}
  </div>
);
