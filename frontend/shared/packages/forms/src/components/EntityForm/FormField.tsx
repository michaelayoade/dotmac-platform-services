'use client';

import React, { useMemo } from 'react';
import { useFormContext, useController } from 'react-hook-form';
import { FormFieldConfig, FormMode, PortalVariant, PortalTheme } from '../../types';
import { cn } from '../../utils/cn';
import {
  Eye,
  EyeOff,
  Calendar,
  Upload,
  Phone,
  MapPin,
  AlertCircle,
  Check,
  ChevronDown,
} from 'lucide-react';

interface FormFieldProps {
  config: FormFieldConfig;
  mode: FormMode;
  portalVariant: PortalVariant;
  theme: PortalTheme;
  error?: string;
}

export function FormField({ config, mode, portalVariant, theme, error }: FormFieldProps) {
  const { control, watch, setValue } = useFormContext();

  const {
    field,
    fieldState: { error: fieldError },
  } = useController({
    name: config.name,
    control,
    disabled: config.disabled || mode === 'view',
  });

  const displayError = error || fieldError?.message;
  const isDisabled = config.disabled || mode === 'view';
  const isRequired = config.required && mode !== 'view';

  // Watch for field dependencies
  const watchedValues = watch();
  const shouldShow = useMemo(() => {
    if (!config.dependencies) return true;

    return config.dependencies.every((dep) => {
      const depValue = watchedValues[dep.field];
      const matches = dep.value === depValue;

      return dep.action === 'show' ? matches : !matches;
    });
  }, [config.dependencies, watchedValues]);

  if (!shouldShow) return null;

  // Field wrapper with label and error
  const FieldWrapper = ({ children }: { children: React.ReactNode }) => (
    <div className={cn('space-y-1', theme.spacing.fieldGap)}>
      {config.label && (
        <label
          htmlFor={config.name}
          className={cn(
            'block text-sm font-medium',
            theme.typography.fieldLabel,
            isRequired && "after:content-['*'] after:text-red-500 after:ml-1",
            isDisabled && 'text-gray-400'
          )}
        >
          {config.label}
        </label>
      )}

      {config.description && (
        <p className={cn('text-sm text-gray-600', theme.typography.helpText)}>
          {config.description}
        </p>
      )}

      {children}

      {displayError && (
        <div className='flex items-center gap-1 text-sm text-red-600'>
          <AlertCircle className='h-4 w-4 flex-shrink-0' />
          <span>{displayError}</span>
        </div>
      )}
    </div>
  );

  // Render field based on type
  const renderField = () => {
    switch (config.type) {
      case 'text':
      case 'email':
        return (
          <input
            {...field}
            id={config.name}
            type={config.type}
            placeholder={config.placeholder}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500',
              'disabled:bg-gray-50 disabled:text-gray-500',
              theme.components.input,
              displayError && 'border-red-300 focus:border-red-500 focus:ring-red-500'
            )}
            disabled={isDisabled}
            aria-describedby={displayError ? `${config.name}-error` : undefined}
          />
        );

      case 'password':
        return (
          <PasswordField
            field={field}
            config={config}
            theme={theme}
            isDisabled={isDisabled}
            error={displayError}
          />
        );

      case 'number':
        return (
          <input
            {...field}
            id={config.name}
            type='number'
            placeholder={config.placeholder}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500',
              'disabled:bg-gray-50 disabled:text-gray-500',
              theme.components.input,
              displayError && 'border-red-300 focus:border-red-500 focus:ring-red-500'
            )}
            disabled={isDisabled}
            onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : '')}
          />
        );

      case 'textarea':
        return (
          <textarea
            {...field}
            id={config.name}
            rows={4}
            placeholder={config.placeholder}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500',
              'disabled:bg-gray-50 disabled:text-gray-500',
              theme.components.input,
              displayError && 'border-red-300 focus:border-red-500 focus:ring-red-500'
            )}
            disabled={isDisabled}
          />
        );

      case 'select':
        return (
          <SelectField
            field={field}
            config={config}
            theme={theme}
            isDisabled={isDisabled}
            error={displayError}
          />
        );

      case 'multiselect':
        return (
          <MultiSelectField
            field={field}
            config={config}
            theme={theme}
            isDisabled={isDisabled}
            error={displayError}
          />
        );

      case 'checkbox':
        return (
          <CheckboxField field={field} config={config} theme={theme} isDisabled={isDisabled} />
        );

      case 'radio':
        return <RadioField field={field} config={config} theme={theme} isDisabled={isDisabled} />;

      case 'date':
        return (
          <DateField
            field={field}
            config={config}
            theme={theme}
            isDisabled={isDisabled}
            error={displayError}
          />
        );

      case 'phone':
        return (
          <PhoneField
            field={field}
            config={config}
            theme={theme}
            isDisabled={isDisabled}
            error={displayError}
          />
        );

      case 'address':
        return (
          <AddressField
            field={field}
            config={config}
            theme={theme}
            isDisabled={isDisabled}
            error={displayError}
            setValue={setValue}
          />
        );

      case 'file':
        return (
          <FileField
            field={field}
            config={config}
            theme={theme}
            isDisabled={isDisabled}
            error={displayError}
          />
        );

      default:
        return (
          <input
            {...field}
            id={config.name}
            type='text'
            placeholder={config.placeholder}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm',
              'focus:border-primary-500 focus:ring-primary-500',
              theme.components.input
            )}
            disabled={isDisabled}
          />
        );
    }
  };

  return <FieldWrapper>{renderField()}</FieldWrapper>;
}

