/**
 * Contacts API
 *
 * Contact CRM management, methods, activities, and bulk operations
 */

import { api, ApiClientError, normalizePaginatedResponse } from "./client";

// ============================================================================
// Contact Types
// ============================================================================

export type ContactStatus = "active" | "inactive" | "archived" | "blocked" | "pending";
export type ContactStage =
  | "prospect"
  | "lead"
  | "opportunity"
  | "account"
  | "partner"
  | "vendor"
  | "other";
export type ContactMethodType =
  | "email"
  | "phone"
  | "mobile"
  | "fax"
  | "website"
  | "social_linkedin"
  | "social_twitter"
  | "social_facebook"
  | "social_instagram"
  | "address"
  | "other";

export interface ContactMethodInput {
  type: ContactMethodType;
  value: string;
  label?: string;
  isPrimary?: boolean;
  isVerified?: boolean;
  isPublic?: boolean;
  displayOrder?: number;
  metadata?: Record<string, unknown>;
  addressLine1?: string;
  addressLine2?: string;
  city?: string;
  stateProvince?: string;
  postalCode?: string;
  country?: string;
}

export interface ContactMethod extends ContactMethodInput {
  id: string;
  contactId: string;
  verifiedAt?: string | null;
  verifiedBy?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ContactLabelDefinition {
  id: string;
  name: string;
  slug?: string | null;
  description?: string | null;
  color?: string | null;
  icon?: string | null;
  category?: string | null;
  displayOrder?: number;
  isVisible?: boolean;
  isSystem?: boolean;
  isDefault?: boolean;
  metadata?: Record<string, unknown> | null;
  tenantId?: string;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string | null;
}

export interface Contact {
  id: string;
  tenantId: string;
  firstName?: string | null;
  middleName?: string | null;
  lastName?: string | null;
  displayName?: string | null;
  prefix?: string | null;
  suffix?: string | null;
  company?: string | null;
  jobTitle?: string | null;
  department?: string | null;
  status?: ContactStatus | null;
  stage?: ContactStage | null;
  ownerId?: string | null;
  assignedTeamId?: string | null;
  notes?: string | null;
  tags?: string[] | null;
  customFields?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
  birthday?: string | null;
  anniversary?: string | null;
  isPrimary?: boolean;
  isDecisionMaker?: boolean;
  isBillingContact?: boolean;
  isTechnicalContact?: boolean;
  preferredContactMethod?: ContactMethodType | null;
  preferredLanguage?: string | null;
  timezone?: string | null;
  isVerified?: boolean;
  createdAt: string;
  updatedAt: string;
  lastContactedAt?: string | null;
  deletedAt?: string | null;
  contactMethods?: ContactMethod[] | null;
  labels?: ContactLabelDefinition[] | null;
  // Convenience properties for UI display
  type?: ContactStage | null; // Alias for stage
  title?: string | null; // Alias for jobTitle
  email?: string | null; // Primary email from contactMethods
  phone?: string | null; // Primary phone from contactMethods
}

// ============================================================================
// Contact CRUD
// ============================================================================

export interface GetContactsParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: ContactStatus;
  stage?: ContactStage;
  type?: ContactStage; // Alias for stage
  ownerId?: string;
  tags?: string[];
  labelIds?: string[];
  includeDeleted?: boolean;
}

export async function getContacts(params: GetContactsParams = {}): Promise<{
  contacts: Contact[];
  totalCount: number;
  pageCount: number;
  hasNext: boolean;
  hasPrev: boolean;
}> {
  const {
    page = 1,
    pageSize = 50,
    search,
    status,
    stage,
    ownerId,
    tags,
    labelIds,
    includeDeleted,
  } = params;

  const response = await api.post<unknown>("/api/v1/contacts/search", {
    query: search,
    status,
    stage,
    ownerId,
    tags,
    labelIds,
    page,
    pageSize,
    includeDeleted,
  });
  const normalized = normalizePaginatedResponse<Contact>(response);

  return {
    contacts: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
    hasNext: normalized.hasNext ?? normalized.page < normalized.totalPages,
    hasPrev: normalized.hasPrev ?? normalized.page > 1,
  };
}

export async function getContact(id: string): Promise<Contact> {
  return api.get<Contact>(`/api/v1/contacts/${id}`);
}

export async function getContactMethods(contactId: string): Promise<ContactMethod[]> {
  const contact = await getContact(contactId);
  return contact.contactMethods ?? [];
}

export interface CreateContactData {
  firstName?: string;
  middleName?: string;
  lastName?: string;
  displayName?: string;
  prefix?: string;
  suffix?: string;
  company?: string;
  jobTitle?: string;
  department?: string;
  status?: ContactStatus;
  stage?: ContactStage;
  ownerId?: string;
  assignedTeamId?: string;
  notes?: string;
  tags?: string[];
  customFields?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  birthday?: string;
  anniversary?: string;
  isPrimary?: boolean;
  isDecisionMaker?: boolean;
  isBillingContact?: boolean;
  isTechnicalContact?: boolean;
  preferredContactMethod?: ContactMethodType;
  preferredLanguage?: string;
  timezone?: string;
  contactMethods?: ContactMethodInput[];
  labelIds?: string[];
  email?: string;
  phone?: string;
}

