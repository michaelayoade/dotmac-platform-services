"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getContacts,
  getContact,
  createContact,
  updateContact,
  deleteContact,
  searchContacts,
  getContactMethods,
  addContactMethod,
  updateContactMethod,
  deleteContactMethod,
  setPrimaryContactMethod,
  getContactActivities,
  addContactActivity,
  getContactTags,
  addContactTag,
  removeContactTag,
  mergeContacts,
  bulkUpdateContacts,
  bulkDeleteContacts,
  importContacts,
  exportContacts,
  getContactStats,
  type GetContactsParams,
  type Contact,
  type CreateContactData,
  type ContactSearchQuery,
  type ContactMethod,
  type ContactMethodInput,
  type ContactActivity,
  type ContactStats,
} from "@/lib/api/contacts";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Contacts Hooks
// ============================================================================

export function useContacts(params?: GetContactsParams) {
  return useQuery({
    queryKey: queryKeys.contacts.list(params),
    queryFn: () => getContacts(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useContact(id: string) {
  return useQuery({
    queryKey: queryKeys.contacts.detail(id),
    queryFn: () => getContact(id),
    enabled: !!id,
  });
}

export function useCreateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createContact,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.stats(),
      });
    },
  });
}

export function useUpdateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateContactData> }) =>
      updateContact(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.contacts.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.all,
      });
    },
  });
}

export function useDeleteContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteContact(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.stats(),
      });
    },
  });
}

export function useSearchContacts() {
  return useMutation({
    mutationFn: (query: ContactSearchQuery) => searchContacts(query),
  });
}

// ============================================================================
// Contact Methods Hooks
// ============================================================================

export function useContactMethods(contactId: string) {
  return useQuery({
    queryKey: queryKeys.contacts.methods(contactId),
    queryFn: () => getContactMethods(contactId),
    enabled: !!contactId,
  });
}

export function useAddContactMethod() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      contactId,
      method,
    }: {
      contactId: string;
      method: ContactMethodInput;
    }) => addContactMethod(contactId, method),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.methods(variables.contactId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.detail(variables.contactId),
      });
    },
  });
}

export function useUpdateContactMethod() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      contactId,
      methodId,
      data,
    }: {
      contactId: string;
      methodId: string;
      data: Partial<ContactMethodInput>;
    }) => updateContactMethod(methodId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.methods(variables.contactId),
      });
    },
  });
}

export function useDeleteContactMethod() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ contactId, methodId }: { contactId: string; methodId: string }) =>
      deleteContactMethod(methodId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.methods(variables.contactId),
      });
    },
  });
}

export function useSetPrimaryContactMethod() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ contactId, methodId }: { contactId: string; methodId: string }) =>
      setPrimaryContactMethod(contactId, methodId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.methods(variables.contactId),
      });
    },
  });
}

// ============================================================================
// Contact Activities Hooks
// ============================================================================

export function useContactActivities(contactId: string) {
  return useQuery({
    queryKey: queryKeys.contacts.activities(contactId),
    queryFn: () => getContactActivities(contactId),
    enabled: !!contactId,
  });
}

export function useAddContactActivity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      contactId,
      activity,
    }: {
      contactId: string;
      activity: {
        activityType: string;
        subject: string;
        description?: string;
        activityDate?: string;
        durationMinutes?: number;
        status?: string;
        outcome?: string;
        metadata?: Record<string, unknown>;
      };
    }) => addContactActivity(contactId, activity),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.activities(variables.contactId),
      });
    },
  });
}

// ============================================================================
// Contact Tags Hooks
// ============================================================================

export function useContactTags(contactId: string) {
  return useQuery({
    queryKey: queryKeys.contacts.tags(contactId),
    queryFn: () => getContactTags(contactId),
    enabled: !!contactId,
  });
}

export function useAddContactTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ contactId, tag }: { contactId: string; tag: string }) =>
      addContactTag(contactId, tag),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.tags(variables.contactId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.detail(variables.contactId),
      });
    },
  });
}

export function useRemoveContactTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ contactId, tag }: { contactId: string; tag: string }) =>
      removeContactTag(contactId, tag),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.tags(variables.contactId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.detail(variables.contactId),
      });
    },
  });
}

// ============================================================================
// Bulk Operations Hooks
// ============================================================================

export function useMergeContacts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      primaryContactId,
      mergeContactIds,
    }: {
      primaryContactId: string;
      mergeContactIds: string[];
    }) => mergeContacts(primaryContactId, mergeContactIds),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.all,
      });
    },
  });
}

export function useBulkUpdateContacts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      contactIds,
      updates,
    }: {
      contactIds: string[];
      updates: Partial<CreateContactData>;
    }) => bulkUpdateContacts({ contactIds, updates }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.all,
      });
    },
  });
}

export function useBulkDeleteContacts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: bulkDeleteContacts,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.stats(),
      });
    },
  });
}

// ============================================================================
// Import/Export Hooks
// ============================================================================

export function useImportContacts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, mapping }: { file: File; mapping?: Record<string, string> }) =>
      importContacts(file, mapping),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.contacts.stats(),
      });
    },
  });
}

export function useExportContacts() {
  return useMutation({
    mutationFn: (params: {
      format: "csv" | "xlsx" | "json";
      contactIds?: string[];
      filters?: Record<string, unknown>;
    }) => exportContacts(params),
  });
}

// ============================================================================
// Contact Stats Hook
// ============================================================================

export function useContactStats(params?: { periodDays?: number }) {
  return useQuery({
    queryKey: queryKeys.contacts.stats(params),
    queryFn: () => getContactStats(params),
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetContactsParams,
  Contact,
  CreateContactData,
  ContactSearchQuery,
  ContactMethod,
  ContactActivity,
  ContactStats,
};
