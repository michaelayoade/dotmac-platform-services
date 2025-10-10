"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Search, Shield, UserMinus, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type UserRecord = {
  id: string;
  name: string;
  email: string;
  role: "Owner" | "Administrator" | "Auditor" | "Support";
  status: "Active" | "Invited" | "Suspended";
  lastSeen: string;
  mfaEnabled: boolean;
};

const USERS: UserRecord[] = [
  {
    id: "USR-9081",
    name: "Alex Johnson",
    email: "alex.johnson@example.com",
    role: "Owner",
    status: "Active",
    lastSeen: "Just now",
    mfaEnabled: true,
  },
  {
    id: "USR-9078",
    name: "Sara Chen",
    email: "sara.chen@example.com",
    role: "Administrator",
    status: "Active",
    lastSeen: "5 minutes ago",
    mfaEnabled: true,
  },
  {
    id: "USR-9071",
    name: "Jamie Patel",
    email: "jamie.patel@example.com",
    role: "Support",
    status: "Invited",
    lastSeen: "Not yet",
    mfaEnabled: false,
  },
  {
    id: "USR-9064",
    name: "Taylor Smith",
    email: "taylor.smith@example.com",
    role: "Auditor",
    status: "Suspended",
    lastSeen: "3 days ago",
    mfaEnabled: false,
  },
];

const ROLE_FILTERS = ["All roles", "Owner", "Administrator", "Auditor", "Support"] as const;
const STATUS_COLORS: Record<UserRecord["status"], string> = {
  Active: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
  Invited: "bg-blue-500/10 text-blue-200 border border-blue-500/20",
  Suspended: "bg-red-500/10 text-red-200 border border-red-500/20",
};

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<(typeof ROLE_FILTERS)[number]>("All roles");

  const filtered = useMemo(() => {
    return USERS.filter((user) => {
      const matchesSearch =
        user.name.toLowerCase().includes(search.toLowerCase()) ||
        user.email.toLowerCase().includes(search.toLowerCase());
      const matchesRole = role === "All roles" || user.role === role;
      return matchesSearch && matchesRole;
    });
  }, [search, role]);

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">User management</p>
            <h1 className="text-3xl font-semibold text-foreground">Administrators & elevated users</h1>
            <p className="text-sm text-muted-foreground">
              Invite new platform administrators, adjust roles and review account security status.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" disabled className="gap-2">
              <UserMinus className="h-4 w-4" />
              Disable selected
            </Button>
            <Button className="gap-2">
              <UserPlus className="h-4 w-4" />
              Invite admin
            </Button>
          </div>
        </div>
      </header>

      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex w-full max-w-md items-center gap-3 rounded-lg border border-border bg-card px-3 py-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by name or email"
                className="border-0 bg-transparent px-0 text-sm focus-visible:ring-0"
              />
            </div>
            <select
              value={role}
              onChange={(event) => setRole(event.target.value as (typeof ROLE_FILTERS)[number])}
              className="h-10 w-full max-w-xs rounded-md border border-border bg-card px-3 text-sm text-foreground focus:border-primary focus:outline-none"
            >
              {ROLE_FILTERS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          <CardDescription>
            There are {filtered.length} of {USERS.length} privileged users displayed.{" "}
            <Link href="/admin/settings" className="text-primary underline underline-offset-4">
              Configure password & session policies
            </Link>
            .
          </CardDescription>
        </CardHeader>

        <CardContent className="overflow-x-auto">
          <Table data-testid="user-list">
            <TableHeader>
              <TableRow className="border-border/40">
                <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">User</TableHead>
                <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Email</TableHead>
                <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Role</TableHead>
                <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Status</TableHead>
                <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">MFA</TableHead>
                <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Last seen</TableHead>
                <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((user) => (
                <TableRow key={user.id} className="border-border/20">
                  <TableCell>
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-foreground">{user.name}</p>
                      <p className="text-xs font-mono text-muted-foreground">{user.id}</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{user.email}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="border-border/60 text-foreground">
                      {user.role}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${STATUS_COLORS[user.status]}`}>
                      {user.status}
                    </span>
                  </TableCell>
                  <TableCell>
                    {user.mfaEnabled ? (
                      <span className="inline-flex items-center gap-2 text-sm text-emerald-300">
                        <Shield className="h-4 w-4" />
                        Enabled
                      </span>
                    ) : (
                      <span className="text-sm text-red-300">Disabled</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{user.lastSeen}</TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button size="sm" variant="ghost" className="text-xs text-primary">
                        Manage
                      </Button>
                      <Button size="sm" variant="ghost" className="text-xs text-muted-foreground hover:text-destructive">
                        Remove
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-sm text-muted-foreground">
                    No administrators match the current filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
