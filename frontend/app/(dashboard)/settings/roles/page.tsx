"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Plus,
  Shield,
  Users,
  Check,
  X,
  Trash2,
  Edit2,
  Lock,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useRoles,
  useRole,
  usePermissions,
  useCreateRole,
  useUpdateRole,
  useDeleteRole,
} from "@/lib/hooks/api/use-rbac";
import type { Role, Permission, CreateRoleData, UpdateRoleData } from "@/lib/api/rbac";

export default function RolesSettingsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // Data fetching
  const { data: roles = [], isLoading: rolesLoading } = useRoles();
  const { data: selectedRole, isLoading: roleLoading } = useRole(
    selectedRoleId || ""
  );
  const { data: allPermissions = [], isLoading: permissionsLoading } =
    usePermissions();

  // Mutations
  const createRole = useCreateRole();
  const updateRole = useUpdateRole();
  const deleteRole = useDeleteRole();

  // Form state for creating/editing
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    permissionIds: [] as string[],
  });

  const handleSelectRole = (role: Role) => {
    setSelectedRoleId(role.id);
    setIsCreating(false);
    setIsEditing(false);
  };

  const handleStartCreate = () => {
    setSelectedRoleId(null);
    setIsCreating(true);
    setIsEditing(false);
    setFormData({ name: "", description: "", permissionIds: [] });
  };

  const handleStartEdit = () => {
    if (selectedRole) {
      setFormData({
        name: selectedRole.name,
        description: selectedRole.description,
        permissionIds: selectedRole.permissions.map((p) => p.id),
      });
      setIsEditing(true);
    }
  };

  const handleCancelEdit = () => {
    setIsCreating(false);
    setIsEditing(false);
    setFormData({ name: "", description: "", permissionIds: [] });
  };

  const handleTogglePermission = (permissionId: string) => {
    setFormData((prev) => ({
      ...prev,
      permissionIds: prev.permissionIds.includes(permissionId)
        ? prev.permissionIds.filter((id) => id !== permissionId)
        : [...prev.permissionIds, permissionId],
    }));
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast({
        title: "Error",
        description: "Role name is required",
        variant: "error",
      });
      return;
    }

    try {
      if (isCreating) {
        const newRole = await createRole.mutateAsync(formData as CreateRoleData);
        toast({
          title: "Role created",
          description: `Role "${newRole.name}" has been created successfully.`,
          variant: "success",
        });
        setSelectedRoleId(newRole.id);
        setIsCreating(false);
      } else if (isEditing && selectedRoleId) {
        await updateRole.mutateAsync({
          id: selectedRoleId,
          data: formData as UpdateRoleData,
        });
        toast({
          title: "Role updated",
          description: `Role "${formData.name}" has been updated successfully.`,
          variant: "success",
        });
        setIsEditing(false);
      }
    } catch {
      toast({
        title: "Error",
        description: isCreating
          ? "Failed to create role"
          : "Failed to update role",
        variant: "error",
      });
    }
  };

  const handleDelete = async () => {
    if (!selectedRoleId || !selectedRole) return;

    if (selectedRole.isSystem) {
      toast({
        title: "Cannot delete system role",
        description: "System roles cannot be deleted.",
        variant: "error",
      });
      return;
    }

    const confirmed = await confirm({
      title: "Delete Role",
      description: `Are you sure you want to delete the role "${selectedRole.name}"? This action cannot be undone and will remove this role from all users.`,
      variant: "danger",
    });

    if (!confirmed) return;

    try {
      await deleteRole.mutateAsync(selectedRoleId);
      toast({
        title: "Role deleted",
        description: `Role "${selectedRole.name}" has been deleted.`,
        variant: "success",
      });
      setSelectedRoleId(null);
    } catch {
      toast({
        title: "Error",
        description: "Failed to delete role",
        variant: "error",
      });
    }
  };

  // Group permissions by resource
  const permissionsByResource = allPermissions.reduce(
    (acc, permission) => {
      if (!acc[permission.resource]) {
        acc[permission.resource] = [];
      }
      acc[permission.resource].push(permission);
      return acc;
    },
    {} as Record<string, Permission[]>
  );

  const isFormMode = isCreating || isEditing;
  const currentPermissions = isFormMode
    ? formData.permissionIds
    : selectedRole?.permissions.map((p) => p.id) || [];

  return (
    <div className="space-y-6">
      {/* Confirm Dialog */}
      {dialog}

      {/* Back link */}
      <Link
        href="/settings"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-secondary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Settings
      </Link>

      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">
            Roles & Permissions
          </h1>
          <p className="text-text-muted mt-1">
            Manage user roles and their access permissions
          </p>
        </div>
        <Button
          onClick={handleStartCreate}
          className="shadow-glow-sm hover:shadow-glow"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Role
        </Button>
      </div>

      {/* Main Content - Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Roles List */}
        <div className="lg:col-span-1">
          <div className="card">
            <div className="p-4 border-b border-border">
              <h2 className="text-sm font-semibold text-text-primary">Roles</h2>
            </div>
            <div className="divide-y divide-border">
              {rolesLoading ? (
                <div className="p-4 text-center text-text-muted">
                  Loading roles...
                </div>
              ) : roles.length === 0 ? (
                <div className="p-4 text-center text-text-muted">
                  No roles found
                </div>
              ) : (
                roles.map((role) => (
                  <button
                    key={role.id}
                    onClick={() => handleSelectRole(role)}
                    className={cn(
                      "w-full p-4 text-left hover:bg-surface-hover transition-colors",
                      selectedRoleId === role.id &&
                        !isCreating &&
                        "bg-surface-hover border-l-2 border-accent"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          "w-8 h-8 rounded-lg flex items-center justify-center",
                          role.isSystem
                            ? "bg-status-warning/15"
                            : "bg-accent-subtle"
                        )}
                      >
                        {role.isSystem ? (
                          <Lock className="w-4 h-4 text-status-warning" />
                        ) : (
                          <Shield className="w-4 h-4 text-accent" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-text-primary truncate">
                            {role.name}
                          </p>
                          {role.isSystem && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-status-warning/15 text-status-warning">
                              System
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-text-muted truncate">
                          {role.permissions.length} permissions
                        </p>
                      </div>
                      <div className="flex items-center gap-1 text-text-muted">
                        <Users className="w-3 h-3" />
                        <span className="text-xs">{role.userCount}</span>
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Permissions Editor */}
        <div className="lg:col-span-2">
          <div className="card">
            {!selectedRoleId && !isCreating ? (
              <div className="p-12 text-center">
                <Shield className="w-12 h-12 mx-auto text-text-muted mb-4" />
                <h3 className="text-lg font-semibold text-text-primary mb-2">
                  Select a Role
                </h3>
                <p className="text-text-muted mb-6">
                  Select a role from the list to view and edit its permissions
                </p>
                <Button variant="outline" onClick={handleStartCreate}>
                  <Plus className="w-4 h-4 mr-2" />
                  Create New Role
                </Button>
              </div>
            ) : (
              <>
                {/* Role Header */}
                <div className="p-4 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      {isFormMode ? (
                        <div className="space-y-3">
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) =>
                              setFormData((prev) => ({
                                ...prev,
                                name: e.target.value,
                              }))
                            }
                            placeholder="Role name"
                            className="w-full px-3 py-2 text-lg font-semibold bg-surface-overlay border border-border rounded-md text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                          />
                          <input
                            type="text"
                            value={formData.description}
                            onChange={(e) =>
                              setFormData((prev) => ({
                                ...prev,
                                description: e.target.value,
                              }))
                            }
                            placeholder="Role description"
                            className="w-full px-3 py-1.5 text-sm bg-surface-overlay border border-border rounded-md text-text-muted placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                          />
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-center gap-2">
                            <h2 className="text-lg font-semibold text-text-primary">
                              {selectedRole?.name}
                            </h2>
                            {selectedRole?.isSystem && (
                              <span className="text-xs px-1.5 py-0.5 rounded bg-status-warning/15 text-status-warning">
                                System Role
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-text-muted mt-1">
                            {selectedRole?.description}
                          </p>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {isFormMode ? (
                        <>
                          <Button variant="outline" onClick={handleCancelEdit}>
                            <X className="w-4 h-4 mr-2" />
                            Cancel
                          </Button>
                          <Button
                            onClick={handleSave}
                            disabled={
                              createRole.isPending || updateRole.isPending
                            }
                            className="shadow-glow-sm"
                          >
                            <Check className="w-4 h-4 mr-2" />
                            {createRole.isPending || updateRole.isPending
                              ? "Saving..."
                              : "Save"}
                          </Button>
                        </>
                      ) : (
                        <>
                          {!selectedRole?.isSystem && (
                            <>
                              <Button
                                variant="outline"
                                onClick={handleStartEdit}
                              >
                                <Edit2 className="w-4 h-4 mr-2" />
                                Edit
                              </Button>
                              <Button
                                variant="destructive"
                                onClick={handleDelete}
                                disabled={deleteRole.isPending}
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Delete
                              </Button>
                            </>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Permissions List */}
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-text-primary mb-4">
                    Permissions
                  </h3>
                  {permissionsLoading || roleLoading ? (
                    <div className="text-center text-text-muted py-8">
                      Loading permissions...
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {Object.entries(permissionsByResource).map(
                        ([resource, permissions]) => (
                          <div key={resource}>
                            <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
                              {resource}
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                              {permissions.map((permission) => {
                                const isSelected = currentPermissions.includes(
                                  permission.id
                                );
                                const canToggle =
                                  isFormMode && !selectedRole?.isSystem;

                                return (
                                  <button
                                    key={permission.id}
                                    onClick={() =>
                                      canToggle &&
                                      handleTogglePermission(permission.id)
                                    }
                                    disabled={!canToggle}
                                    className={cn(
                                      "flex items-center gap-3 p-3 rounded-lg border text-left transition-all",
                                      isSelected
                                        ? "border-accent bg-accent-subtle"
                                        : "border-border bg-surface-overlay",
                                      canToggle
                                        ? "hover:border-accent cursor-pointer"
                                        : "cursor-default opacity-75"
                                    )}
                                  >
                                    <div
                                      className={cn(
                                        "w-5 h-5 rounded flex items-center justify-center flex-shrink-0",
                                        isSelected
                                          ? "bg-accent text-text-inverse"
                                          : "bg-surface border border-border"
                                      )}
                                    >
                                      {isSelected && (
                                        <Check className="w-3 h-3" />
                                      )}
                                    </div>
                                    <div className="min-w-0">
                                      <p className="text-sm font-medium text-text-primary">
                                        {permission.action}
                                      </p>
                                      <p className="text-xs text-text-muted truncate">
                                        {permission.description}
                                      </p>
                                    </div>
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
