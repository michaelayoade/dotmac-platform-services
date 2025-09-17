'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { PortalTheme } from '../../types';
import { cn } from '../../utils/cn';

interface FormSectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  collapsible?: boolean;
  defaultExpanded?: boolean;
  theme: PortalTheme;
  className?: string;
}

export function FormSection({
  title,
  description,
  children,
  collapsible = false,
  defaultExpanded = true,
  theme,
  className,
}: FormSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const toggleExpanded = () => {
    if (collapsible) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Section Header */}
      <div
        className={cn(
          'flex items-start justify-between',
          collapsible && 'cursor-pointer hover:opacity-80 transition-opacity'
        )}
        onClick={toggleExpanded}
      >
        <div className='flex-1'>
          <div className='flex items-center gap-2'>
            {collapsible && (
              <button
                type='button'
                className='p-0.5 rounded hover:bg-gray-100 transition-colors'
                aria-expanded={isExpanded}
                aria-label={isExpanded ? 'Collapse section' : 'Expand section'}
              >
                {isExpanded ? (
                  <ChevronDown className='h-4 w-4 text-gray-500' />
                ) : (
                  <ChevronRight className='h-4 w-4 text-gray-500' />
                )}
              </button>
            )}

            <h3 className={cn('text-lg font-medium', theme.typography.sectionTitle)}>{title}</h3>
          </div>

          {description && (
            <p className={cn('mt-1 text-sm', theme.typography.helpText)}>{description}</p>
          )}
        </div>
      </div>

      {/* Section Content */}
      {(!collapsible || isExpanded) && (
        <div
          className={cn(
            'space-y-4',
            theme.spacing.fieldGap,
            collapsible && 'animate-in slide-in-from-top-2 duration-200'
          )}
        >
          {children}
        </div>
      )}

      {/* Section Divider */}
      <div className='border-b border-gray-200' />
    </div>
  );
}
