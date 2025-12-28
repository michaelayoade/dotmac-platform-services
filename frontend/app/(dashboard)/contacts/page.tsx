"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Users,
  Plus,
  Search,
  Filter,
  RefreshCcw,
  Mail,
  Phone,
  Building,
  Tag,
  MoreHorizontal,
  Trash2,
  Edit,
  Download,
  Upload,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input, Modal } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useContacts,
  useContactStats,
  useDeleteContact,
  useExportContacts,
} from "@/lib/hooks/api/use-contacts";
import type { ContactStage } from "@/lib/api/contacts";

type ContactType = "account" | "lead" | "partner" | "vendor" | "other";

const typeConfig: Record<ContactType, { label: string; color: string }> = {
  account: { label: "Account", color: "bg-status-success/15 text-status-success" },
  lead: { label: "Lead", color: "bg-status-info/15 text-status-info" },
  partner: { label: "Partner", color: "bg-accent-subtle text-accent" },
  vendor: { label: "Vendor", color: "bg-highlight-subtle text-highlight" },
  other: { label: "Other", color: "bg-surface-overlay text-text-muted" },
};

export default function ContactsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<ContactStage | "all">("all");
  const [page, setPage] = useState(1);
  const [selectedContacts, setSelectedContacts] = useState<Set<string>>(new Set());

  const { data, isLoading, refetch } = useContacts({
    page,
    pageSize: 20,
    search: searchQuery || undefined,
    type: typeFilter !== "all" ? typeFilter : undefined,
  });
  const { data: stats } = useContactStats();

  const deleteContact = useDeleteContact();
  const exportContacts = useExportContacts();

  const contacts = data?.contacts || [];
  const totalPages = data?.pageCount || 1;

  const handleDelete = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: "Delete Contact",
      description: `Are you sure you want to delete "${name}"? This action cannot be undone.`,
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteContact.mutateAsync(id);
        toast({ title: "Contact deleted" });
      } catch {
        toast({ title: "Failed to delete contact", variant: "error" });
      }
    }
  };

  const handleExport = async () => {
    try {
      const result = await exportContacts.mutateAsync({
        format: "csv",
        contactIds: selectedContacts.size > 0 ? Array.from(selectedContacts) : undefined,
      });

      const blob = new Blob([result], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `contacts-${format(new Date(), "yyyy-MM-dd")}.csv`;
      a.click();
      URL.revokeObjectURL(url);

      toast({ title: "Contacts exported successfully" });
    } catch {
      toast({ title: "Failed to export contacts", variant: "error" });
    }
  };

  const toggleSelectContact = (id: string) => {
    const newSelected = new Set(selectedContacts);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedContacts(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedContacts.size === contacts.length) {
      setSelectedContacts(new Set());
    } else {
      setSelectedContacts(new Set(contacts.map((c) => c.id)));
    }
  };

  if (isLoading) {
    return <ContactsSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title="Contacts"
        description="Manage your contacts and leads"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
            <Link href="/contacts/import">
              <Button variant="outline">
                <Upload className="w-4 h-4 mr-2" />
                Import
              </Button>
            </Link>
            <Link href="/contacts/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Add Contact
              </Button>
            </Link>
          </div>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Total Contacts</p>
          <p className="text-2xl font-semibold text-text-primary">
            {stats?.totalContacts?.toLocaleString() || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Accounts</p>
          <p className="text-2xl font-semibold text-status-success">
            {stats?.accountCount?.toLocaleString() || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Leads</p>
          <p className="text-2xl font-semibold text-status-info">
            {stats?.leadCount?.toLocaleString() || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">Partners</p>
          <p className="text-2xl font-semibold text-accent">
            {stats?.partnerCount?.toLocaleString() || 0}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-text-muted mb-1">New (30d)</p>
          <p className="text-2xl font-semibold text-text-primary">
            {stats?.newLast30Days?.toLocaleString() || 0}
          </p>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            placeholder="Search contacts..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value as ContactStage | "all");
              setPage(1);
            }}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Types</option>
            <option value="account">Account</option>
            <option value="lead">Lead</option>
            <option value="partner">Partner</option>
            <option value="vendor">Vendor</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* Contacts Table */}
      {contacts.length === 0 ? (
        <Card className="p-12 text-center">
          <Users className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No contacts found</h3>
          <p className="text-text-muted mb-6">
            {searchQuery || typeFilter !== "all"
              ? "Try adjusting your filters"
              : "Add your first contact to get started"}
          </p>
          <Link href="/contacts/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Contact
            </Button>
          </Link>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="data-table" aria-label="Contacts list"><caption className="sr-only">Contacts list</caption>
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="text-left px-4 py-3 w-12">
                    <input
                      type="checkbox"
                      checked={selectedContacts.size === contacts.length}
                      onChange={toggleSelectAll}
                      className="rounded border-border-subtle"
                    />
                  </th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Contact</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Type</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Company</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Email</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Phone</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Added</th>
                  <th className="text-left text-sm font-medium text-text-muted px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {contacts.map((contact) => {
                  const type = typeConfig[contact.type as ContactType] || typeConfig.other;

                  return (
                    <tr key={contact.id} className="border-b border-border-subtle hover:bg-surface-overlay/50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedContacts.has(contact.id)}
                          onChange={() => toggleSelectContact(contact.id)}
                          className="rounded border-border-subtle"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-accent-subtle flex items-center justify-center">
                            <span className="text-accent font-medium">
                              {contact.firstName?.[0]}{contact.lastName?.[0]}
                            </span>
                          </div>
                          <div>
                            <Link
                              href={`/contacts/${contact.id}`}
                              className="font-medium text-text-primary hover:text-accent transition-colors"
                            >
                              {contact.firstName} {contact.lastName}
                            </Link>
                            {contact.title && (
                              <p className="text-xs text-text-muted">{contact.title}</p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", type.color)}>
                          {type.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-secondary">{contact.company || "-"}</span>
                      </td>
                      <td className="px-4 py-3">
                        {contact.email ? (
                          <a href={`mailto:${contact.email}`} className="text-sm text-accent hover:underline">
                            {contact.email}
                          </a>
                        ) : (
                          <span className="text-sm text-text-muted">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-secondary">{contact.phone || "-"}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-text-muted">
                          {formatDistanceToNow(new Date(contact.createdAt), { addSuffix: true })}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Link href={`/contacts/${contact.id}/edit`}>
                            <Button variant="ghost" size="sm">
                              <Edit className="w-4 h-4" />
                            </Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(contact.id, `${contact.firstName} ${contact.lastName}`)}
                            className="text-status-error hover:text-status-error"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
              <p className="text-sm text-text-muted">
                Page {page} of {totalPages}
                {selectedContacts.size > 0 && (
                  <span className="ml-2">• {selectedContacts.size} selected</span>
                )}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function ContactsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="card">
        <div className="p-4 space-y-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="h-12 bg-surface-overlay rounded" />
          ))}
        </div>
      </div>
    </div>
  );
}