// Specialized field components
function PasswordField({ field, config, theme, isDisabled, error }: any) {
  const [showPassword, setShowPassword] = React.useState(false);

  return (
    <div className='relative'>
      <input
        {...field}
        id={config.name}
        type={showPassword ? 'text' : 'password'}
        placeholder={config.placeholder}
        className={cn(
          'block w-full pr-10 rounded-md border-gray-300 shadow-sm',
          'focus:border-primary-500 focus:ring-primary-500',
          'disabled:bg-gray-50 disabled:text-gray-500',
          theme.components.input,
          error && 'border-red-300 focus:border-red-500 focus:ring-red-500'
        )}
        disabled={isDisabled}
      />
      <button
        type='button'
        className='absolute inset-y-0 right-0 pr-3 flex items-center'
        onClick={() => setShowPassword(!showPassword)}
      >
        {showPassword ? (
          <EyeOff className='h-4 w-4 text-gray-400' />
        ) : (
          <Eye className='h-4 w-4 text-gray-400' />
        )}
      </button>
    </div>
  );
}

function SelectField({ field, config, theme, isDisabled, error }: any) {
  return (
    <div className='relative'>
      <select
        {...field}
        id={config.name}
        className={cn(
          'block w-full rounded-md border-gray-300 shadow-sm',
          'focus:border-primary-500 focus:ring-primary-500',
          'disabled:bg-gray-50 disabled:text-gray-500',
          theme.components.input,
          error && 'border-red-300 focus:border-red-500 focus:ring-red-500'
        )}
        disabled={isDisabled}
      >
        {config.placeholder && <option value=''>{config.placeholder}</option>}
        {config.options?.map((option: any) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <ChevronDown className='absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none' />
    </div>
  );
}

function MultiSelectField({ field, config, theme, isDisabled, error }: any) {
  const selectedValues = field.value || [];

  const handleToggle = (value: string) => {
    const newValues = selectedValues.includes(value)
      ? selectedValues.filter((v: string) => v !== value)
      : [...selectedValues, value];
    field.onChange(newValues);
  };

  return (
    <div className='space-y-2'>
      {config.options?.map((option: any) => (
        <label key={option.value} className='flex items-center'>
          <input
            type='checkbox'
            checked={selectedValues.includes(option.value)}
            onChange={() => handleToggle(option.value)}
            disabled={isDisabled}
            className='h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
          />
          <span className='ml-2 text-sm text-gray-700'>{option.label}</span>
        </label>
      ))}
    </div>
  );
}

function CheckboxField({ field, config, theme, isDisabled }: any) {
  return (
    <div className='flex items-start'>
      <input
        {...field}
        id={config.name}
        type='checkbox'
        checked={field.value || false}
        className='h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
        disabled={isDisabled}
      />
      {config.label && (
        <label htmlFor={config.name} className='ml-2 block text-sm text-gray-700'>
          {config.label}
        </label>
      )}
    </div>
  );
}

function RadioField({ field, config, theme, isDisabled }: any) {
  return (
    <div className='space-y-2'>
      {config.options?.map((option: any) => (
        <label key={option.value} className='flex items-center'>
          <input
            type='radio'
            name={config.name}
            value={option.value}
            checked={field.value === option.value}
            onChange={() => field.onChange(option.value)}
            disabled={isDisabled}
            className='h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500'
          />
          <span className='ml-2 text-sm text-gray-700'>{option.label}</span>
        </label>
      ))}
    </div>
  );
}

function DateField({ field, config, theme, isDisabled, error }: any) {
  return (
    <div className='relative'>
      <input
        {...field}
        id={config.name}
        type='date'
        className={cn(
          'block w-full pr-10 rounded-md border-gray-300 shadow-sm',
          'focus:border-primary-500 focus:ring-primary-500',
          'disabled:bg-gray-50 disabled:text-gray-500',
          theme.components.input,
          error && 'border-red-300 focus:border-red-500 focus:ring-red-500'
        )}
        disabled={isDisabled}
      />
      <Calendar className='absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none' />
    </div>
  );
}

function PhoneField({ field, config, theme, isDisabled, error }: any) {
  return (
    <div className='relative'>
      <input
        {...field}
        id={config.name}
        type='tel'
        placeholder={config.placeholder || '+1 (555) 123-4567'}
        className={cn(
          'block w-full pr-10 rounded-md border-gray-300 shadow-sm',
          'focus:border-primary-500 focus:ring-primary-500',
          'disabled:bg-gray-50 disabled:text-gray-500',
          theme.components.input,
          error && 'border-red-300 focus:border-red-500 focus:ring-red-500'
        )}
        disabled={isDisabled}
      />
      <Phone className='absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none' />
    </div>
  );
}

function AddressField({ field, config, theme, isDisabled, error, setValue }: any) {
  const address = field.value || {};

  const updateAddress = (key: string, value: string) => {
    const newAddress = { ...address, [key]: value };
    field.onChange(newAddress);
  };

  return (
    <div className='space-y-3'>
      <input
        type='text'
        placeholder='Street address'
        value={address.street || ''}
        onChange={(e) => updateAddress('street', e.target.value)}
        className={cn(
          'block w-full rounded-md border-gray-300 shadow-sm',
          'focus:border-primary-500 focus:ring-primary-500',
          theme.components.input
        )}
        disabled={isDisabled}
      />

      <div className='grid grid-cols-2 gap-3'>
        <input
          type='text'
          placeholder='City'
          value={address.city || ''}
          onChange={(e) => updateAddress('city', e.target.value)}
          className={cn(
            'block w-full rounded-md border-gray-300 shadow-sm',
            'focus:border-primary-500 focus:ring-primary-500',
            theme.components.input
          )}
          disabled={isDisabled}
        />

        <input
          type='text'
          placeholder='State'
          value={address.state || ''}
          onChange={(e) => updateAddress('state', e.target.value)}
          className={cn(
            'block w-full rounded-md border-gray-300 shadow-sm',
            'focus:border-primary-500 focus:ring-primary-500',
            theme.components.input
          )}
          disabled={isDisabled}
        />
      </div>

      <div className='grid grid-cols-2 gap-3'>
        <input
          type='text'
          placeholder='ZIP code'
          value={address.zipCode || ''}
          onChange={(e) => updateAddress('zipCode', e.target.value)}
          className={cn(
            'block w-full rounded-md border-gray-300 shadow-sm',
            'focus:border-primary-500 focus:ring-primary-500',
            theme.components.input
          )}
          disabled={isDisabled}
        />

        <input
          type='text'
          placeholder='Country'
          value={address.country || 'US'}
          onChange={(e) => updateAddress('country', e.target.value)}
          className={cn(
            'block w-full rounded-md border-gray-300 shadow-sm',
            'focus:border-primary-500 focus:ring-primary-500',
            theme.components.input
          )}
          disabled={isDisabled}
        />
      </div>
    </div>
  );
}

function FileField({ field, config, theme, isDisabled, error }: any) {
  const [dragOver, setDragOver] = React.useState(false);

  const handleFileChange = (files: FileList | null) => {
    if (files && files.length > 0) {
      const fileArray = Array.from(files);
      field.onChange(fileArray);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileChange(e.dataTransfer.files);
  };

  return (
    <div
      className={cn(
        'border-2 border-dashed border-gray-300 rounded-lg p-6 text-center',
        'hover:border-gray-400 transition-colors',
        dragOver && 'border-primary-500 bg-primary-50',
        error && 'border-red-300'
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <Upload className='mx-auto h-8 w-8 text-gray-400' />
      <p className='mt-2 text-sm text-gray-600'>
        Drop files here or{' '}
        <label className='cursor-pointer text-primary-600 hover:text-primary-500'>
          browse
          <input
            type='file'
            className='sr-only'
            onChange={(e) => handleFileChange(e.target.files)}
            disabled={isDisabled}
            multiple
          />
        </label>
      </p>
    </div>
  );
}
