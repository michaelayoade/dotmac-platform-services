"use client";

import { use, type ElementType } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Download,
  CheckCircle,
  Clock,
  Receipt,
  DollarSign,
  Calendar,
  User,
  FileText,
  RefreshCcw,
  Ban,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useCreditNote,
  useIssueCreditNote,
  useVoidCreditNote,
  useDownloadCreditNotePdf,
  type CreditNoteStatus,
} from "@/lib/hooks/api/use-billing";

interface CreditNoteDetailPageProps {
  params: Promise<{ id: string }>;
}

const statusConfig: Record<
  CreditNoteStatus,
  { icon: ElementType; class: string; label: string; bg: string }
> = {
  draft: {
    icon: FileText,
    class: "text-text-muted",
    label: "Draft",
    bg: "bg-surface-overlay",
  },
  issued: {
    icon: Receipt,
    class: "text-status-info",
    label: "Issued",
    bg: "bg-status-info/15",
  },
  applied: {
    icon: CheckCircle,
    class: "text-status-success",
    label: "Applied",
    bg: "bg-status-success/15",
  },
  voided: {
    icon: Ban,
    class: "text-text-muted",
    label: "Voided",
    bg: "bg-surface-overlay",
  },
};

export default function CreditNoteDetailPage({ params }: CreditNoteDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();

  // Data fetching
  const { data: creditNote, isLoading, error, refetch } = useCreditNote(id);

  // Mutations
  const issueCreditNote = useIssueCreditNote();
  const voidCreditNote = useVoidCreditNote();
  const downloadPdf = useDownloadCreditNotePdf();

  const handleIssueCreditNote = async () => {
    const confirmed = await confirm({
      title: "Issue Credit Note",
      description: "Are you sure you want to issue this credit note? Once issued, it can be applied to invoices.",
    });

    if (confirmed) {
      try {
        await issueCreditNote.mutateAsync(id);
        toast({
          title: "Credit note issued",
          description: "The credit note has been issued and is now available for use.",
        });
      } catch {
        toast({
          title: "Error",
          description: "Failed to issue credit note. Please try again.",
          variant: "error",
        });
      }
    }
  };

  const handleVoidCreditNote = async () => {
    const confirmed = await confirm({
      title: "Void Credit Note",
      description: "Are you sure you want to void this credit note? This action cannot be undone.",
      variant: "danger",
    });

    if (confirmed) {
      try {
        await voidCreditNote.mutateAsync(id);
        toast({
          title: "Credit note voided",
          description: "The credit note has been voided.",
        });
      } catch {
        toast({
          title: "Error",
          description: "Failed to void credit note. Please try again.",
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
      a.download = `credit-note-${creditNote?.number || id}.pdf`;
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
    return <CreditNoteDetailSkeleton />;
  }

  // Error state
  if (error || !creditNote) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="text-status-error mb-4">
          <Receipt className="w-12 h-12" />
        </div>
        <h2 className="text-xl font-semibold text-text-primary mb-2">Credit note not found</h2>
        <p className="text-text-muted mb-6">
          The credit note you&apos;re looking for doesn&apos;t exist or you don&apos;t have access.
        </p>
        <Button onClick={() => router.push("/billing/credit-notes")}>Back to Credit Notes</Button>
      </div>
    );
  }

  const status = statusConfig[creditNote.status] || statusConfig.draft;
  const StatusIcon = status.icon;
  const total = creditNote.amount;

  const canIssue = creditNote.status === "draft";
  const canApply = creditNote.status === "issued" && creditNote.remainingAmount > 0;
  const canVoid = creditNote.status !== "applied" && creditNote.status !== "voided";

  return (
    <div className="space-y-8 animate-fade-up">
      {dialog}

      {/* Page Header */}
      <PageHeader
        title={`Credit Note ${creditNote.number}`}
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Credit Notes", href: "/billing/credit-notes" },
          { label: creditNote.number },
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
            {canApply && (
              <Link href={`/billing/credit-notes/${id}/apply`}>
                <Button variant="outline">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Apply to Invoice
                </Button>
              </Link>
            )}
            {canIssue && (
              <Button
                onClick={handleIssueCreditNote}
                disabled={issueCreditNote.isPending}
                className="shadow-glow-sm hover:shadow-glow"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                {issueCreditNote.isPending ? "Issuing..." : "Issue Credit Note"}
              </Button>
            )}
          </div>
        }
      />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Credit Note Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Credit Note Header Card */}
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
                      <p className="text-sm font-medium text-text-primary">
                        {creditNote.customerName}
                      </p>
                    </div>
                  </div>
                  {creditNote.invoiceNumber && (
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                        <Receipt className="w-5 h-5 text-status-info" />
                      </div>
                      <div>
                        <p className="text-xs text-text-muted">Related Invoice</p>
                        <Link
                          href={`/billing/invoices/${creditNote.invoiceId}`}
                          className="text-sm text-accent hover:text-accent-hover inline-flex items-center gap-1"
                        >
                          {creditNote.invoiceNumber}
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="text-left md:text-right">
                <h3 className="text-lg font-semibold text-text-primary mb-4">Credit Note Details</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between md:justify-end gap-4">
                    <span className="text-sm text-text-muted">Credit Note Number:</span>
                    <span className="text-sm font-mono font-medium text-text-primary">
                      {creditNote.number}
                    </span>
                  </div>
                  <div className="flex items-center justify-between md:justify-end gap-4">
                    <span className="text-sm text-text-muted">Created:</span>
                    <span className="text-sm text-text-primary">
                      {format(new Date(creditNote.createdAt), "MMM d, yyyy")}
                    </span>
                  </div>
                  {creditNote.issueDate && (
                    <div className="flex items-center justify-between md:justify-end gap-4">
                      <span className="text-sm text-text-muted">Issued:</span>
                      <span className="text-sm text-status-info font-medium">
                        {format(new Date(creditNote.issueDate), "MMM d, yyyy")}
                      </span>
                    </div>
                  )}
                  {creditNote.voidedDate && (
                    <div className="flex items-center justify-between md:justify-end gap-4">
                      <span className="text-sm text-text-muted">Voided:</span>
                      <span className="text-sm text-text-muted">
                        {format(new Date(creditNote.voidedDate), "MMM d, yyyy")}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Card>

          {/* Reason */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Reason</h3>
            <p className="text-text-secondary">{creditNote.reason}</p>
          </Card>

          {/* Line Items */}
          <Card className="overflow-hidden">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Credit Items</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table" aria-label="Credit note line items"><caption className="sr-only">Credit note line items</caption>
                <thead>
                  <tr>
                    <th className="w-1/2">Description</th>
                    <th className="text-right">Qty</th>
                    <th className="text-right">Unit Price</th>
                    <th className="text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {creditNote.lineItems.map((item) => (
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
                <div className="flex justify-between text-lg font-semibold pt-2 border-t border-border">
                  <span className="text-text-primary">Credit Total</span>
                  <span className="text-status-success tabular-nums">
                    -${(total / 100).toFixed(2)} {creditNote.currency}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column - Summary & Actions */}
        <div className="space-y-6">
          {/* Credit Summary */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Credit Summary</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Credit Amount</p>
                  <p className="text-lg font-semibold text-status-success">
                    -${(creditNote.amount / 100).toLocaleString()} {creditNote.currency}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Remaining Balance</p>
                  <p className={cn(
                    "text-lg font-semibold",
                    creditNote.remainingAmount > 0 ? "text-status-warning" : "text-text-muted"
                  )}>
                    ${(creditNote.remainingAmount / 100).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-status-info" />
                </div>
                <div>
                  <p className="text-xs text-text-muted">Applied Amount</p>
                  <p className="text-lg font-semibold text-text-primary">
                    ${(creditNote.appliedAmount / 100).toLocaleString()}
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
              {canApply && (
                <Link href={`/billing/credit-notes/${id}/apply`} className="block">
                  <Button variant="outline" className="w-full justify-start">
                    <ArrowRight className="w-4 h-4 mr-2" />
                    Apply to Invoice
                  </Button>
                </Link>
              )}
              {canIssue && (
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={handleIssueCreditNote}
                  disabled={issueCreditNote.isPending}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Issue Credit Note
                </Button>
              )}
              {canVoid && (
                <Button
                  variant="outline"
                  className="w-full justify-start text-status-error hover:text-status-error"
                  onClick={handleVoidCreditNote}
                  disabled={voidCreditNote.isPending}
                >
                  <Ban className="w-4 h-4 mr-2" />
                  Void Credit Note
                </Button>
              )}
            </div>
          </Card>

          {/* Activity/History */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">History</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-accent mt-2" />
                <div>
                  <p className="text-sm text-text-primary">Credit note created</p>
                  <p className="text-xs text-text-muted">
                    {format(new Date(creditNote.createdAt), "MMM d, yyyy 'at' h:mm a")}
                  </p>
                </div>
              </div>
              {creditNote.issueDate && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-status-info mt-2" />
                  <div>
                    <p className="text-sm text-text-primary">Credit note issued</p>
                    <p className="text-xs text-text-muted">
                      {format(new Date(creditNote.issueDate), "MMM d, yyyy 'at' h:mm a")}
                    </p>
                  </div>
                </div>
              )}
              {creditNote.appliedAmount > 0 && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-status-success mt-2" />
                  <div>
                    <p className="text-sm text-text-primary">
                      Applied ${(creditNote.appliedAmount / 100).toLocaleString()} to invoices
                    </p>
                    <p className="text-xs text-text-muted">
                      {format(new Date(creditNote.updatedAt), "MMM d, yyyy 'at' h:mm a")}
                    </p>
                  </div>
                </div>
              )}
              {creditNote.voidedDate && (
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-text-muted mt-2" />
                  <div>
                    <p className="text-sm text-text-primary">Credit note voided</p>
                    <p className="text-xs text-text-muted">
                      {format(new Date(creditNote.voidedDate), "MMM d, yyyy 'at' h:mm a")}
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
function CreditNoteDetailSkeleton() {
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
