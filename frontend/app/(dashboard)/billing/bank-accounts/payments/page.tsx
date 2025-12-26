"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Plus,
  CreditCard,
  DollarSign,
  FileText,
  Calendar,
  User,
  Check,
  Banknote,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useManualPayments,
  useRecordManualPayment,
  useBankAccounts,
  type ManualPayment,
  type RecordManualPaymentData,
} from "@/lib/hooks/api/use-billing";

const methodConfig = {
  cash: { label: "Cash", icon: Banknote, class: "bg-status-success/15 text-status-success" },
  check: { label: "Check", icon: FileText, class: "bg-accent-subtle text-accent" },
  bank_transfer: { label: "Bank Transfer", icon: CreditCard, class: "bg-status-info/15 text-status-info" },
  other: { label: "Other", icon: DollarSign, class: "bg-surface-overlay text-text-muted" },
};

export default function ManualPaymentsPage() {
  const { toast } = useToast();
  const [page, setPage] = useState(1);
  const [methodFilter, setMethodFilter] = useState<ManualPayment["method"] | "">("");
  const [showNewForm, setShowNewForm] = useState(false);

  const { data: payments, isLoading } = useManualPayments({
    page,
    pageSize: 20,
    method: methodFilter || undefined,
  });
  const { data: bankAccounts } = useBankAccounts();
  const recordPayment = useRecordManualPayment();

  const [newPayment, setNewPayment] = useState<RecordManualPaymentData>({
    invoiceId: "",
    amount: 0,
    method: "cash",
    receivedAt: new Date().toISOString().split("T")[0],
  });

  const handleRecord = async () => {
    if (!newPayment.invoiceId || newPayment.amount <= 0) {
      toast({
        title: "Validation Error",
        description: "Please enter invoice ID and amount.",
        variant: "error",
      });
      return;
    }

    try {
      await recordPayment.mutateAsync({
        ...newPayment,
        amount: Math.round(newPayment.amount * 100), // Convert to cents
      });
      toast({
        title: "Payment recorded",
        description: "Manual payment has been recorded successfully.",
      });
      setShowNewForm(false);
      setNewPayment({
        invoiceId: "",
        amount: 0,
        method: "cash",
        receivedAt: new Date().toISOString().split("T")[0],
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to record payment.",
        variant: "error",
      });
    }
  };

  const totalRecorded = payments?.items.reduce((sum, p) => sum + p.amount, 0) ?? 0;

  if (isLoading) {
    return <ManualPaymentsSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Manual Payments"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Bank Accounts", href: "/billing/bank-accounts" },
          { label: "Manual Payments" },
        ]}
        actions={
          <div className="flex gap-3">
            <Link href="/billing/bank-accounts">
              <Button variant="ghost">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
            </Link>
            <Button
              onClick={() => setShowNewForm(true)}
              className="shadow-glow-sm hover:shadow-glow"
            >
              <Plus className="w-4 h-4 mr-2" />
              Record Payment
            </Button>
          </div>
        }
      />

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <DollarSign className="w-5 h-5 text-status-success" />
            <div>
              <p className="text-sm text-text-muted">Total Recorded</p>
              <p className="text-xl font-bold text-text-primary">
                ${(totalRecorded / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-accent" />
            <div>
              <p className="text-sm text-text-muted">Total Payments</p>
              <p className="text-xl font-bold text-text-primary">{payments?.total ?? 0}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-status-info" />
            <div>
              <p className="text-sm text-text-muted">This Month</p>
              <p className="text-xl font-bold text-text-primary">
                {payments?.items.filter((p) => {
                  const paymentDate = new Date(p.receivedAt);
                  const now = new Date();
                  return (
                    paymentDate.getMonth() === now.getMonth() &&
                    paymentDate.getFullYear() === now.getFullYear()
                  );
                }).length ?? 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* New Payment Form */}
      {showNewForm && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-6">Record Manual Payment</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Invoice ID <span className="text-status-error">*</span>
              </label>
              <Input
                value={newPayment.invoiceId}
                onChange={(e) => setNewPayment({ ...newPayment, invoiceId: e.target.value })}
                placeholder="Enter invoice ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Amount <span className="text-status-error">*</span>
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <Input
                  type="number"
                  min={0}
                  step={0.01}
                  value={newPayment.amount || ""}
                  onChange={(e) =>
                    setNewPayment({ ...newPayment, amount: parseFloat(e.target.value) || 0 })
                  }
                  className="pl-10"
                  placeholder="0.00"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Payment Method
              </label>
              <Select
                value={newPayment.method}
                onChange={(e) =>
                  setNewPayment({ ...newPayment, method: e.target.value as ManualPayment["method"] })
                }
              >
                <option value="cash">Cash</option>
                <option value="check">Check</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="other">Other</option>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Date Received
              </label>
              <Input
                type="date"
                value={newPayment.receivedAt}
                onChange={(e) => setNewPayment({ ...newPayment, receivedAt: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Reference
              </label>
              <Input
                value={newPayment.reference || ""}
                onChange={(e) => setNewPayment({ ...newPayment, reference: e.target.value })}
                placeholder="Check number, transaction ID, etc."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Deposit to Account
              </label>
              <Select
                value={newPayment.bankAccountId || ""}
                onChange={(e) =>
                  setNewPayment({ ...newPayment, bankAccountId: e.target.value || undefined })
                }
              >
                <option value="">Select account (optional)</option>
                {bankAccounts?.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name} - {account.bankName}
                  </option>
                ))}
              </Select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Notes
              </label>
              <Input
                value={newPayment.notes || ""}
                onChange={(e) => setNewPayment({ ...newPayment, notes: e.target.value })}
                placeholder="Additional notes..."
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border">
            <Button variant="ghost" onClick={() => setShowNewForm(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleRecord}
              disabled={recordPayment.isPending}
              className="shadow-glow-sm hover:shadow-glow"
            >
              {recordPayment.isPending ? "Recording..." : "Record Payment"}
            </Button>
          </div>
        </Card>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="flex gap-4">
          <Select
            value={methodFilter}
            onChange={(e) => {
              setMethodFilter(e.target.value as ManualPayment["method"] | "");
              setPage(1);
            }}
            className="w-48"
          >
            <option value="">All Methods</option>
            <option value="cash">Cash</option>
            <option value="check">Check</option>
            <option value="bank_transfer">Bank Transfer</option>
            <option value="other">Other</option>
          </Select>
        </div>
      </Card>

      {/* Payments List */}
      {payments && payments.items.length > 0 ? (
        <div className="space-y-4">
          {payments.items.map((payment) => {
            const config = methodConfig[payment.method];
            const MethodIcon = config.icon;

            return (
              <Card key={payment.id} className="p-6">
                <div className="flex items-center gap-4">
                  <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center", config.class)}>
                    <MethodIcon className="w-6 h-6" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Link
                        href={`/billing/invoices/${payment.invoiceId}`}
                        className="font-semibold text-text-primary hover:text-accent"
                      >
                        Invoice {payment.invoiceNumber}
                      </Link>
                      <span className={cn("px-2 py-0.5 rounded text-xs", config.class)}>
                        {config.label}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-4 text-sm text-text-muted">
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {payment.customerName}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {new Date(payment.receivedAt).toLocaleDateString()}
                      </span>
                      {payment.reference && (
                        <span>Ref: {payment.reference}</span>
                      )}
                      <span>Recorded by: {payment.recordedBy}</span>
                    </div>
                    {payment.notes && (
                      <p className="text-sm text-text-muted mt-2">{payment.notes}</p>
                    )}
                  </div>

                  <div className="text-right">
                    <p className="text-xl font-bold text-status-success">
                      ${(payment.amount / 100).toFixed(2)}
                    </p>
                    <p className="text-sm text-text-muted">{payment.currency}</p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="p-12 text-center">
          <CreditCard className="w-12 h-12 mx-auto text-text-muted mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No manual payments</h3>
          <p className="text-text-muted mb-6">Record cash, check, or bank transfer payments here</p>
          <Button
            onClick={() => setShowNewForm(true)}
            className="shadow-glow-sm hover:shadow-glow"
          >
            <Plus className="w-4 h-4 mr-2" />
            Record First Payment
          </Button>
        </Card>
      )}

      {/* Pagination */}
      {payments && payments.totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-text-muted">
            Page {page} of {payments.totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page === payments.totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

function ManualPaymentsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-24 bg-surface-overlay rounded" />
          <div className="h-10 w-36 bg-surface-overlay rounded" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-4">
            <div className="h-12 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-6">
            <div className="h-20 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