function buildContactMethods(data: CreateContactData): ContactMethodInput[] | undefined {
  const methods = [...(data.contactMethods ?? [])];

  if (data.email && !methods.some((method) => method.type === "email")) {
    methods.push({ type: "email", value: data.email, isPrimary: true });
  }
  if (data.phone && !methods.some((method) => method.type === "phone")) {
    methods.push({ type: "phone", value: data.phone, isPrimary: true });
  }

  return methods.length ? methods : undefined;
}

export async function createContact(data: CreateContactData): Promise<Contact> {
  return api.post<Contact>("/api/v1/contacts", {
    ...data,
    contactMethods: buildContactMethods(data),
  });
}

export async function updateContact(
  id: string,
  data: Partial<CreateContactData>
): Promise<Contact> {
  return api.patch<Contact>(`/api/v1/contacts/${id}`, data);
}

export async function deleteContact(id: string, hardDelete?: boolean): Promise<void> {
  return api.delete(`/api/v1/contacts/${id}`, {
    params: { hardDelete },
  });
}

// ============================================================================
// Contact Search
// ============================================================================

export interface ContactSearchQuery {
  query?: string;
  status?: ContactStatus;
  stage?: ContactStage;
  ownerId?: string;
  tags?: string[];
  labelIds?: string[];
  page?: number;
  pageSize?: number;
  includeDeleted?: boolean;
}

export async function searchContacts(query: ContactSearchQuery): Promise<{
  contacts: Contact[];
  totalCount: number;
  pageCount: number;
  hasNext: boolean;
  hasPrev: boolean;
}> {
  return getContacts({
    page: query.page,
    pageSize: query.pageSize,
    search: query.query,
    status: query.status,
    stage: query.stage,
    ownerId: query.ownerId,
    tags: query.tags,
    labelIds: query.labelIds,
    includeDeleted: query.includeDeleted,
  });
}

// ============================================================================
// Contact Methods
// ============================================================================

export async function addContactMethod(
  contactId: string,
  method: ContactMethodInput
): Promise<ContactMethod> {
  return api.post<ContactMethod>(`/api/v1/contacts/${contactId}/methods`, method);
}

export async function updateContactMethod(
  methodId: string,
  data: Partial<ContactMethodInput>
): Promise<ContactMethod> {
  return api.patch<ContactMethod>(`/api/v1/contacts/methods/${methodId}`, data);
}

export async function deleteContactMethod(methodId: string): Promise<void> {
  return api.delete(`/api/v1/contacts/methods/${methodId}`);
}

export async function setPrimaryContactMethod(
  _contactId: string,
  methodId: string
): Promise<ContactMethod> {
  return updateContactMethod(methodId, { isPrimary: true });
}

// ============================================================================
// Contact Activities
// ============================================================================

export interface ContactActivity {
  id: string;
  contactId: string;
  activityType: string;
  subject: string;
  description?: string | null;
  activityDate?: string | null;
  durationMinutes?: number | null;
  status: string;
  outcome?: string | null;
  metadata?: Record<string, unknown> | null;
  performedBy: string;
  createdAt: string;
  updatedAt: string;
}

export async function getContactActivities(
  contactId: string,
  params?: { limit?: number; offset?: number }
): Promise<ContactActivity[]> {
  return api.get<ContactActivity[]>(`/api/v1/contacts/${contactId}/activities`, {
    params,
  });
}

export async function addContactActivity(
  contactId: string,
  activity: {
    activityType: string;
    subject: string;
    description?: string;
    activityDate?: string;
    durationMinutes?: number;
    status?: string;
    outcome?: string;
    metadata?: Record<string, unknown>;
  }
): Promise<ContactActivity> {
  return api.post<ContactActivity>(`/api/v1/contacts/${contactId}/activities`, {
    activityType: activity.activityType,
    subject: activity.subject,
    description: activity.description,
    activityDate: activity.activityDate,
    durationMinutes: activity.durationMinutes,
    status: activity.status ?? "completed",
    outcome: activity.outcome,
    metadata: activity.metadata,
  });
}

export async function getContactTags(contactId: string): Promise<string[]> {
  const contact = await getContact(contactId);
  return contact.tags ?? [];
}

export async function addContactTag(contactId: string, tag: string): Promise<Contact> {
  const tags = await getContactTags(contactId);
  const nextTags = Array.from(new Set([...tags, tag]));
  return updateContact(contactId, { tags: nextTags });
}

export async function removeContactTag(contactId: string, tag: string): Promise<Contact> {
  const tags = await getContactTags(contactId);
  const nextTags = tags.filter((existing) => existing !== tag);
  return updateContact(contactId, { tags: nextTags });
}

// ============================================================================
// Labels and Custom Fields
// ============================================================================

