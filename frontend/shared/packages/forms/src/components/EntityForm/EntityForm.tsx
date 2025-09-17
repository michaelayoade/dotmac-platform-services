'use client';

import React, { useMemo, useCallback } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { getEntitySchema, validateEntity } from '../../schemas';
import {
  EntityFormConfig,
  PortalVariant,
  EntityType,
  FormMode,
  ValidationContext,
} from '../../types';
import { FormSection } from './FormSection';
import { FormActions } from './FormActions';
import { FormField } from './FormField';
import { usePortalTheme } from '../../hooks/usePortalTheme';
import { generateEntityFormConfig } from '../../configs/entityConfigs';
import { cn } from '../../utils/cn';

interface EntityFormProps<TData = any> {
  entity: EntityType;
  mode: FormMode;
  portalVariant: PortalVariant;
  initialData?: TData;
  onSubmit: (data: TData) => Promise<void>;
  onCancel?: () => void;
  config?: Partial<EntityFormConfig>;
  validationContext?: ValidationContext;
  className?: string;
  isLoading?: boolean;
  errors?: Record<string, string>;
}

export function EntityForm<TData = any>({
  entity,
  mode,
  portalVariant,
  initialData,
  onSubmit,
  onCancel,
  config: customConfig,
  validationContext,
  className,
  isLoading = false,
  errors: externalErrors,
}: EntityFormProps<TData>) {
  // Get portal-specific theme
  const theme = usePortalTheme(portalVariant);

  // Generate form configuration
  const formConfig = useMemo(() => {
    const baseConfig = generateEntityFormConfig(entity, mode, portalVariant);

    // Merge with custom config and portal customizations
    const portalCustomizations = baseConfig.portalCustomizations?.[portalVariant] || {};

    return {
      ...baseConfig,
      ...portalCustomizations,
      ...customConfig,
      // Merge fields arrays properly
      fields: customConfig?.fields || baseConfig.fields,
      sections: customConfig?.sections || baseConfig.sections,
    };
  }, [entity, mode, portalVariant, customConfig]);

  // Get validation schema
  const validationSchema = useMemo(() => {
    return getEntitySchema(entity, portalVariant, validationContext);
  }, [entity, portalVariant, validationContext]);

  // Initialize form
  const methods = useForm({
    resolver: zodResolver(validationSchema),
    defaultValues: initialData || {},
    mode: 'onChange',
    reValidateMode: 'onChange',
  });

  const {
    handleSubmit,
    formState: { errors, isSubmitting, isDirty, isValid },
  } = methods;

  // Handle form submission
  const onFormSubmit = useCallback(
    async (data: any) => {
      try {
        // Validate data before submission
        const validation = validateEntity(data, entity, portalVariant, validationContext);

        if (!validation.success) {
          console.error('Form validation failed:', validation.error);
          return;
        }

        await onSubmit(validation.data as TData);
      } catch (error) {
        console.error('Form submission error:', error);
      }
    },
    [entity, portalVariant, validationContext, onSubmit]
  );

  // Filter fields based on portal variant and permissions
  const visibleFields = useMemo(() => {
    return formConfig.fields.filter((field) => {
      // Check portal variant restrictions
      if (field.portalVariants && !field.portalVariants.includes(portalVariant)) {
        return false;
      }

      // Check permission restrictions
      if (field.permissions && validationContext?.userPermissions) {
        const hasPermission = field.permissions.some((permission) =>
          validationContext.userPermissions.includes(permission)
        );
        if (!hasPermission) return false;
      }

      // Check mode restrictions
      if (mode === 'view' && field.hidden) {
        return false;
      }

      return true;
    });
  }, [formConfig.fields, portalVariant, validationContext, mode]);

  // Render form sections or fields directly
  const renderFormContent = () => {
    if (formConfig.sections && formConfig.sections.length > 0) {
      return formConfig.sections.map((section) => (
        <FormSection
          key={section.title}
          title={section.title}
          description={section.description}
          collapsible={section.collapsible}
          defaultExpanded={section.defaultExpanded}
          theme={theme}
        >
          {section.fields.map((fieldName) => {
            const fieldConfig = visibleFields.find((f) => f.name === fieldName);
            if (!fieldConfig) return null;

            return (
              <FormField
                key={fieldName}
                config={fieldConfig}
                mode={mode}
                portalVariant={portalVariant}
                theme={theme}
                error={errors[fieldName]?.message || externalErrors?.[fieldName]}
              />
            );
          })}
        </FormSection>
      ));
    }

    // Render fields directly without sections
    return visibleFields.map((fieldConfig) => (
      <FormField
        key={fieldConfig.name}
        config={fieldConfig}
        mode={mode}
        portalVariant={portalVariant}
        theme={theme}
        error={errors[fieldConfig.name]?.message || externalErrors?.[fieldConfig.name]}
      />
    ));
  };

  const formTitle =
    formConfig.title ||
    `${mode === 'create' ? 'Create' : mode === 'edit' ? 'Edit' : 'View'} ${entity}`;

  return (
    <FormProvider {...methods}>
      <form
        onSubmit={handleSubmit(onFormSubmit)}
        className={cn(
          'space-y-6',
          theme.components.card,
          formConfig.layout === 'two-column' && 'lg:grid lg:grid-cols-2 lg:gap-6 lg:space-y-0',
          className
        )}
        noValidate
      >
        {/* Form Header */}
        <div className='space-y-1'>
          <h2 className={cn('text-2xl font-semibold', theme.typography.formTitle)}>{formTitle}</h2>
          {formConfig.subtitle && (
            <p className={cn('text-sm text-gray-600', theme.typography.helpText)}>
              {formConfig.subtitle}
            </p>
          )}
        </div>

        {/* Form Content */}
        <div
          className={cn(
            'space-y-6',
            formConfig.layout === 'two-column' &&
              'lg:col-span-2 lg:grid lg:grid-cols-2 lg:gap-6 lg:space-y-0'
          )}
        >
          {renderFormContent()}
        </div>

        {/* Form Actions */}
        {mode !== 'view' && (
          <FormActions
            config={formConfig.actions}
            mode={mode}
            portalVariant={portalVariant}
            theme={theme}
            onCancel={onCancel}
            isLoading={isLoading || isSubmitting}
            isValid={isValid}
            isDirty={isDirty}
          />
        )}

        {/* Debug info in development */}
        {process.env.NODE_ENV === 'development' && (
          <details className='mt-8 p-4 bg-gray-100 rounded'>
            <summary className='cursor-pointer font-medium'>Debug Info</summary>
            <pre className='mt-2 text-xs overflow-auto'>
              {JSON.stringify(
                {
                  entity,
                  mode,
                  portalVariant,
                  errors: Object.keys(errors),
                  isDirty,
                  isValid,
                  isSubmitting,
                },
                null,
                2
              )}
            </pre>
          </details>
        )}
      </form>
    </FormProvider>
  );
}

// Export typed versions for common entities
export const CustomerForm = <TData = any,>(props: Omit<EntityFormProps<TData>, 'entity'>) => (
  <EntityForm {...props} entity='customer' />
);

export const TenantForm = <TData = any,>(props: Omit<EntityFormProps<TData>, 'entity'>) => (
  <EntityForm {...props} entity='tenant' />
);

export const UserForm = <TData = any,>(props: Omit<EntityFormProps<TData>, 'entity'>) => (
  <EntityForm {...props} entity='user' />
);

export const DeviceForm = <TData = any,>(props: Omit<EntityFormProps<TData>, 'entity'>) => (
  <EntityForm {...props} entity='device' />
);

export const ServiceForm = <TData = any,>(props: Omit<EntityFormProps<TData>, 'entity'>) => (
  <EntityForm {...props} entity='service' />
);
