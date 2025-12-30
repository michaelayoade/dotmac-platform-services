"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Receipt,
  Download,
  Mail,
  Eye,
  Search,
  Calendar,
  CheckCircle,
  Clock,
  XCircle,
  RefreshCw,
  CreditCard,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import {
  useReceipts,
  useDownloadReceiptPdf,
  useEmailReceipt,
  type ListReceiptsParams,
} from "@/lib/hooks/api/use-billing";
import type { Receipt as ReceiptType, ReceiptStatus } from "@/types/models";

export default function ReceiptsPage() {
  const { toast } = useToast();
  const [params, setParams] = useState<ListReceiptsParams>({});
  const { data, isLoading } = useReceipts(params);
  const downloadPdf = useDownloadReceiptPdf();
  const emailReceipt = useEmailReceipt();

  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [emailingId, setEmailingId] = useState<string | null>(null);

  const receipts = data?.items || [];

  const statusConfig: Record<ReceiptStatus, { icon: React.ElementType; class: string; label: string }> = {
    completed: { icon: CheckCircle, class: "status-badge--success", label: "Completed" },
    pending: { icon: Clock, class: "status-badge--warning", label: "Pending" },
    failed: { icon: XCircle, class: "status-badge--error", label: "Failed" },
    refunded: { icon: RefreshCw, class: "status-badge--info", label: "Refunded" },
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount / 100);
  };

  const handleDownload = async (receipt: ReceiptType) => {
    setDownloadingId(receipt.id);
    try {
      const blob = await downloadPdf.mutateAsync(receipt.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `receipt-${receipt.number}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast({
        title: "Download started",
        description: `Receipt ${receipt.number} is being downloaded.`,
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to download receipt.",
        variant: "error",
      });
    } finally {
      setDownloadingId(null);
    }
  };

  const handleEmail = async (receipt: ReceiptType) => {
    setEmailingId(receipt.id);
    try {
      await emailReceipt.mutateAsync({ id: receipt.id });
      toast({
        title: "Receipt sent",
        description: `Receipt ${receipt.number} has been emailed to the tenant.`,
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to email receipt.",
        variant: "error",
      });
    } finally {
      setEmailingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header with Breadcrumbs */}
      <div>
        <div className="flex items-center gap-2 text-sm text-text-muted mb-4">
          <Link href="/billing" className="hover:text-text-secondary">
            Billing
          </Link>
          <span>/</span>
          <span className="text-text-primary">Receipts</span>
        </div>

        <div className="page-header">
          <div>
            <h1 className="page-title">Receipts</h1>
            <p className="page-description">
              View and download payment receipts
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search receipts..."
              className="w-full pl-10 pr-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-text-muted">Status:</span>
            {[
              { value: undefined, label: "All" },
              { value: "completed" as ReceiptStatus, label: "Completed" },
              { value: "pending" as ReceiptStatus, label: "Pending" },
              { value: "refunded" as ReceiptStatus, label: "Refunded" },
            ].map((option) => (
              <Button
                key={option.label}
                variant={params.status === option.value ? "default" : "outline"}
                size="sm"
                onClick={() => setParams((p) => ({ ...p, status: option.value }))}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Receipts Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-text-muted">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading receipts...
          </div>
        ) : receipts.length === 0 ? (
          <div className="p-12 text-center">
            <Receipt className="w-12 h-12 mx-auto text-text-muted mb-4" />
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              No receipts found
            </h3>
            <p className="text-text-muted">
              {params.status
                ? `No ${params.status} receipts`
                : "No receipts to display"}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table" aria-label="Receipts list"><caption className="sr-only">Receipts list</caption>
              <thead>
                <tr>
                  <th>Receipt #</th>
                  <th>Tenant</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Payment Method</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {receipts.map((receipt: ReceiptType) => {
                  const config = statusConfig[receipt.status];
                  const StatusIcon = config.icon;
                  const isDownloading = downloadingId === receipt.id;
                  const isEmailing = emailingId === receipt.id;

                  return (
                    <tr key={receipt.id} className="group">
                      <td>
                        <Link
                          href={`/billing/receipts/${receipt.id}`}
                          className="font-mono text-sm text-accent hover:underline"
                        >
                          {receipt.number}
                        </Link>
                      </td>
                      <td>
                        <p className="text-sm font-medium text-text-primary">
                          {receipt.customer?.name || "Unknown"}
                        </p>
                        <p className="text-xs text-text-muted">
                          {receipt.customer?.email || "—"}
                        </p>
                      </td>
                      <td>
                        <div className="flex items-center gap-1 text-sm text-text-secondary">
                          <Calendar className="w-3 h-3" />
                          {formatDate(receipt.paymentDate)}
                        </div>
                      </td>
                      <td>
                        <span className="text-sm font-semibold tabular-nums text-text-primary">
                          {formatCurrency(receipt.total)}
                        </span>
                      </td>
                      <td>
                        <span className={cn("status-badge", config.class)}>
                          <StatusIcon className="w-3 h-3" />
                          {config.label}
                        </span>
                      </td>
                      <td>
                        {receipt.paymentMethod ? (
                          <div className="flex items-center gap-2 text-sm text-text-muted">
                            <CreditCard className="w-3 h-3" />
                            •••• {receipt.paymentMethod.last4}
                          </div>
                        ) : (
                          <span className="text-sm text-text-muted">—</span>
                        )}
                      </td>
                      <td>
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Link href={`/billing/receipts/${receipt.id}`}>
                            <Button variant="outline" size="sm" title="View">
                              <Eye className="w-3 h-3" />
                            </Button>
                          </Link>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownload(receipt)}
                            disabled={isDownloading}
                            title="Download PDF"
                          >
                            {isDownloading ? (
                              <RefreshCw className="w-3 h-3 animate-spin" />
                            ) : (
                              <Download className="w-3 h-3" />
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEmail(receipt)}
                            disabled={isEmailing}
                            title="Email Receipt"
                          >
                            {isEmailing ? (
                              <RefreshCw className="w-3 h-3 animate-spin" />
                            ) : (
                              <Mail className="w-3 h-3" />
                            )}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
