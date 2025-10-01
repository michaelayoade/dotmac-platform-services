import * as React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline';
}

function Badge({ className = '', variant = 'default', ...props }: BadgeProps) {
  const variants = {
    default: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    secondary: 'bg-slate-700/10 text-slate-400 border-slate-700/20',
    destructive: 'bg-red-500/10 text-red-400 border-red-500/20',
    outline: 'text-slate-400 border-slate-700',
  };

  return (
    <div
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border ${variants[variant]} ${className}`}
      {...props}
    />
  );
}

export { Badge };