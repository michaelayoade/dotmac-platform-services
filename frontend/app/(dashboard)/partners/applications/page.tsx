"use client";

import { useState } from "react";
import Link from "next/link";
import {
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Building2,
  Mail,
  Phone,
  Globe,
  X,
} from "lucide-react";
import { Button, Modal, Input } from "@/lib/dotmac/core";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";

interface PartnerApplication {
  id: string;
  companyName: string;
  contactName: string;
  contactEmail: string;
  phone: string | null;
  website: string | null;
  businessDescription: string | null;
  expectedReferralsMonthly: number | null;
  status: "pending" | "approved" | "rejected";
  reviewedBy: string | null;
  reviewedAt: string | null;
  rejectionReason: string | null;
  partnerId: string | null;
  createdAt: string;
  updatedAt: string;
}

interface ApplicationsResponse {
  applications: PartnerApplication[];
  total: number;
  page: number;
  pageSize: number;
}

export default function PartnerApplicationsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [selectedApplication, setSelectedApplication] = useState<PartnerApplication | null>(
    null
  );
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["partner-applications", statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      const url = `/api/v1/partners/applications${params.toString() ? `?${params}` : ""}`;
      return api.get<ApplicationsResponse>(url);
    },
  });

  const approveMutation = useMutation({
    mutationFn: async (applicationId: string) => {
      return api.post(`/api/v1/partners/applications/${applicationId}/approve`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-applications"] });
      setIsViewModalOpen(false);
      setSelectedApplication(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({ applicationId, reason }: { applicationId: string; reason: string }) => {
      return api.post(`/api/v1/partners/applications/${applicationId}/reject`, {
        rejection_reason: reason,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-applications"] });
      setIsRejectModalOpen(false);
      setSelectedApplication(null);
      setRejectionReason("");
    },
  });

  const applications = data?.applications ?? [];
  const pendingCount = applications.filter((a) => a.status === "pending").length;
  const approvedCount = applications.filter((a) => a.status === "approved").length;
  const rejectedCount = applications.filter((a) => a.status === "rejected").length;

  const handleApprove = (application: PartnerApplication) => {
    if (confirm(`Are you sure you want to approve ${application.companyName}?`)) {
      approveMutation.mutate(application.id);
    }
  };

  const handleOpenRejectModal = (application: PartnerApplication) => {
    setSelectedApplication(application);
    setIsRejectModalOpen(true);
  };

  const handleReject = () => {
    if (!selectedApplication || !rejectionReason.trim()) return;
    rejectMutation.mutate({
      applicationId: selectedApplication.id,
      reason: rejectionReason,
    });
  };

  const handleViewApplication = (application: PartnerApplication) => {
    setSelectedApplication(application);
    setIsViewModalOpen(true);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return (
          <span className="badge badge-warning flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Pending
          </span>
        );
      case "approved":
        return (
          <span className="badge badge-success flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Approved
          </span>
        );
      case "rejected":
        return (
          <span className="badge badge-error flex items-center gap-1">
            <XCircle className="w-3 h-3" />
            Rejected
          </span>
        );
      default:
        return <span className="badge badge-default">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/" className="hover:text-text-secondary">
          Dashboard
        </Link>
        <span aria-hidden="true">/</span>
        <Link href="/partners" className="hover:text-text-secondary">
          Partners
        </Link>
        <span aria-hidden="true">/</span>
        <span className="text-text-primary">Applications</span>
      </nav>

      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Partner Applications</h1>
          <p className="page-description">Review and manage partner program applications</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="quick-stats">
        <div
          className={`quick-stat cursor-pointer ${statusFilter === "" ? "ring-2 ring-brand-primary" : ""}`}
          onClick={() => setStatusFilter("")}
        >
          <p className="metric-label">All Applications</p>
          <p className="metric-value text-2xl">{applications.length}</p>
        </div>
        <div
          className={`quick-stat cursor-pointer ${statusFilter === "pending" ? "ring-2 ring-brand-primary" : ""}`}
          onClick={() => setStatusFilter("pending")}
        >
          <p className="metric-label">Pending</p>
          <p className="metric-value text-2xl text-status-warning">{pendingCount}</p>
        </div>
        <div
          className={`quick-stat cursor-pointer ${statusFilter === "approved" ? "ring-2 ring-brand-primary" : ""}`}
          onClick={() => setStatusFilter("approved")}
        >
          <p className="metric-label">Approved</p>
          <p className="metric-value text-2xl text-status-success">{approvedCount}</p>
        </div>
        <div
          className={`quick-stat cursor-pointer ${statusFilter === "rejected" ? "ring-2 ring-brand-primary" : ""}`}
          onClick={() => setStatusFilter("rejected")}
        >
          <p className="metric-label">Rejected</p>
          <p className="metric-value text-2xl text-status-error">{rejectedCount}</p>
        </div>
      </div>

      {/* Applications Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="divide-y divide-border-subtle">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="px-4 py-4 flex items-center gap-4">
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-48 skeleton" />
                  <div className="h-3 w-32 skeleton" />
                </div>
                <div className="h-6 w-20 skeleton rounded-full" />
                <div className="h-4 w-24 skeleton" />
              </div>
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" aria-label="Partner applications"><caption className="sr-only">Partner applications</caption>
              <thead className="bg-surface-raised border-b border-border">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                    Company
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
                    Submitted
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {applications.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-12 text-center text-text-muted">
                      No applications found
                    </td>
                  </tr>
                ) : (
                  applications.map((app) => (
                    <tr key={app.id} className="hover:bg-surface-raised/50">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-brand-primary/10 flex items-center justify-center text-brand-primary font-medium">
                            <Building2 className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="font-medium text-text-primary">
                              {app.companyName}
                            </div>
                            {app.website && (
                              <div className="text-sm text-text-muted">
                                {app.website}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-text-primary">{app.contactName}</div>
                        <div className="text-sm text-text-muted">{app.contactEmail}</div>
                      </td>
                      <td className="px-4 py-4">{getStatusBadge(app.status)}</td>
                      <td className="px-4 py-4 text-text-secondary text-sm">
                        {new Date(app.createdAt).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewApplication(app)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          {app.status === "pending" && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-status-success border-status-success hover:bg-status-success/10"
                                onClick={() => handleApprove(app)}
                                disabled={approveMutation.isPending}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Approve
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-status-error border-status-error hover:bg-status-error/10"
                                onClick={() => handleOpenRejectModal(app)}
                              >
                                <XCircle className="w-4 h-4 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* View Application Modal */}
      <Modal
        open={isViewModalOpen}
        onOpenChange={(open) => {
          setIsViewModalOpen(open);
          if (!open) {
            setSelectedApplication(null);
          }
        }}
        title="Application Details"
      >
        {selectedApplication && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-text-primary">
                {selectedApplication.companyName}
              </h3>
              {getStatusBadge(selectedApplication.status)}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-text-muted">Contact Name</p>
                <p className="text-text-primary">{selectedApplication.contactName}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted">Email</p>
                <p className="text-text-primary">{selectedApplication.contactEmail}</p>
              </div>
              {selectedApplication.phone && (
                <div>
                  <p className="text-sm text-text-muted">Phone</p>
                  <p className="text-text-primary">{selectedApplication.phone}</p>
                </div>
              )}
              {selectedApplication.website && (
                <div>
                  <p className="text-sm text-text-muted">Website</p>
                  <a
                    href={selectedApplication.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-primary hover:underline"
                  >
                    {selectedApplication.website}
                  </a>
                </div>
              )}
              {selectedApplication.expectedReferralsMonthly && (
                <div>
                  <p className="text-sm text-text-muted">Expected Monthly Referrals</p>
                  <p className="text-text-primary">
                    {selectedApplication.expectedReferralsMonthly}
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm text-text-muted">Submitted</p>
                <p className="text-text-primary">
                  {new Date(selectedApplication.createdAt).toLocaleString()}
                </p>
              </div>
            </div>

            {selectedApplication.businessDescription && (
              <div>
                <p className="text-sm text-text-muted mb-1">Business Description</p>
                <p className="text-text-secondary text-sm bg-surface-raised p-3 rounded-md">
                  {selectedApplication.businessDescription}
                </p>
              </div>
            )}

            {selectedApplication.status === "rejected" &&
              selectedApplication.rejectionReason && (
                <div>
                  <p className="text-sm text-status-error mb-1">Rejection Reason</p>
                  <p className="text-text-secondary text-sm bg-status-error/10 p-3 rounded-md">
                    {selectedApplication.rejectionReason}
                  </p>
                </div>
              )}

            {selectedApplication.status === "pending" && (
              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <Button
                  variant="outline"
                  className="text-status-error border-status-error hover:bg-status-error/10"
                  onClick={() => {
                    setIsViewModalOpen(false);
                    handleOpenRejectModal(selectedApplication);
                  }}
                >
                  <XCircle className="w-4 h-4 mr-1" />
                  Reject
                </Button>
                <Button
                  className="bg-status-success hover:bg-status-success/90"
                  onClick={() => handleApprove(selectedApplication)}
                  disabled={approveMutation.isPending}
                >
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Approve
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Reject Modal */}
      <Modal
        open={isRejectModalOpen}
        onOpenChange={(open) => {
          setIsRejectModalOpen(open);
          if (!open) {
            setSelectedApplication(null);
            setRejectionReason("");
          }
        }}
        title="Reject Application"
      >
        {selectedApplication && (
          <div className="space-y-4">
            <p className="text-text-secondary">
              Are you sure you want to reject the application from{" "}
              <span className="font-medium text-text-primary">
                {selectedApplication.companyName}
              </span>
              ?
            </p>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Rejection Reason *
              </label>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 bg-surface border border-border rounded-md text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-brand-primary/50"
                placeholder="Please provide a reason for rejection..."
                required
              />
            </div>
            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                variant="outline"
                onClick={() => {
                  setIsRejectModalOpen(false);
                  setSelectedApplication(null);
                  setRejectionReason("");
                }}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleReject}
                disabled={!rejectionReason.trim() || rejectMutation.isPending}
              >
                <XCircle className="w-4 h-4 mr-1" />
                {rejectMutation.isPending ? "Rejecting..." : "Reject Application"}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
