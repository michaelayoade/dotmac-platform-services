import type { MetricDefinition, AnalyticsDashboard, FilterConfig } from '../types';

export const validateMetricDefinition = (metric: MetricDefinition): string[] => {
  const errors: string[] = [];

  if (!metric.id || typeof metric.id !== 'string') {
    errors.push('Metric ID is required and must be a string');
  }

  if (!metric.name || typeof metric.name !== 'string') {
    errors.push('Metric name is required and must be a string');
  }

  if (!metric.unit || typeof metric.unit !== 'string') {
    errors.push('Metric unit is required and must be a string');
  }

  const validTypes = ['counter', 'gauge', 'histogram', 'summary'];
  if (!validTypes.includes(metric.type)) {
    errors.push(`Metric type must be one of: ${validTypes.join(', ')}`);
  }

  const validCategories = ['business', 'technical', 'operational', 'financial'];
  if (!validCategories.includes(metric.category)) {
    errors.push(`Metric category must be one of: ${validCategories.join(', ')}`);
  }

  if (metric.aggregation) {
    const validMethods = ['sum', 'avg', 'min', 'max', 'count', 'distinct'];
    if (!validMethods.includes(metric.aggregation.method)) {
      errors.push(`Aggregation method must be one of: ${validMethods.join(', ')}`);
    }

    const validIntervals = ['minute', 'hour', 'day', 'week', 'month', 'year'];
    if (!validIntervals.includes(metric.aggregation.interval)) {
      errors.push(`Aggregation interval must be one of: ${validIntervals.join(', ')}`);
    }
  }

  return errors;
};

export const validateDashboardConfig = (dashboard: AnalyticsDashboard): string[] => {
  const errors: string[] = [];

  if (!dashboard.id || typeof dashboard.id !== 'string') {
    errors.push('Dashboard ID is required and must be a string');
  }

  if (!dashboard.name || typeof dashboard.name !== 'string') {
    errors.push('Dashboard name is required and must be a string');
  }

  const validCategories = ['executive', 'operational', 'financial', 'marketing', 'technical'];
  if (!validCategories.includes(dashboard.category)) {
    errors.push(`Dashboard category must be one of: ${validCategories.join(', ')}`);
  }

  const validLayouts = ['grid', 'free', 'tabs'];
  if (!validLayouts.includes(dashboard.layout)) {
    errors.push(`Dashboard layout must be one of: ${validLayouts.join(', ')}`);
  }

  const validThemes = ['light', 'dark', 'auto'];
  if (!validThemes.includes(dashboard.theme)) {
    errors.push(`Dashboard theme must be one of: ${validThemes.join(', ')}`);
  }

  if (!Array.isArray(dashboard.widgets)) {
    errors.push('Dashboard widgets must be an array');
  } else {
    dashboard.widgets.forEach((widget, index) => {
      const widgetErrors = validateWidget(widget);
      widgetErrors.forEach((error) => {
        errors.push(`Widget ${index}: ${error}`);
      });
    });
  }

  if (!dashboard.owner || typeof dashboard.owner !== 'string') {
    errors.push('Dashboard owner is required and must be a string');
  }

  if (!Array.isArray(dashboard.sharedWith)) {
    errors.push('Dashboard sharedWith must be an array');
  }

  if (dashboard.settings) {
    if (typeof dashboard.settings.autoRefresh !== 'boolean') {
      errors.push('Dashboard settings autoRefresh must be a boolean');
    }

    if (
      typeof dashboard.settings.refreshInterval !== 'number' ||
      dashboard.settings.refreshInterval < 0
    ) {
      errors.push('Dashboard settings refreshInterval must be a positive number');
    }

    if (!dashboard.settings.timezone || typeof dashboard.settings.timezone !== 'string') {
      errors.push('Dashboard settings timezone is required and must be a string');
    }

    if (!dashboard.settings.currency || typeof dashboard.settings.currency !== 'string') {
      errors.push('Dashboard settings currency is required and must be a string');
    }
  }

  return errors;
};

