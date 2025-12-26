"use client";

import { useState } from "react";
import Link from "next/link";
import {
  CreditCard,
  Plus,
  Trash2,
  Star,
  RefreshCw,
  AlertCircle,
  Check,
  X,
} from "lucide-react";
import { Button, useToast } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  usePaymentMethods,
  useSetDefaultPaymentMethod,
  useDeletePaymentMethod,
} from "@/lib/hooks/api/use-billing";
import type { PaymentMethod } from "@/types/models";

// Card brand icons mapping
const cardBrandIcons: Record<string, string> = {
  visa: "💳",
  mastercard: "💳",
  amex: "💳",
  discover: "💳",
  default: "💳",
};

export default function PaymentMethodsPage() {
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const { data: paymentMethods = [], isLoading } = usePaymentMethods();
  const setDefaultPaymentMethod = useSetDefaultPaymentMethod();
  const deletePaymentMethod = useDeletePaymentMethod();

  const [showAddModal, setShowAddModal] = useState(false);
  const [actioningId, setActioningId] = useState<string | null>(null);

  // Form state for adding card
  const [cardNumber, setCardNumber] = useState("");
  const [expiryMonth, setExpiryMonth] = useState("");
  const [expiryYear, setExpiryYear] = useState("");
  const [cvc, setCvc] = useState("");
  const [cardholderName, setCardholderName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSetDefault = async (id: string) => {
    setActioningId(id);
    try {
      await setDefaultPaymentMethod.mutateAsync(id);
      toast({
        title: "Default payment method updated",
        description: "This card will be used for future charges.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to update default payment method.",
        variant: "error",
      });
    } finally {
      setActioningId(null);
    }
  };

  const handleDelete = async (id: string) => {
    const method = paymentMethods.find((m: PaymentMethod) => m.id === id);
    const confirmed = await confirm({
      title: "Remove Payment Method",
      description: `Are you sure you want to remove the card ending in ${method?.last4 || "****"}? Future charges will use the default payment method.`,
      variant: "danger",
    });

    if (!confirmed) return;

    setActioningId(id);
    try {
      await deletePaymentMethod.mutateAsync(id);
      toast({
        title: "Payment method removed",
        description: "The payment method has been removed.",
        variant: "success",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to remove payment method.",
        variant: "error",
      });
    } finally {
      setActioningId(null);
    }
  };

  const handleAddCard = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate API call - in real implementation this would use Stripe Elements
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      toast({
        title: "Payment method added",
        description: "Your card has been added successfully.",
        variant: "success",
      });
      setShowAddModal(false);
      resetForm();
    } catch {
      toast({
        title: "Error",
        description: "Failed to add payment method.",
        variant: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setCardNumber("");
    setExpiryMonth("");
    setExpiryYear("");
    setCvc("");
    setCardholderName("");
  };

  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\D/g, "");
    const groups = cleaned.match(/.{1,4}/g);
    return groups ? groups.join(" ").substring(0, 19) : "";
  };

  const getCardBrand = (number: string): string => {
    const cleaned = number.replace(/\s/g, "");
    if (cleaned.startsWith("4")) return "visa";
    if (/^5[1-5]/.test(cleaned) || /^2[2-7]/.test(cleaned)) return "mastercard";
    if (/^3[47]/.test(cleaned)) return "amex";
    if (/^6(?:011|5)/.test(cleaned)) return "discover";
    return "default";
  };

  return (
    <div className="space-y-6">
      {/* Confirm dialog */}
      {dialog}

      {/* Page Header with Breadcrumbs */}
      <div>
        <div className="flex items-center gap-2 text-sm text-text-muted mb-4">
          <Link href="/billing" className="hover:text-text-secondary">
            Billing
          </Link>
          <span>/</span>
          <span className="text-text-primary">Payment Methods</span>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">
              Payment Methods
            </h1>
            <p className="text-text-muted mt-1">
              Manage your cards and payment options
            </p>
          </div>
          <Button
            onClick={() => setShowAddModal(true)}
            className="shadow-glow-sm hover:shadow-glow"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Payment Method
          </Button>
        </div>
      </div>

      {/* Payment Methods List */}
      <div className="card">
        {isLoading ? (
          <div className="p-8 text-center text-text-muted">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading payment methods...
          </div>
        ) : paymentMethods.length === 0 ? (
          <div className="p-12 text-center">
            <CreditCard className="w-12 h-12 mx-auto text-text-muted mb-4" />
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              No payment methods
            </h3>
            <p className="text-text-muted mb-6">
              Add a payment method to enable automatic billing
            </p>
            <Button onClick={() => setShowAddModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Payment Method
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {paymentMethods.map((method: PaymentMethod) => {
              const isActioning = actioningId === method.id;

              return (
                <div
                  key={method.id}
                  className="p-4 flex items-center justify-between group"
                >
                  <div className="flex items-center gap-4">
                    {/* Card Icon */}
                    <div
                      className={cn(
                        "w-14 h-10 rounded-lg flex items-center justify-center text-2xl",
                        method.isDefault
                          ? "bg-accent-subtle border-2 border-accent"
                          : "bg-surface-overlay border border-border"
                      )}
                    >
                      {cardBrandIcons[method.brand?.toLowerCase() || "default"]}
                    </div>

                    {/* Card Details */}
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-text-primary">
                          {method.brand || "Card"} •••• {method.last4}
                        </p>
                        {method.isDefault && (
                          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-accent-subtle text-accent">
                            <Star className="w-3 h-3" />
                            Default
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-text-muted">
                        Expires {method.expMonth?.toString().padStart(2, "0")}/{method.expYear}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    {isActioning ? (
                      <RefreshCw className="w-4 h-4 animate-spin text-text-muted" />
                    ) : (
                      <>
                        {!method.isDefault && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSetDefault(method.id)}
                          >
                            <Star className="w-3 h-3 mr-1" />
                            Set Default
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(method.id)}
                          className="text-status-error hover:text-status-error"
                          disabled={method.isDefault}
                          title={method.isDefault ? "Cannot remove default payment method" : "Remove"}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Security Notice */}
      <div className="flex items-start gap-3 p-4 bg-surface-overlay border border-border rounded-lg">
        <CreditCard className="w-5 h-5 text-text-muted flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-text-primary">Secure payment processing</p>
          <p className="text-text-muted mt-1">
            Your payment information is encrypted and securely stored. We never store your full card number.
          </p>
        </div>
      </div>

      {/* Add Payment Method Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-overlay/60 backdrop-blur-sm"
            onClick={() => {
              setShowAddModal(false);
              resetForm();
            }}
          />
          <div className="relative w-full max-w-md mx-4 bg-surface border border-border rounded-xl shadow-2xl animate-fade-up">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                  <CreditCard className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-text-primary">
                    Add Payment Method
                  </h2>
                  <p className="text-xs text-text-muted">
                    Add a credit or debit card
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  resetForm();
                }}
                className="p-2 rounded-lg hover:bg-surface-hover transition-colors"
              >
                <X className="w-5 h-5 text-text-muted" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleAddCard} className="p-4 space-y-4">
              {/* Card Number */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Card Number
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={formatCardNumber(cardNumber)}
                    onChange={(e) => setCardNumber(e.target.value.replace(/\D/g, "").slice(0, 16))}
                    placeholder="1234 5678 9012 3456"
                    className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent font-mono"
                    autoComplete="cc-number"
                    required
                  />
                  {cardNumber && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-lg">
                      {cardBrandIcons[getCardBrand(cardNumber)]}
                    </span>
                  )}
                </div>
              </div>

              {/* Cardholder Name */}
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Cardholder Name
                </label>
                <input
                  type="text"
                  value={cardholderName}
                  onChange={(e) => setCardholderName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent"
                  autoComplete="cc-name"
                  required
                />
              </div>

              {/* Expiry & CVC */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Month
                  </label>
                  <select
                    value={expiryMonth}
                    onChange={(e) => setExpiryMonth(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                    required
                  >
                    <option value="">MM</option>
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
                      <option key={month} value={month.toString().padStart(2, "0")}>
                        {month.toString().padStart(2, "0")}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    Year
                  </label>
                  <select
                    value={expiryYear}
                    onChange={(e) => setExpiryYear(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                    required
                  >
                    <option value="">YY</option>
                    {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() + i).map((year) => (
                      <option key={year} value={year.toString()}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">
                    CVC
                  </label>
                  <input
                    type="text"
                    value={cvc}
                    onChange={(e) => setCvc(e.target.value.replace(/\D/g, "").slice(0, 4))}
                    placeholder="123"
                    className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent font-mono"
                    autoComplete="cc-csc"
                    required
                  />
                </div>
              </div>

              {/* Security Info */}
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <Check className="w-3 h-3 text-status-success" />
                Your card details are encrypted and secure
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowAddModal(false);
                    resetForm();
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="shadow-glow-sm"
                >
                  {isSubmitting ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4 mr-2" />
                      Add Card
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
