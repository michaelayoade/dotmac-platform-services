/**
 * Communications components exports
 */

export { TemplateManager } from './TemplateManager';
export { BulkEmailManager } from './BulkEmailManager';

// Export types that might be needed by parent components
export type {
  EmailTemplate,
  BulkEmailJob,
  RecipientData
} from './types';

// Main communications dashboard component (could be added later)
export { CommunicationsDashboard } from './CommunicationsDashboard';