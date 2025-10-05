"use client";

import { useState } from "react";
import { usePartners, useDeletePartner, Partner } from "@/hooks/usePartners";
import { Users, Plus } from "lucide-react";
import PartnerMetrics from "@/components/partners/PartnerMetrics";
import PartnersList from "@/components/partners/PartnersList";
import CreatePartnerModal from "@/components/partners/CreatePartnerModal";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { logger } from "@/lib/logger";

export default function PartnersPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [partnerToDelete, setPartnerToDelete] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const { data, isLoading, error } = usePartners(statusFilter);
  const deletePartner = useDeletePartner();

  const handleEdit = (partner: Partner) => {
    setSelectedPartner(partner);
    setShowCreateModal(true);
  };

  const handleDelete = (partnerId: string) => {
    setPartnerToDelete(partnerId);
    setShowDeleteDialog(true);
  };

  const confirmDelete = async () => {
    if (!partnerToDelete) return;

    setIsDeleting(true);
    try {
      await deletePartner.mutateAsync(partnerToDelete);
      logger.info("Partner deleted successfully", { partnerId: partnerToDelete });
      setShowDeleteDialog(false);
      setPartnerToDelete(null);
    } catch (error) {
      logger.error("Failed to delete partner", { partnerId: partnerToDelete, error });
      alert("Failed to delete partner");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCloseModal = () => {
    setShowCreateModal(false);
    setSelectedPartner(null);
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center py-12" role="status" aria-live="polite">
          <div className="text-muted-foreground">Loading partners...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <EmptyState.Error
          title="Failed to load partners"
          description={error.message}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  const partners = data?.partners || [];

  return (
    <div className="p-6">
      <PageHeader
        title="Partner Management"
        description="Manage partner relationships and track performance"
        icon={Users}
        actions={
          <Button onClick={() => setShowCreateModal(true)} aria-label="Create new partner">
            <Plus className="h-4 w-4 mr-2" />
            Create Partner
          </Button>
        }
      />

      <PartnerMetrics partners={partners} />

      <div className="mb-4 flex gap-4 items-center">
        <div className="flex-1">
          <label htmlFor="status-filter" className="block text-sm text-muted-foreground mb-2">
            Filter by Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full md:w-64 px-3 py-2 bg-accent border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            aria-label="Filter partners by status"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
            <option value="terminated">Terminated</option>
          </select>
        </div>

        <div className="text-sm text-muted-foreground" role="status" aria-live="polite">
          Showing {partners.length} partner{partners.length !== 1 ? "s" : ""}
        </div>
      </div>

      {partners.length === 0 ? (
        <EmptyState.List
          entityName="partners"
          onCreateClick={() => setShowCreateModal(true)}
          icon={Users}
        />
      ) : (
        <PartnersList
          partners={partners}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}

      {showCreateModal && (
        <CreatePartnerModal
          partner={selectedPartner}
          onClose={handleCloseModal}
        />
      )}

      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Delete Partner"
        description="Are you sure you want to delete this partner? This action cannot be undone and will remove all associated data."
        confirmText="Delete Partner"
        cancelText="Cancel"
        onConfirm={confirmDelete}
        variant="destructive"
        isLoading={isDeleting}
      />
    </div>
  );
}