const validateWidget = (widget: any): string[] => {
  const errors: string[] = [];

  if (!widget.id || typeof widget.id !== 'string') {
    errors.push('Widget ID is required and must be a string');
  }

  const validTypes = ['metric', 'chart', 'table', 'kpi', 'funnel', 'heatmap'];
  if (!validTypes.includes(widget.type)) {
    errors.push(`Widget type must be one of: ${validTypes.join(', ')}`);
  }

  if (!widget.title || typeof widget.title !== 'string') {
    errors.push('Widget title is required and must be a string');
  }

  if (!widget.position || typeof widget.position !== 'object') {
    errors.push('Widget position is required and must be an object');
  } else {
    const { x, y, width, height } = widget.position;
    if (typeof x !== 'number' || x < 0) {
      errors.push('Widget position x must be a non-negative number');
    }
    if (typeof y !== 'number' || y < 0) {
      errors.push('Widget position y must be a non-negative number');
    }
    if (typeof width !== 'number' || width <= 0) {
      errors.push('Widget position width must be a positive number');
    }
    if (typeof height !== 'number' || height <= 0) {
      errors.push('Widget position height must be a positive number');
    }
  }

  if (!widget.config || typeof widget.config !== 'object') {
    errors.push('Widget config is required and must be an object');
  }

  if (!widget.dataSource || typeof widget.dataSource !== 'object') {
    errors.push('Widget dataSource is required and must be an object');
  } else {
    const validDataSourceTypes = ['api', 'database', 'realtime', 'csv', 'external'];
    if (!validDataSourceTypes.includes(widget.dataSource.type)) {
      errors.push(`Widget dataSource type must be one of: ${validDataSourceTypes.join(', ')}`);
    }
  }

  if (typeof widget.isVisible !== 'boolean') {
    errors.push('Widget isVisible must be a boolean');
  }

  return errors;
};

export const validateFilterConfig = (filter: FilterConfig): string[] => {
  const errors: string[] = [];

  if (!filter.id || typeof filter.id !== 'string') {
    errors.push('Filter ID is required and must be a string');
  }

  if (!filter.name || typeof filter.name !== 'string') {
    errors.push('Filter name is required and must be a string');
  }

  const validTypes = ['date_range', 'select', 'multiselect', 'text', 'number_range'];
  if (!validTypes.includes(filter.type)) {
    errors.push(`Filter type must be one of: ${validTypes.join(', ')}`);
  }

  if (!filter.field || typeof filter.field !== 'string') {
    errors.push('Filter field is required and must be a string');
  }

  if (filter.type === 'select' || filter.type === 'multiselect') {
    if (!Array.isArray(filter.options)) {
      errors.push('Filter options must be an array for select and multiselect types');
    } else {
      filter.options.forEach((option, index) => {
        if (!option.label || typeof option.label !== 'string') {
          errors.push(`Filter option ${index} label is required and must be a string`);
        }
        if (option.value === undefined || option.value === null) {
          errors.push(`Filter option ${index} value is required`);
        }
      });
    }
  }

  return errors;
};

export const validateEmailAddress = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validateUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const validateDateRange = (start: Date, end: Date): string[] => {
  const errors: string[] = [];

  if (!(start instanceof Date) || isNaN(start.getTime())) {
    errors.push('Start date must be a valid Date object');
  }

  if (!(end instanceof Date) || isNaN(end.getTime())) {
    errors.push('End date must be a valid Date object');
  }

  if (
    start instanceof Date &&
    end instanceof Date &&
    !isNaN(start.getTime()) &&
    !isNaN(end.getTime())
  ) {
    if (start >= end) {
      errors.push('Start date must be before end date');
    }

    const maxRange = 365 * 24 * 60 * 60 * 1000; // 1 year in milliseconds
    if (end.getTime() - start.getTime() > maxRange) {
      errors.push('Date range cannot exceed 1 year');
    }
  }

  return errors;
};

export const validateNumericRange = (min: number, max: number): string[] => {
  const errors: string[] = [];

  if (typeof min !== 'number' || isNaN(min)) {
    errors.push('Minimum value must be a valid number');
  }

  if (typeof max !== 'number' || isNaN(max)) {
    errors.push('Maximum value must be a valid number');
  }

  if (typeof min === 'number' && typeof max === 'number' && !isNaN(min) && !isNaN(max)) {
    if (min >= max) {
      errors.push('Minimum value must be less than maximum value');
    }
  }

  return errors;
};
