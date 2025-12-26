import { Suspense } from "react";
import Link from "next/link";
import { Plus, Download, Filter, MoreHorizontal, Mail, Shield, Trash2 } from "lucide-react";
import { DataTable, type ColumnDef } from "@/lib/dotmac/data-table";
import { Button } from "@/lib/dotmac/core";

import { getUsers, type User } from "@/lib/api/users";
import { fetchOrNull } from "@/lib/api/fetch-or-null";
import { UsersTableClient } from "./users-table-client";

export const metadata = {
  title: "Users",
  description: "Manage platform users and permissions",
};

export default async function UsersPage({
  searchParams,
}: {
  searchParams: { page?: string; search?: string; status?: string };
}) {
  const page = Number(searchParams.page) || 1;
  const search = searchParams.search || "";
  const status = searchParams.status || "";

  const userResponse = await fetchOrNull(() =>
    getUsers({
      page,
      search,
      status,
      pageSize: 20,
    })
  );
  const users = userResponse?.users ?? [];
  const totalCount = userResponse?.totalCount ?? null;
  const pageCount = userResponse?.pageCount ?? 1;

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/" className="hover:text-text-secondary">
          Dashboard
        </Link>
        <span aria-hidden="true">/</span>
        <span className="text-text-primary">Users</span>
      </nav>

      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Users</h1>
          <p className="page-description">
            Manage user accounts, roles, and permissions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="hidden sm:flex">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Link href="/users/new">
            <Button className="shadow-glow-sm hover:shadow-glow">
              <Plus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="quick-stats">
        <div className="quick-stat">
          <p className="metric-label">Total Users</p>
          <p className="metric-value text-2xl">
            {totalCount === null ? "—" : totalCount.toLocaleString()}
          </p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Active (page)</p>
          <p className="metric-value text-2xl text-status-success">
            {users.filter((u) => u.status === "active").length}
          </p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Pending (page)</p>
          <p className="metric-value text-2xl text-status-warning">
            {users.filter((u) => u.status === "pending").length}
          </p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Suspended (page)</p>
          <p className="metric-value text-2xl text-status-error">
            {users.filter((u) => u.status === "suspended").length}
          </p>
        </div>
      </div>

      {/* Users Table */}
      <Suspense fallback={<TableSkeleton />}>
        <UsersTableClient
          initialUsers={users}
          pageCount={pageCount}
          totalCount={totalCount ?? 0}
          currentPage={page}
          currentSearch={search}
          currentStatus={status}
        />
      </Suspense>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="card overflow-hidden">
      <div className="p-4 border-b border-border flex items-center gap-4">
        <div className="h-10 w-64 skeleton" />
        <div className="h-10 w-32 skeleton" />
      </div>
      <div className="divide-y divide-border-subtle">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="px-4 py-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-full skeleton" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-48 skeleton" />
              <div className="h-3 w-32 skeleton" />
            </div>
            <div className="h-6 w-20 skeleton rounded-full" />
            <div className="h-4 w-24 skeleton" />
          </div>
        ))}
      </div>
    </div>
  );
}
