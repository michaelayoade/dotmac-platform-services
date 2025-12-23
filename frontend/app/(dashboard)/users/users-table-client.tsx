"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useCallback, useMemo, type ElementType } from "react";
import { type ColumnDef } from "@tanstack/react-table";
import {
  DataTable,
  type BulkAction,
  type QuickFilter,
  type FilterConfig,
} from "@dotmac/data-table";
import { useToast } from "@dotmac/core";
import {
  MoreHorizontal,
  Mail,
  Shield,
  Trash2,
  UserCheck,
  UserX,
  Edit,
  Eye,
  Ban,
  CheckCircle,
  Clock,
  AlertCircle,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { type User } from "@/lib/api/users";

interface UsersTableClientProps {
  initialUsers: User[];
  pageCount: number;
  totalCount: number;
  currentPage: number;
  currentSearch: string;
  currentStatus: string;
}

export function UsersTableClient({
  initialUsers,
  pageCount,
  totalCount,
  currentPage,
  currentSearch,
  currentStatus,
}: UsersTableClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [selectedUsers, setSelectedUsers] = useState<User[]>([]);

  // Update URL params for server-side pagination
  const updateParams = useCallback(
    (updates: Record<string, string | number>) => {
      const params = new URLSearchParams(searchParams.toString());
      Object.entries(updates).forEach(([key, value]) => {
        if (value) {
          params.set(key, String(value));
        } else {
          params.delete(key);
        }
      });
      router.push(`/users?${params.toString()}`);
    },
    [router, searchParams]
  );

  // Column definitions
  const columns: ColumnDef<User>[] = useMemo(
    () => [
      {
        accessorKey: "name",
        header: "User",
        cell: ({ row }) => {
          const user = row.original;
          return (
            <div className="flex items-center gap-3">
              {/* Avatar */}
              <div className="relative">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent/80 to-highlight/80 flex items-center justify-center text-sm font-semibold text-text-inverse">
                  {user.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()}
                </div>
                {user.status === "active" && (
                  <span className="absolute bottom-0 right-0 w-3 h-3 bg-status-success border-2 border-surface-elevated rounded-full" />
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">
                  {user.name}
                </p>
                <p className="text-xs text-text-muted">{user.email}</p>
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: "role",
        header: "Role",
        cell: ({ row }) => {
          const role = row.original.role;
          const roleColors: Record<string, string> = {
            admin: "bg-status-error/15 text-status-error",
            owner: "bg-highlight-subtle text-highlight",
            member: "bg-surface-overlay text-text-secondary",
            viewer: "bg-surface-overlay text-text-muted",
          };
          return (
            <span
              className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold capitalize",
                roleColors[role] || roleColors.member
              )}
            >
              <Shield className="w-3 h-3" />
              {role}
            </span>
          );
        },
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
          const status = row.original.status;
          const statusConfig: Record<
            string,
            { icon: ElementType; class: string; label: string }
          > = {
            active: {
              icon: CheckCircle,
              class: "status-badge--success",
              label: "Active",
            },
            pending: {
              icon: Clock,
              class: "status-badge--warning",
              label: "Pending",
            },
            suspended: {
              icon: Ban,
              class: "status-badge--error",
              label: "Suspended",
            },
            inactive: {
              icon: AlertCircle,
              class: "bg-surface-overlay text-text-muted",
              label: "Inactive",
            },
          };
          const config = statusConfig[status] || statusConfig.inactive;
          const Icon = config.icon;
          return (
            <span className={cn("status-badge", config.class)}>
              <Icon className="w-3 h-3" />
              {config.label}
            </span>
          );
        },
      },
      {
        accessorKey: "tenant",
        header: "Organization",
        cell: ({ row }) => (
          <span className="text-sm text-text-secondary">
            {row.original.tenant?.name || "—"}
          </span>
        ),
      },
      {
        accessorKey: "lastActive",
        header: "Last Active",
        cell: ({ row }) => {
          const date = row.original.lastActive;
          if (!date) return <span className="text-text-muted">Never</span>;
          return (
            <span className="text-sm text-text-secondary tabular-nums">
              {new Date(date).toLocaleDateString()}
            </span>
          );
        },
      },
      {
        accessorKey: "createdAt",
        header: "Created",
        cell: ({ row }) => (
          <span className="text-sm text-text-muted tabular-nums">
            {new Date(row.original.createdAt).toLocaleDateString()}
          </span>
        ),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <UserActionsMenu user={row.original} onAction={handleUserAction} />
        ),
        size: 50,
      },
    ],
    []
  );

  // Bulk actions
  const bulkActions: BulkAction<User>[] = [
    {
      label: "Send Email",
      icon: Mail,
      action: async (users) => {
        toast({
          title: "Email sent",
          description: `Email sent to ${users.length} user(s)`,
          variant: "success",
        });
      },
    },
    {
      label: "Activate",
      icon: UserCheck,
      action: async (users) => {
        toast({
          title: "Users activated",
          description: `${users.length} user(s) activated`,
          variant: "success",
        });
      },
      disabled: (users) => users.every((u) => u.status === "active"),
    },
    {
      label: "Suspend",
      icon: UserX,
      variant: "destructive",
      action: async (users) => {
        toast({
          title: "Users suspended",
          description: `${users.length} user(s) suspended`,
          variant: "warning",
        });
      },
      confirm: {
        title: "Suspend Users",
        description: "Are you sure you want to suspend these users? They will lose access immediately.",
        confirmLabel: "Suspend",
      },
    },
    {
      label: "Delete",
      icon: Trash2,
      variant: "destructive",
      action: async (users) => {
        toast({
          title: "Users deleted",
          description: `${users.length} user(s) deleted`,
          variant: "error",
        });
      },
      confirm: {
        title: "Delete Users",
        description: "This action cannot be undone. Are you sure?",
        confirmLabel: "Delete",
      },
    },
  ];

  // Quick filters
  const quickFilters: QuickFilter<User>[] = [
    {
      label: "Active",
      filter: (user) => user.status === "active",
    },
    {
      label: "Admins",
      filter: (user) => user.role === "admin",
    },
    {
      label: "Pending Invite",
      filter: (user) => user.status === "pending",
    },
    {
      label: "Recently Active",
      filter: (user) =>
        user.lastActive
          ? new Date(user.lastActive) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
          : false,
    },
  ];

  // Advanced filters
  const filters: FilterConfig[] = [
    {
      column: "status",
      label: "Status",
      type: "select",
      options: [
        { label: "Active", value: "active" },
        { label: "Pending", value: "pending" },
        { label: "Suspended", value: "suspended" },
        { label: "Inactive", value: "inactive" },
      ],
    },
    {
      column: "role",
      label: "Role",
      type: "select",
      options: [
        { label: "Admin", value: "admin" },
        { label: "Owner", value: "owner" },
        { label: "Member", value: "member" },
        { label: "Viewer", value: "viewer" },
      ],
    },
  ];

  // Handle user actions
  const handleUserAction = (action: string, user: User) => {
    switch (action) {
      case "view":
        router.push(`/users/${user.id}`);
        break;
      case "edit":
        router.push(`/users/${user.id}/edit`);
        break;
      case "delete":
        // Handle delete
        break;
    }
  };

  // Confirmation adapter for bulk actions
  const confirmAdapter = async (options: {
    title: string;
    description: string;
    confirmLabel?: string;
  }) => {
    return window.confirm(`${options.title}\n\n${options.description}`);
  };

  return (
    <div className="card overflow-hidden animate-fade-up">
      <DataTable
        columns={columns}
        data={initialUsers}
        selectable
        onSelectionChange={setSelectedUsers}
        bulkActions={bulkActions}
        searchable
        searchPlaceholder="Search users by name or email..."
        searchableColumns={["name", "email"]}
        globalFilter={currentSearch}
        onGlobalFilterChange={(value) => updateParams({ search: value, page: 1 })}
        quickFilters={quickFilters}
        filters={filters}
        sortable
        defaultSorting={[{ id: "createdAt", desc: true }]}
        pagination
        serverSidePagination={{
          pageIndex: currentPage - 1,
          pageSize: 20,
          pageCount,
          totalRows: totalCount,
          onPageChange: (pageIndex) => updateParams({ page: pageIndex + 1 }),
          onPageSizeChange: () => {},
        }}
        exportable
        exportFilename="users-export"
        columnVisibility
        onRowClick={(user) => router.push(`/users/${user.id}`)}
        confirmAdapter={confirmAdapter}
        translations={{
          searchPlaceholder: "Search users...",
          filtersLabel: "Filters",
          clearFilters: "Clear filters",
          exportLabel: "Export",
          columnsLabel: "Columns",
          bulkActionsLabel: "Bulk Actions",
          selectedCount: (selected, total) => `${selected} of ${total} selected`,
          totalCount: (total) => `${total} users`,
          loadingLabel: "Loading users...",
          emptyLabel: "No users found",
          rowsPerPage: "Rows",
          pageOf: (page, pageCount) => `Page ${page} of ${pageCount}`,
          previous: "Previous",
          next: "Next",
          sortAscending: "Sort A-Z",
          sortDescending: "Sort Z-A",
        }}
      />
    </div>
  );
}

// Actions dropdown menu
function UserActionsMenu({
  user,
  onAction,
}: {
  user: User;
  onAction: (action: string, user: User) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors"
      >
        <MoreHorizontal className="w-4 h-4" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-1 w-40 bg-surface-elevated border border-border rounded-lg shadow-lg overflow-hidden z-20 animate-fade-in">
            <div className="py-1">
              <button
                onClick={() => {
                  onAction("view", user);
                  setIsOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
              >
                <Eye className="w-4 h-4" />
                View
              </button>
              <button
                onClick={() => {
                  onAction("edit", user);
                  setIsOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
              >
                <Edit className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => {
                  onAction("email", user);
                  setIsOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
              >
                <Mail className="w-4 h-4" />
                Send Email
              </button>
              <div className="border-t border-border my-1" />
              <button
                onClick={() => {
                  onAction("delete", user);
                  setIsOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-status-error hover:bg-status-error/10"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
