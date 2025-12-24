"use client";

import { use, type ElementType } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Download,
  Send,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  Receipt,
  DollarSign,
  Calendar,
  User,
  Mail,
  Building2,
  FileText,
  RefreshCcw,
  MoreHorizontal,
  Printer,
  Ban,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useInvoice,
  useMarkInvoicePaid,
  useSendInvoice,
  useVoidInvoice,
  useDownloadInvoicePdf,
} from "@/lib/hooks/api/use-billing";

interface InvoiceDetailPageProps {
  params: Promise<{ id: string }>;
}

const statusConfig: Record<
  string,
  { icon: ElementType; class: string; label: string; bg: string }
> = {
  paid: {
    icon: CheckCircle,
    class: "text-status-success",
    label: "Paid",
    bg: "bg-status-success/15",
  },
  pending: {
    icon: Clock,
    class: "text-status-warning",
    label: "Pending",
    bg: "bg-status-warning/15",
  },
  overdue: {
    icon: AlertCircle,
    class: "text-status-error",
    label: "Overdue",
    bg: "bg-status-error/15",
  },
  draft: {
    icon: Receipt,
    class: "text-text-muted",
    label: "Draft",
    bg: "bg-surface-overlay",
  },
  cancelled: {
    icon: XCircle,
    class: "text-text-muted",
    label: "Cancelled",
    bg: "bg-surface-overlay",
  },
};