export async function getLabelDefinitions(params?: {
  category?: string;
  includeHidden?: boolean;
}): Promise<ContactLabelDefinition[]> {
  return api.get<ContactLabelDefinition[]>("/api/v1/contacts/labels/definitions", {
    params,
  });
}

export async function createLabelDefinition(data: {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  category?: string;
  displayOrder?: number;
  isVisible?: boolean;
  isDefault?: boolean;
  metadata?: Record<string, unknown>;
}): Promise<ContactLabelDefinition> {
  return api.post<ContactLabelDefinition>("/api/v1/contacts/labels/definitions", data);
}

export interface FieldDefinition {
  id: string;
  name: string;
  fieldKey?: string | null;
  fieldType:
    | "text"
    | "number"
    | "date"
    | "datetime"
    | "boolean"
    | "select"
    | "multiselect"
    | "url"
    | "email"
    | "phone"
    | "currency"
    | "percentage"
    | "json";
  description?: string | null;
  options?: Array<Record<string, unknown>> | null;
  isRequired?: boolean;
  isUnique?: boolean;
  isSearchable?: boolean;
  defaultValue?: unknown;
  validationRules?: Record<string, unknown> | null;
  displayOrder?: number;
  placeholder?: string | null;
  helpText?: string | null;
  fieldGroup?: string | null;
  isVisible?: boolean;
  isEditable?: boolean;
  requiredPermission?: string | null;
  isSystem?: boolean;
  isEncrypted?: boolean;
  metadata?: Record<string, unknown> | null;
}

export async function getFieldDefinitions(params?: {
  fieldGroup?: string;
  includeHidden?: boolean;
}): Promise<FieldDefinition[]> {
  return api.get<FieldDefinition[]>("/api/v1/contacts/fields/definitions", {
    params,
  });
}

export async function createFieldDefinition(data: {
  name: string;
  fieldKey?: string;
  fieldType: FieldDefinition["fieldType"];
  description?: string;
  options?: Array<Record<string, unknown>>;
  isRequired?: boolean;
  isUnique?: boolean;
  isSearchable?: boolean;
  defaultValue?: unknown;
  validationRules?: Record<string, unknown>;
  displayOrder?: number;
  placeholder?: string;
  helpText?: string;
  fieldGroup?: string;
  isVisible?: boolean;
  isEditable?: boolean;
  requiredPermission?: string;
  isEncrypted?: boolean;
  metadata?: Record<string, unknown>;
}): Promise<FieldDefinition> {
  return api.post<FieldDefinition>("/api/v1/contacts/fields/definitions", data);
}

// ============================================================================
// Bulk Operations
// ============================================================================

export async function bulkUpdateContacts(data: {
  contactIds: string[];
  updates: Partial<{
    status: ContactStatus;
    stage: ContactStage;
    ownerId: string;
    assignedTeamId: string;
    notes: string;
    tags: string[];
  }>;
}): Promise<{ updated: number; errors?: Array<Record<string, string>> }> {
  return api.post<{ updated: number; errors?: Array<Record<string, string>> }>(
    "/api/v1/contacts/bulk/update",
    {
      contactIds: data.contactIds,
      updateData: {
        status: data.updates.status,
        stage: data.updates.stage,
        ownerId: data.updates.ownerId,
        assignedTeamId: data.updates.assignedTeamId,
        notes: data.updates.notes,
        tags: data.updates.tags,
      },
    }
  );
}

export async function bulkDeleteContacts(data: {
  contactIds: string[];
  hardDelete?: boolean;
}): Promise<{ deleted: number; errors?: Array<Record<string, string>> }> {
  return api.post<{ deleted: number; errors?: Array<Record<string, string>> }>(
    "/api/v1/contacts/bulk/delete",
    {
      contactIds: data.contactIds,
      hardDelete: data.hardDelete,
    }
  );
}

function unsupportedContactsFeature(feature: string): never {
  throw new ApiClientError(
    `${feature} is not supported by the backend yet`,
    501,
    "NOT_IMPLEMENTED"
  );
}

export async function mergeContacts(
  _primaryContactId: string,
  _mergeContactIds: string[]
): Promise<Contact> {
  return unsupportedContactsFeature("Contact merge");
}

export async function importContacts(
  _file: File,
  _mapping?: Record<string, string>
): Promise<{ imported: number; failed: number }> {
  return unsupportedContactsFeature("Contact import");
}

export async function exportContacts(_params: {
  format: "csv" | "xlsx" | "json";
  contactIds?: string[];
  filters?: Record<string, unknown>;
}): Promise<Blob> {
  return unsupportedContactsFeature("Contact export");
}

export interface ContactStats {
  total: number;
  active: number;
  inactive: number;
  archived: number;
  byStage: Record<ContactStage, number>;
  // Additional computed fields for UI
  totalContacts: number;
  accountCount: number;
  leadCount: number;
  partnerCount: number;
  newLast30Days: number;
}

export async function getContactStats(_params?: { periodDays?: number }): Promise<ContactStats> {
  return unsupportedContactsFeature("Contact stats");
}
