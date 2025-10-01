"use client";

import { useState } from "react";
import { usePartners, useDeletePartner, Partner } from "@/hooks/usePartners";
import PartnerMetrics from "@/components/partners/PartnerMetrics";
import PartnersList from "@/components/partners/PartnersList";
import CreatePartnerModal from "@/components/partners/CreatePartnerModal";

export default function PartnersPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);

  const { data, isLoading, error } = usePartners(statusFilter);
  const deletePartner = useDeletePartner();

  const handleEdit = (partner: Partner) => {
    setSelectedPartner(partner);
    setShowCreateModal(true);
  };

  const handleDelete = async (partnerId: string) => {
    if (confirm("Are you sure you want to delete this partner?")) {
      try {
        await deletePartner.mutateAsync(partnerId);
      } catch (error) {
        console.error("Failed to delete partner:", error);
        alert("Failed to delete partner");
      }
    }
  };

  const handleCloseModal = () => {
    setShowCreateModal(false);
    setSelectedPartner(null);
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-slate-400">Loading partners...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-red-400">Failed to load partners</div>
          <div className="text-sm text-slate-500 mt-2">{error.message}</div>
        </div>
      </div>
    );
  }

  const partners = data?.partners || [];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Partner Management</h1>
          <p className="text-slate-400 mt-1">
            Manage partner relationships and track performance
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          Create Partner
        </button>
      </div>

      <PartnerMetrics partners={partners} />

      <div className="mb-4 flex gap-4 items-center">
        <div className="flex-1">
          <label htmlFor="status-filter" className="block text-sm text-slate-400 mb-2">
            Filter by Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full md:w-64 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
            <option value="terminated">Terminated</option>
          </select>
        </div>

        <div className="text-sm text-slate-400">
          Showing {partners.length} partner{partners.length !== 1 ? "s" : ""}
        </div>
      </div>

      <PartnersList
        partners={partners}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {showCreateModal && (
        <CreatePartnerModal
          partner={selectedPartner}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}
