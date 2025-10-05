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
      className={`h-4 w-4 rounded-full border border-border text-sky-500 focus:ring-sky-500 ${className}`}
      {...props}
    />
  )
);
RadioGroupItem.displayName = 'RadioGroupItem';
