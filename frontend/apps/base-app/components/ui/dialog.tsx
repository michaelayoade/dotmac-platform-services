'use client';

import * as React from 'react';

interface DialogProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface DialogTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

interface DialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

interface DialogHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

interface DialogTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
  className?: string;
}

interface DialogDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
  className?: string;
}

interface DialogFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

const DialogContext = React.createContext<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
}>({
  open: false,
  onOpenChange: () => {},
});

export const Dialog = ({ children, open = false, onOpenChange = () => {}, ...props }: DialogProps) => (
  <DialogContext.Provider value={{ open, onOpenChange }}>
    <div {...props}>{children}</div>
  </DialogContext.Provider>
);

export const DialogTrigger = ({ children, ...props }: DialogTriggerProps) => (
  <button {...props}>{children}</button>
);

export const DialogContent = ({ children, className = '', ...props }: DialogContentProps) => {
  const { open, onOpenChange } = React.useContext(DialogContext);

  if (!open) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 ${className}`}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onOpenChange(false);
        }
      }}
      {...props}
    >
      <div
        className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg shadow-primary/10"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
};

export const DialogHeader = ({ children, className = '', ...props }: DialogHeaderProps) => (
  <div className={`mb-4 ${className}`} {...props}>
    {children}
  </div>
);

export const DialogTitle = ({ children, className = '', ...props }: DialogTitleProps) => (
  <h2 className={`text-lg font-semibold text-foreground ${className}`} {...props}>
    {children}
  </h2>
);

export const DialogDescription = ({ children, className = '', ...props }: DialogDescriptionProps) => (
  <p className={`text-sm text-muted-foreground ${className}`} {...props}>
    {children}
  </p>
);

export const DialogFooter = ({ children, className = '', ...props }: DialogFooterProps) => (
  <div className={`mt-4 flex justify-end gap-2 ${className}`} {...props}>
    {children}
  </div>
);
