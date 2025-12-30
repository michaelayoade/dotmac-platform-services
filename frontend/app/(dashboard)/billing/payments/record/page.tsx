"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Banknote, Calendar, FileText, User, Receipt } from "lucide-react";
import { Button, Input, Select } from "@/lib/dotmac/core";
import { useToast } from "@dotmac/core";

import { useRecordPayment } from "@/lib/hooks/api/use-payments";
import type { Payment, RecordPaymentRequest } from "@/lib/api/payments";

const paymentMethods: Array<{ value: Payment["method"]; label: string }> = [
  { value: "cash", label: "Cash" },
  { value: "check", label: "Check" },
  { value: "bank_transfer", label: "Bank Transfer" },
  { value: "wire_transfer", label: "Wire Transfer" },
];

export default function RecordPaymentPage() {
  const router = useRouter();
  const { toast } = useToast();
  const recordPayment = useRecordPayment();

  const [formData, setFormData] = useState<RecordPaymentRequest>({
    customerId: "",
    amount: 0,
    currency: "USD",
    method: "bank_transfer",
    referenceNumber: "",
    invoiceId: "",
    paymentDate: new Date().toISOString().split("T")[0],
    notes: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.customerId.trim()) {
      newErrors.customerId = "Customer is required";
    }

    if (!formData.amount || formData.amount <= 0) {
      newErrors.amount = "Amount must be greater than 0";
    }

    if (!formData.method) {
      newErrors.method = "Payment method is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await recordPayment.mutateAsync(formData);

      toast({
        title: "Payment recorded",
        description: "The offline payment has been recorded successfully.",
        variant: "success",
      });

      router.push("/billing/payments");
    } catch (error) {
      toast({
        title: "Failed to record payment",
        description: "An error occurred. Please try again.",
        variant: "error",
      });
    }
  };

  const handleChange = (field: keyof RecordPaymentRequest, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-text-muted">
        <Link href="/billing" className="hover:text-text-secondary">
          Billing
        </Link>
        <span>/</span>
        <Link href="/billing/payments" className="hover:text-text-secondary">
          Payments
        </Link>
        <span>/</span>
        <span className="text-text-primary">Record Payment</span>
      </div>

      {/* Header */}
      <div className="page-header">
        <div className="flex items-center gap-4">
          <Link href="/billing/payments">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <h1 className="page-title">Record Offline Payment</h1>
            <p className="text-text-muted">
              Record a cash, check, or bank transfer payment
            </p>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Payment Details */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-6 flex items-center gap-2">
              <Banknote className="w-5 h-5" />
              Payment Details
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="sm:col-span-2">
                <label
                  htmlFor="customerId"
                  className="flex items-center gap-2 text-sm font-medium text-text-primary mb-1.5"
                >
                  <User className="w-4 h-4" />
                  Customer ID *
                </label>
                <Input
                  id="customerId"
                  value={formData.customerId}
                  onChange={(e) => handleChange("customerId", e.target.value)}
                  placeholder="Enter customer ID or search..."
                  className={errors.customerId ? "border-status-error" : ""}
                />
                {errors.customerId && (
                  <p className="text-sm text-status-error mt-1">{errors.customerId}</p>
                )}
              </div>

              <div>
                <label
                  htmlFor="amount"
                  className="block text-sm font-medium text-text-primary mb-1.5"
                >
                  Amount *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">$</span>
                  <Input
                    id="amount"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.amount || ""}
                    onChange={(e) => handleChange("amount", parseFloat(e.target.value) || 0)}
                    placeholder="0.00"
                    className={`pl-7 ${errors.amount ? "border-status-error" : ""}`}
                  />
                </div>
                {errors.amount && (
                  <p className="text-sm text-status-error mt-1">{errors.amount}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Currency
                </label>
                <Select
                  value={formData.currency}
                  onValueChange={(value) => handleChange("currency", value)}
                >
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="CAD">CAD</option>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Payment Method *
                </label>
                <Select
                  value={formData.method}
                  onValueChange={(value) => handleChange("method", value as Payment["method"])}
                >
                  {paymentMethods.map((method) => (
                    <option key={method.value} value={method.value}>
                      {method.label}
                    </option>
                  ))}
                </Select>
                {errors.method && (
                  <p className="text-sm text-status-error mt-1">{errors.method}</p>
                )}
              </div>

              <div>
                <label
                  htmlFor="paymentDate"
                  className="flex items-center gap-2 text-sm font-medium text-text-primary mb-1.5"
                >
                  <Calendar className="w-4 h-4" />
                  Payment Date
                </label>
                <Input
                  id="paymentDate"
                  type="date"
                  value={formData.paymentDate}
                  onChange={(e) => handleChange("paymentDate", e.target.value)}
                />
              </div>

              <div>
                <label
                  htmlFor="referenceNumber"
                  className="block text-sm font-medium text-text-primary mb-1.5"
                >
                  Reference Number
                </label>
                <Input
                  id="referenceNumber"
                  value={formData.referenceNumber}
                  onChange={(e) => handleChange("referenceNumber", e.target.value)}
                  placeholder="Check #, Wire ID, etc."
                />
              </div>

              <div>
                <label
                  htmlFor="invoiceId"
                  className="flex items-center gap-2 text-sm font-medium text-text-primary mb-1.5"
                >
                  <Receipt className="w-4 h-4" />
                  Apply to Invoice (optional)
                </label>
                <Input
                  id="invoiceId"
                  value={formData.invoiceId}
                  onChange={(e) => handleChange("invoiceId", e.target.value)}
                  placeholder="Invoice ID"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Notes
            </h2>
            <textarea
              value={formData.notes}
              onChange={(e) => handleChange("notes", e.target.value)}
              placeholder="Add any notes about this payment..."
              rows={4}
              className="w-full px-3 py-2 rounded-lg border border-border bg-transparent text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Summary */}
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
              Summary
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-border">
                <span className="text-text-muted">Amount</span>
                <span className="text-xl font-bold text-text-primary">
                  ${(formData.amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Method</span>
                <span className="text-text-primary">
                  {paymentMethods.find((m) => m.value === formData.method)?.label}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-text-muted">Date</span>
                <span className="text-text-primary tabular-nums">
                  {formData.paymentDate || "Today"}
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="card p-6 space-y-3">
            <Button
              type="submit"
              className="w-full shadow-glow-sm hover:shadow-glow"
              disabled={recordPayment.isPending}
            >
              {recordPayment.isPending ? "Recording..." : "Record Payment"}
            </Button>
            <Link href="/billing/payments" className="block">
              <Button type="button" variant="outline" className="w-full">
                Cancel
              </Button>
            </Link>
          </div>
        </div>
      </form>
    </div>
  );
}
