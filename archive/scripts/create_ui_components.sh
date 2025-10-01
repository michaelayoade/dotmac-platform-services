#!/bin/bash

cd /Users/michaelayoade/Downloads/Projects/dotmac-platform-services/frontend/apps/base-app/components/ui

# Create textarea.tsx
cat > textarea.tsx << 'EOF'
import * as React from 'react';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', ...props }, ref) => {
    return (
      <textarea
        className={`flex min-h-[80px] w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
        ref={ref}
        {...props}
      />
    );
  }
);
Textarea.displayName = 'Textarea';

export { Textarea };
EOF

# Create switch.tsx
cat > switch.tsx << 'EOF'
import * as React from 'react';

export interface SwitchProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ className = '', checked = false, onCheckedChange, ...props }, ref) => {
    return (
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onCheckedChange?.(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-sky-500' : 'bg-slate-700'
        } ${className}`}
        ref={ref}
        {...props}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    );
  }
);
Switch.displayName = 'Switch';

export { Switch };
EOF

# Create checkbox.tsx
cat > checkbox.tsx << 'EOF'
import * as React from 'react';

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className = '', ...props }, ref) => {
    return (
      <input
        type="checkbox"
        className={`h-4 w-4 rounded border-slate-700 text-sky-500 focus:ring-sky-500 ${className}`}
        ref={ref}
        {...props}
      />
    );
  }
);
Checkbox.displayName = 'Checkbox';

export { Checkbox };
EOF

# Create scroll-area.tsx
cat > scroll-area.tsx << 'EOF'
import * as React from 'react';

const ScrollArea = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', children, ...props }, ref) => (
    <div ref={ref} className={`relative overflow-auto ${className}`} {...props}>
      {children}
    </div>
  )
);
ScrollArea.displayName = 'ScrollArea';

const ScrollBar = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={`${className}`} {...props} />
  )
);
ScrollBar.displayName = 'ScrollBar';

export { ScrollArea, ScrollBar };
EOF

# Create separator.tsx
cat > separator.tsx << 'EOF'
import * as React from 'react';

const Separator = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', orientation = 'horizontal', ...props }: any, ref) => (
    <div
      ref={ref}
      className={`shrink-0 bg-slate-700 ${
        orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]'
      } ${className}`}
      {...props}
    />
  )
);
Separator.displayName = 'Separator';

export { Separator };
EOF

# Create progress.tsx
cat > progress.tsx << 'EOF'
import * as React from 'react';

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className = '', value = 0, ...props }, ref) => (
    <div
      ref={ref}
      className={`relative h-2 w-full overflow-hidden rounded-full bg-slate-800 ${className}`}
      {...props}
    >
      <div
        className="h-full bg-sky-500 transition-all"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
);
Progress.displayName = 'Progress';

export { Progress };
EOF

# Create avatar.tsx
cat > avatar.tsx << 'EOF'
import * as React from 'react';

const Avatar = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full ${className}`}
      {...props}
    />
  )
);
Avatar.displayName = 'Avatar';

const AvatarImage = React.forwardRef<HTMLImageElement, React.ImgHTMLAttributes<HTMLImageElement>>(
  ({ className = '', ...props }, ref) => (
    <img ref={ref} className={`aspect-square h-full w-full ${className}`} {...props} />
  )
);
AvatarImage.displayName = 'AvatarImage';

const AvatarFallback = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`flex h-full w-full items-center justify-center rounded-full bg-slate-700 ${className}`}
      {...props}
    />
  )
);
AvatarFallback.displayName = 'AvatarFallback';

export { Avatar, AvatarImage, AvatarFallback };
EOF

# Create dropdown-menu.tsx
cat > dropdown-menu.tsx << 'EOF'
export const DropdownMenu = ({ children, ...props }: any) => (
  <div {...props}>{children}</div>
);

export const DropdownMenuTrigger = ({ children, ...props }: any) => (
  <button {...props}>{children}</button>
);

export const DropdownMenuContent = ({ children, className = '', ...props }: any) => (
  <div className={`z-50 min-w-[8rem] overflow-hidden rounded-md border border-slate-700 bg-slate-800 p-1 shadow-md ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuItem = ({ children, className = '', ...props }: any) => (
  <div className={`relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm hover:bg-slate-700 ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuLabel = ({ children, className = '', ...props }: any) => (
  <div className={`px-2 py-1.5 text-sm font-semibold ${className}`} {...props}>
    {children}
  </div>
);

export const DropdownMenuSeparator = ({ className = '', ...props }: any) => (
  <div className={`-mx-1 my-1 h-px bg-slate-700 ${className}`} {...props} />
);

export const DropdownMenuGroup = ({ children, ...props }: any) => (
  <div {...props}>{children}</div>
);
EOF

# Create radio-group.tsx
cat > radio-group.tsx << 'EOF'
import * as React from 'react';

export const RadioGroup = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={`grid gap-2 ${className}`} {...props} />
  )
);
RadioGroup.displayName = 'RadioGroup';

export const RadioGroupItem = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className = '', ...props }, ref) => (
    <input
      type="radio"
      ref={ref}
      className={`h-4 w-4 rounded-full border border-slate-700 text-sky-500 focus:ring-sky-500 ${className}`}
      {...props}
    />
  )
);
RadioGroupItem.displayName = 'RadioGroupItem';
EOF

# Create use-toast.tsx
cat > use-toast.tsx << 'EOF'
import { useState, useCallback } from 'react';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback(({ title, description, variant = 'default' }: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast = { id, title, description, variant };
    setToasts((prev) => [...prev, newToast]);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  return { toast, toasts };
}
EOF

echo "✅ All UI components created successfully!"
ls -la *.tsx | wc -l
echo "total component files created"