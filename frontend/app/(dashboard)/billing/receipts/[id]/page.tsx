"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Receipt,
  Download,
  Mail,
  Printer,
  CheckCircle,
  Clock,
  XCircle,
  RefreshCw,
  CreditCard,
  Building,
  Calendar,
  Hash,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import {
  useReceipt,
  useDownloadReceiptPdf,
  useEmailReceipt,
} from "@/lib/hooks/api/use-billing";
import type { ReceiptStatus } from "@/types/models";

export default function ReceiptDetailPage() {
  const params = useParams();
  const { toast } = useToast();
  const receiptId = params.id as string;

  const { data: receipt, isLoading } = useReceipt(receiptId);
  const downloadPdf = useDownloadReceiptPdf();
  const emailReceipt = useEmailReceipt();

  const [isDownloading, setIsDownloading] = useState(false);
  const [isEmailing, setIsEmailing] = useState(false);

  const statusConfig: Record<ReceiptStatus, { icon: React.ElementType; class: string; label: string }> = {
    completed: { icon: CheckCircle, class: "status-badge--success", label: "Completed" },
    pending: { icon: Clock, class: "status-badge--warning", label: "Pending" },
    failed: { icon: XCircle, class: "status-badge--error", label: "Failed" },
    refunded: { icon: RefreshCw, class: "status-badge--info", label: "Refunded" },
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount / 100);
  };

  const handleDownload = async () => {
    if (!receipt) return;
    setIsDownloading(true);
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
        description: "Your receipt is being downloaded.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to download receipt.",
        variant: "error",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const handleEmail = async () => {
    if (!receipt) return;
    setIsEmailing(true);
    try {
      await emailReceipt.mutateAsync({ id: receipt.id });
      toast({
        title: "Receipt sent",
        description: "The receipt has been emailed to the tenant.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to email receipt.",
        variant: "error",
      });
    } finally {
      setIsEmailing(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-text-muted" />
      </div>
    );
  }

  if (!receipt) {
    return (
      <div className="text-center py-12">
        <Receipt className="w-12 h-12 mx-auto text-text-muted mb-4" />
        <h2 className="text-lg font-semibold text-text-primary mb-2">
          Receipt not found
        </h2>
        <p className="text-text-muted mb-4">
          The receipt you&apos;re looking for doesn&apos;t exist.
        </p>
        <Link href="/billing/receipts">
          <Button variant="outline">Back to Receipts</Button>
        </Link>
      </div>
    );
  }

  const config = statusConfig[receipt.status];
  const StatusIcon = config.icon;

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-text-muted print:hidden">
        <Link href="/billing" className="hover:text-text-secondary">
          Billing
        </Link>
        <span>/</span>
        <Link href="/billing/receipts" className="hover:text-text-secondary">
          Receipts
        </Link>
        <span>/</span>
        <span className="text-text-primary">{receipt.number}</span>
      </div>

      {/* Page Header */}
      <div className="flex items-start justify-between print:hidden">
        <div className="flex items-center gap-4">
          <Link
            href="/billing/receipts"
            className="p-2 rounded-lg hover:bg-surface-hover transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-text-muted" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold text-text-primary">
                Receipt {receipt.number}
              </h1>
              <span className={cn("status-badge", config.class)}>
                <StatusIcon className="w-3 h-3" />
                {config.label}
              </span>
            </div>
            <p className="text-text-muted mt-1">
              {formatDate(receipt.paymentDate)} • {formatCurrency(receipt.total)}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="w-4 h-4 mr-2" />
            Print
          </Button>
          <Button
            variant="outline"
            onClick={handleEmail}
            disabled={isEmailing}
          >
            {isEmailing ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Mail className="w-4 h-4 mr-2" />
            )}
            Email
          </Button>
          <Button
            onClick={handleDownload}
            disabled={isDownloading}
            className="shadow-glow-sm"
          >
            {isDownloading ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-2" />
            )}
            Download PDF
          </Button>
        </div>
      </div>

      {/* Receipt Preview */}
      <div className="card p-8 print:shadow-none print:border-0">
        {/* Receipt Header */}
        <div className="flex justify-between items-start mb-8 pb-8 border-b border-border">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-lg bg-accent-subtle flex items-center justify-center">
                <Receipt className="w-6 h-6 text-accent" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-text-primary">
                  Payment Receipt
                </h2>
                <p className="text-sm text-text-muted">
                  Thank you for your payment
                </p>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 justify-end text-sm text-text-muted mb-1">
              <Hash className="w-3 h-3" />
              <span className="font-mono">{receipt.number}</span>
            </div>
            <div className="flex items-center gap-2 justify-end text-sm text-text-muted">
              <Calendar className="w-3 h-3" />
              {formatDate(receipt.paymentDate)}
            </div>
          </div>
        </div>

        {/* Tenant & Payment Info */}
        <div className="grid grid-cols-2 gap-8 mb-8">
          <div>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
              Tenant
            </h3>
            <div className="space-y-1">
              <p className="font-medium text-text-primary">
                {receipt.customer?.name || "Tenant"}
              </p>
              {receipt.customer?.email && (
                <p className="text-sm text-text-muted">
                  {receipt.customer.email}
                </p>
              )}
              {receipt.customer?.company && (
                <div className="flex items-center gap-1 text-sm text-text-muted">
                  <Building className="w-3 h-3" />
                  {receipt.customer.company}
                </div>
              )}
            </div>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
              Payment Method
            </h3>
            {receipt.paymentMethod ? (
              <div className="flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-text-muted" />
                <span className="text-text-primary">
                  {receipt.paymentMethod.brand} •••• {receipt.paymentMethod.last4}
                </span>
              </div>
            ) : (
              <p className="text-sm text-text-muted">Not available</p>
            )}
          </div>
        </div>

        {/* Payment Details */}
        <div className="mb-8">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
            Payment Details
          </h3>
          <div className="bg-surface-overlay rounded-lg overflow-hidden">
            <table className="data-table" aria-label="Receipt payment details"><caption className="sr-only">Receipt payment details</caption>
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left text-xs font-semibold text-text-muted uppercase tracking-wider px-4 py-3">
                    Description
                  </th>
                  <th className="text-right text-xs font-semibold text-text-muted uppercase tracking-wider px-4 py-3">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody>
                {receipt.invoice?.items?.map((item, idx) => (
                  <tr key={idx} className="border-b border-border last:border-0">
                    <td className="px-4 py-3">
                      <p className="text-sm text-text-primary">{item.description}</p>
                      {item.quantity > 1 && (
                        <p className="text-xs text-text-muted">
                          {item.quantity} × {formatCurrency(item.unitPrice)}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-medium tabular-nums text-text-primary">
                      {formatCurrency(item.total)}
                    </td>
                  </tr>
                )) || (
                  <tr className="border-b border-border">
                    <td className="px-4 py-3 text-sm text-text-primary">
                      {receipt.description || "Payment"}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-medium tabular-nums text-text-primary">
                      {formatCurrency(receipt.amount)}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Totals */}
        <div className="flex justify-end">
          <div className="w-64 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-text-muted">Subtotal</span>
              <span className="text-text-primary tabular-nums">
                {formatCurrency(receipt.amount)}
              </span>
            </div>
            {receipt.tax > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Tax</span>
                <span className="text-text-primary tabular-nums">
                  {formatCurrency(receipt.tax)}
                </span>
              </div>
            )}
            <div className="flex justify-between text-lg font-semibold pt-2 border-t border-border">
              <span className="text-text-primary">Total Paid</span>
              <span className="text-accent tabular-nums">
                {formatCurrency(receipt.total)}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-border text-center">
          <p className="text-sm text-text-muted">
            Questions about this receipt? Contact{" "}
            <a href="mailto:billing@dotmac.io" className="text-accent hover:underline">
              billing@dotmac.io
            </a>
          </p>
        </div>
      </div>

      {/* Related Invoice */}
      {receipt.invoiceId && (
        <div className="card p-4 print:hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Hash className="w-4 h-4 text-text-muted" />
              <div>
                <p className="text-sm font-medium text-text-primary">
                  Related Invoice
                </p>
                <p className="text-xs text-text-muted">
                  This receipt is for invoice {receipt.invoice?.number || receipt.invoiceId}
                </p>
              </div>
            </div>
            <Link href={`/billing/invoices/${receipt.invoiceId}`}>
              <Button variant="outline" size="sm">
                View Invoice
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