export default function InvoiceDetailPage({ params }: InvoiceDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  // Data fetching
  const { data: invoice, isLoading, error, refetch } = useInvoice(id);

  // Mutations
  const markPaid = useMarkInvoicePaid();
  const sendInvoice = useSendInvoice();
  const voidInvoice = useVoidInvoice();
  const downloadPdf = useDownloadInvoicePdf();

  const handleMarkPaid = async () => {
    const confirmed = await confirm({
      title: "Mark as Paid",
      description: "Are you sure you want to mark this invoice as paid? This will update the customer's account balance.",
    });

    if (confirmed) {
      try {
        await markPaid.mutateAsync(id);
        toast({
          title: "Invoice marked as paid",
          description: "The invoice status has been updated.",
        });
      } catch {
        toast({
          title: "Error",
          description: "Failed to update invoice. Please try again.",
          variant: "error",
        });
      }
    }
  };

  const handleSendInvoice = async () => {
    const customerLabel = invoice?.customerId ? `customer ${invoice.customerId}` : "the customer";
    const confirmed = await confirm({
      title: "Send Invoice",
      description: `Send this invoice to ${customerLabel}? They will receive an email with payment instructions.`,
    });

    if (confirmed) {
      try {
        await sendInvoice.mutateAsync(id);
        toast({
          title: "Invoice sent",
          description: `Invoice sent to ${customerLabel}`,
        });
      } catch {
        toast({
          title: "Error",
          description: "Failed to send invoice. Please try again.",
          variant: "error",
        });
      }
    }
  };

  const handleVoidInvoice = async () => {
    const confirmed = await confirm({
      title: "Void Invoice",
      description: "Are you sure you want to void this invoice? This action cannot be undone.",
      variant: "danger",
    });

    if (confirmed) {
      try {
        await voidInvoice.mutateAsync(id);
        toast({
          title: "Invoice voided",
          description: "The invoice has been voided.",
        });
      } catch {
        toast({
          title: "Error",
          description: "Failed to void invoice. Please try again.",
          variant: "error",
        });
      }
    }
  };

  const handleDownloadPdf = async () => {
    try {
      const blob = await downloadPdf.mutateAsync(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `invoice-${invoice?.number || id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast({ title: "PDF downloaded" });
    } catch {
      toast({
        title: "Error",
        description: "Failed to download PDF. Please try again.",
        variant: "error",
      });
    }
  };

  // Loading state
  if (isLoading) {
    return <InvoiceDetailSkeleton />;
  }

  // Error state
  if (error || !invoice) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="text-status-error mb-4">
          <Receipt className="w-12 h-12" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">Invoice not found</h2>
        <p className="text-text-muted mb-6">
          The invoice you&apos;re looking for doesn&apos;t exist or you don&apos;t have access.
        </p>
        <Button onClick={() => router.push("/billing/invoices")}>Back to Invoices</Button>
      </div>
    );
  }

  const status = statusConfig[invoice.status] || statusConfig.draft;
  const StatusIcon = status.icon;
  const subtotal = invoice.items.reduce((sum, item) => sum + item.total, 0);
  const taxAmount = invoice.tax;
  const taxRate = subtotal > 0 ? taxAmount / subtotal : 0;
  const total = invoice.total;

  const canMarkPaid = invoice.status === "pending" || invoice.status === "overdue";
  const canSend = invoice.status === "draft" || invoice.status === "pending";
  const canVoid = invoice.status !== "paid" && invoice.status !== "cancelled";

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      {/* Page Header */}
      <PageHeader
        title={`Invoice ${invoice.number}`}
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Invoices", href: "/billing/invoices" },
          { label: invoice.number },
        ]}
        badge={
          <span
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium",
              status.bg,
              status.class
            )}
          >
            <StatusIcon className="w-4 h-4" />
            {status.label}
          </span>
        }
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCcw className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={handleDownloadPdf} disabled={downloadPdf.isPending}>
              <Download className="w-4 h-4 mr-2" />
              {downloadPdf.isPending ? "Downloading..." : "Download PDF"}
            </Button>
            {canSend && (
              <Button variant="outline" onClick={handleSendInvoice} disabled={sendInvoice.isPending}>
                <Send className="w-4 h-4 mr-2" />
                {sendInvoice.isPending ? "Sending..." : "Send Invoice"}
              </Button>
            )}
            {canMarkPaid && (
              <Button onClick={handleMarkPaid} disabled={markPaid.isPending} className="shadow-glow-sm hover:shadow-glow">
                <CheckCircle className="w-4 h-4 mr-2" />
                {markPaid.isPending ? "Processing..." : "Mark as Paid"}
              </Button>
            )}
          </div>
        }
      />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Invoice Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Invoice Header Card */}
          <Card className="p-6">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-4">Customer Details</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                      <User className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <p className="text-xs text-text-muted">Customer</p>
                      {invoice.customerId ? (
                        <Link
                          href={`/customers/${invoice.customerId}`}
                          className="text-sm text-accent hover:text-accent-hover"
                        >
                          Customer {invoice.customerId}
                        </Link>
                      ) : (
                        <p className="text-sm text-text-muted">Unknown customer</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                      <Mail className="w-5 h-5 text-status-info" />
                    </div>
                    <div>
                      <p className="text-xs text-text-muted">Email</p>
                      <p className="text-sm text-text-muted">Not available</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-left md:text-right">
                <h3 className="text-lg font-semibold text-text-primary mb-4">Invoice Details</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between md:justify-end gap-4">
                    <span className="text-sm text-text-muted">Invoice Number:</span>
                    <span className="text-sm font-mono font-medium text-text-primary">{invoice.number}</span>
                  </div>
                  <div className="flex items-center justify-between md:justify-end gap-4">
                    <span className="text-sm text-text-muted">Issue Date:</span>
                    <span className="text-sm text-text-primary">
                      {format(new Date(invoice.createdAt), "MMM d, yyyy")}
                    </span>
                  </div>
                  <div className="flex items-center justify-between md:justify-end gap-4">
                    <span className="text-sm text-text-muted">Due Date:</span>
                    <span
                      className={cn(
                        "text-sm",
                        invoice.status === "overdue" ? "text-status-error font-medium" : "text-text-primary"
                      )}
                    >
                      {format(new Date(invoice.dueDate), "MMM d, yyyy")}
                    </span>
                  </div>
                  {invoice.paidAt && (
                    <div className="flex items-center justify-between md:justify-end gap-4">
                      <span className="text-sm text-text-muted">Paid Date:</span>
                      <span className="text-sm text-status-success font-medium">
                        {format(new Date(invoice.paidAt), "MMM d, yyyy")}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Card>

          {/* Line Items */}
          <Card className="overflow-hidden">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Line Items</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="w-1/2">Description</th>
                    <th className="text-right">Qty</th>
                    <th className="text-right">Unit Price</th>
                    <th className="text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.items.map((item) => (
                    <tr key={item.id}>
                      <td className="text-text-primary">{item.description}</td>
                      <td className="text-right tabular-nums">{item.quantity}</td>
                      <td className="text-right tabular-nums">
                        ${(item.unitPrice / 100).toFixed(2)}
                      </td>
                      <td className="text-right font-medium tabular-nums">
                        ${(item.total / 100).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Totals */}
            <div className="p-6 bg-surface-overlay/50 border-t border-border">
              <div className="max-w-xs ml-auto space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Subtotal</span>
                  <span className="text-text-primary tabular-nums">
                    ${(subtotal / 100).toFixed(2)}
                  </span>
                </div>
                {taxAmount > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-text-muted">Tax ({(taxRate * 100).toFixed(0)}%)</span>
                    <span className="text-text-primary tabular-nums">
                      ${(taxAmount / 100).toFixed(2)}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-semibold pt-2 border-t border-border">
                  <span className="text-text-primary">Total</span>
                  <span className="text-text-primary tabular-nums">
                    ${(total / 100).toFixed(2)} {invoice.currency}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column - Summary & Actions */}
        <div className="space-y-6">
          {/* Payment Summary */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Payment Summary</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Amount Due</p>
                  <p className="text-lg font-semibold text-text-primary">
                    ${(invoice.total / 100).toLocaleString()} {invoice.currency}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", status.bg)}>
                  <StatusIcon className={cn("w-5 h-5", status.class)} />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Status</p>
                  <p className={cn("text-sm font-medium", status.class)}>{status.label}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-text-muted" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Due Date</p>
                  <p
                    className={cn(
                      "text-sm font-medium",
                      invoice.status === "overdue" ? "text-status-error" : "text-text-primary"
                    )}
                  >
                    {format(new Date(invoice.dueDate), "MMMM d, yyyy")}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={handleDownloadPdf}
                disabled={downloadPdf.isPending}
              >
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Printer className="w-4 h-4 mr-2" />
                Print Invoice
              </Button>
              {canSend && (
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={handleSendInvoice}
                  disabled={sendInvoice.isPending}
                >
                  <Send className="w-4 h-4 mr-2" />
                  Send to Customer
                </Button>
              )}
              {canVoid && (
                <Button
                  variant="outline"
                  className="w-full justify-start text-status-error hover:text-status-error"
                  onClick={handleVoidInvoice}
                  disabled={voidInvoice.isPending}
                >
                  <Ban className="w-4 h-4 mr-2" />
                  Void Invoice
                </Button>
              )}
            </div>
          </Card>

          {/* Activity/History - Placeholder */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">History</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-accent mt-2" />
                <div>
                  <p className="text-sm text-text-primary">Invoice created</p>
                  <p className="text-xs text-text-muted">
                    {format(new Date(invoice.createdAt), "MMM d, yyyy 'at' h:mm a")}
                  </p>
                </div>
              </div>
              {invoice.paidAt && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-status-success mt-2" />
                  <div>
                    <p className="text-sm text-text-primary">Payment received</p>
                    <p className="text-xs text-text-muted">
                      {format(new Date(invoice.paidAt), "MMM d, yyyy 'at' h:mm a")}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Loading skeleton
function InvoiceDetailSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-48 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-64 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-32 bg-surface-overlay rounded" />
          <div className="h-10 w-32 bg-surface-overlay rounded" />
        </div>
      </div>

      {/* Content skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <div className="h-6 w-40 bg-surface-overlay rounded mb-4" />
            <div className="grid grid-cols-2 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-surface-overlay rounded-lg" />
                  <div>
                    <div className="h-3 w-16 bg-surface-overlay rounded mb-1" />
                    <div className="h-4 w-32 bg-surface-overlay rounded" />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="card p-6">
            <div className="h-6 w-32 bg-surface-overlay rounded mb-4" />
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-surface-overlay rounded" />
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <div className="h-6 w-32 bg-surface-overlay rounded mb-4" />
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-surface-overlay rounded-lg" />
                  <div>
                    <div className="h-3 w-20 bg-surface-overlay rounded mb-1" />
                    <div className="h-5 w-24 bg-surface-overlay rounded" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
