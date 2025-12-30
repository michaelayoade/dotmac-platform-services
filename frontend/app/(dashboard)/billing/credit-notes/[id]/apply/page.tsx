"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Receipt,
  DollarSign,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useCreditNote,
  useCustomerOpenInvoices,
  useApplyCreditNote,
} from "@/lib/hooks/api/use-billing";

interface ApplyCreditNotePageProps {
  params: Promise<{ id: string }>;
}

export default function ApplyCreditNotePage({ params }: ApplyCreditNotePageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);
  const [applyAmount, setApplyAmount] = useState<string>("");

  // Fetch credit note
  const { data: creditNote, isLoading: creditNoteLoading } = useCreditNote(id);

  // Fetch open invoices for the customer
  const { data: openInvoices, isLoading: invoicesLoading } = useCustomerOpenInvoices(
    creditNote?.customerId || ""
  );

  const applyCreditNote = useApplyCreditNote();

  const selectedInvoice = openInvoices?.find((inv) => inv.id === selectedInvoiceId);
  const maxApplyAmount = Math.min(
    creditNote?.remainingAmount || 0,
    selectedInvoice?.amount || 0
  );
  const applyAmountCents = Math.round(parseFloat(applyAmount || "0") * 100);
  const isValidAmount = applyAmountCents > 0 && applyAmountCents <= maxApplyAmount;

  const handleApply = async () => {
    if (!selectedInvoiceId || !isValidAmount) return;

    try {
      await applyCreditNote.mutateAsync({
        id,
        data: {
          invoiceId: selectedInvoiceId,
          amount: applyAmountCents,
        },
      });

      toast({
        title: "Credit applied",
        description: `$${applyAmount} has been applied to the invoice.`,
      });

      router.push(`/billing/credit-notes/${id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to apply credit. Please try again.",
        variant: "error",
      });
    }
  };

  const isLoading = creditNoteLoading || invoicesLoading;

  if (isLoading) {
    return <ApplyPageSkeleton />;
  }

  if (!creditNote) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Receipt className="w-12 h-12 text-text-muted mb-4" />
        <h2 className="text-xl font-semibold text-text-primary mb-2">Credit note not found</h2>
        <Button onClick={() => router.push("/billing/credit-notes")}>Back to Credit Notes</Button>
      </div>
    );
  }

  if (creditNote.status !== "issued" || creditNote.remainingAmount === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <AlertCircle className="w-12 h-12 text-status-warning mb-4" />
        <h2 className="text-xl font-semibold text-text-primary mb-2">Cannot apply credit</h2>
        <p className="text-text-muted mb-6">
          {creditNote.status !== "issued"
            ? "This credit note must be issued before it can be applied."
            : "This credit note has no remaining balance."}
        </p>
        <Button onClick={() => router.push(`/billing/credit-notes/${id}`)}>
          Back to Credit Note
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Apply Credit Note"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Credit Notes", href: "/billing/credit-notes" },
          { label: creditNote.number, href: `/billing/credit-notes/${id}` },
          { label: "Apply" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      {/* Credit Note Summary */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
            <Receipt className="w-5 h-5 text-status-success" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Credit Note {creditNote.number}</h3>
            <p className="text-sm text-text-muted">
              Customer: {creditNote.customerName}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="p-4 bg-surface-overlay rounded-lg">
            <p className="text-xs text-text-muted mb-1">Total Credit</p>
            <p className="text-lg font-semibold text-text-primary">
              ${(creditNote.amount / 100).toLocaleString()}
            </p>
          </div>
          <div className="p-4 bg-surface-overlay rounded-lg">
            <p className="text-xs text-text-muted mb-1">Applied</p>
            <p className="text-lg font-semibold text-text-muted">
              ${(creditNote.appliedAmount / 100).toLocaleString()}
            </p>
          </div>
          <div className="p-4 bg-status-success/15 rounded-lg">
            <p className="text-xs text-text-muted mb-1">Available to Apply</p>
            <p className="text-lg font-semibold text-status-success">
              ${(creditNote.remainingAmount / 100).toLocaleString()}
            </p>
          </div>
        </div>
      </Card>

      {/* Select Invoice */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <DollarSign className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">Select Invoice</h3>
            <p className="text-sm text-text-muted">Choose an open invoice to apply credit to</p>
          </div>
        </div>

        {openInvoices && openInvoices.length > 0 ? (
          <div className="space-y-3">
            {openInvoices.map((invoice) => {
              const isSelected = selectedInvoiceId === invoice.id;
              return (
                <button
                  key={invoice.id}
                  type="button"
                  onClick={() => {
                    setSelectedInvoiceId(invoice.id);
                    // Auto-fill with max applicable amount
                    const max = Math.min(creditNote.remainingAmount, invoice.amount);
                    setApplyAmount((max / 100).toFixed(2));
                  }}
                  className={cn(
                    "w-full flex items-center justify-between p-4 rounded-lg border-2 transition-all text-left",
                    isSelected
                      ? "border-accent bg-accent-subtle/30"
                      : "border-border hover:border-accent/50 bg-surface-overlay"
                  )}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={cn(
                        "w-6 h-6 rounded-full border-2 flex items-center justify-center",
                        isSelected
                          ? "border-accent bg-accent"
                          : "border-border bg-surface"
                      )}
                    >
                      {isSelected && <CheckCircle className="w-4 h-4 text-text-inverse" />}
                    </div>
                    <div>
                      <p className="font-mono text-sm font-medium text-text-primary">
                        {invoice.number}
                      </p>
                      <p className="text-xs text-text-muted">
                        Due: {format(new Date(invoice.dueDate), "MMM d, yyyy")}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-text-primary tabular-nums">
                      ${(invoice.amount / 100).toLocaleString()}
                    </p>
                    <p
                      className={cn(
                        "text-xs",
                        invoice.status === "overdue" ? "text-status-error" : "text-text-muted"
                      )}
                    >
                      {invoice.status === "overdue" ? "Overdue" : "Pending"}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <Receipt className="w-12 h-12 mx-auto text-text-muted mb-4" />
            <h3 className="text-lg font-semibold text-text-primary mb-2">No open invoices</h3>
            <p className="text-text-muted">
              This customer has no pending or overdue invoices to apply credit to.
            </p>
          </div>
        )}
      </Card>

      {/* Amount to Apply */}
      {selectedInvoice && (
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-highlight" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Amount to Apply</h3>
              <p className="text-sm text-text-muted">
                Maximum: ${(maxApplyAmount / 100).toFixed(2)}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Amount <span className="text-status-error">*</span>
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <Input
                  type="number"
                  min="0.01"
                  max={(maxApplyAmount / 100).toFixed(2)}
                  step="0.01"
                  value={applyAmount}
                  onChange={(e) => setApplyAmount(e.target.value)}
                  placeholder="0.00"
                  className={cn(
                    "pl-8",
                    !isValidAmount && applyAmount && "border-status-error"
                  )}
                />
              </div>
              {!isValidAmount && applyAmount && (
                <p className="text-xs text-status-error mt-1">
                  Amount must be between $0.01 and ${(maxApplyAmount / 100).toFixed(2)}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Quick Actions
              </label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setApplyAmount((maxApplyAmount / 100).toFixed(2))}
                >
                  Apply Max
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setApplyAmount((selectedInvoice.amount / 100).toFixed(2))}
                  disabled={selectedInvoice.amount > creditNote.remainingAmount}
                >
                  Full Invoice
                </Button>
              </div>
            </div>
          </div>

          {/* Summary */}
          {isValidAmount && (
            <div className="mt-6 p-4 bg-status-success/15 rounded-lg border border-status-success/20">
              <div className="flex items-center gap-2 text-status-success mb-2">
                <CheckCircle className="w-4 h-4" />
                <span className="font-medium">Application Preview</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-text-muted">Invoice balance after</p>
                  <p className="font-semibold text-text-primary">
                    ${((selectedInvoice.amount - applyAmountCents) / 100).toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-text-muted">Credit remaining after</p>
                  <p className="font-semibold text-text-primary">
                    ${((creditNote.remainingAmount - applyAmountCents) / 100).toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Actions */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            {selectedInvoice && isValidAmount && (
              <>
                <p className="text-sm text-text-muted">Apply to Invoice {selectedInvoice.number}</p>
                <p className="text-2xl font-semibold text-status-success">
                  -${applyAmount}
                </p>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Button type="button" variant="ghost" onClick={() => router.back()}>
              Cancel
            </Button>
            <Button
              onClick={handleApply}
              disabled={!selectedInvoiceId || !isValidAmount || applyCreditNote.isPending}
              className="shadow-glow-sm hover:shadow-glow"
            >
              {applyCreditNote.isPending ? "Applying..." : "Apply Credit"}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function ApplyPageSkeleton() {
  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-pulse">
      <div>
        <div className="h-4 w-48 bg-surface-overlay rounded mb-2" />
        <div className="h-8 w-64 bg-surface-overlay rounded" />
      </div>
      <div className="card p-6">
        <div className="h-6 w-48 bg-surface-overlay rounded mb-4" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-surface-overlay rounded-lg" />
          ))}
        </div>
      </div>
      <div className="card p-6">
        <div className="h-6 w-40 bg-surface-overlay rounded mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-surface-overlay rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
