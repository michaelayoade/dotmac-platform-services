import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  CreditCard,
  Banknote,
  Calendar,
  Receipt,
  User,
  FileText,
} from "lucide-react";
import { Button } from "@/lib/dotmac/core";

import { getPayment, type Payment } from "@/lib/api/payments";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

interface PageProps {
  params: { id: string };
}

export async function generateMetadata({ params }: PageProps) {
  try {
    const payment = await getPayment(params.id);
    return {
      title: `Payment - ${payment.referenceNumber || payment.id}`,
      description: `Payment details for ${payment.customerName || "customer"}`,
    };
  } catch {
    return {
      title: "Payment Not Found",
    };
  }
}

export default async function PaymentDetailPage({ params }: PageProps) {
  let payment: Payment;
  try {
    payment = await getPayment(params.id);
  } catch {
    notFound();
  }

  const statusConfig: Record<
    Payment["status"],
    { icon: typeof CheckCircle; class: string; label: string }
  > = {
    completed: { icon: CheckCircle, class: "status-badge--success", label: "Completed" },
    pending: { icon: Clock, class: "status-badge--warning", label: "Pending" },
    failed: { icon: AlertCircle, class: "status-badge--error", label: "Failed" },
    refunded: { icon: XCircle, class: "bg-surface-overlay text-text-muted", label: "Refunded" },
  };

  const methodLabels: Record<Payment["method"], string> = {
    cash: "Cash",
    check: "Check",
    bank_transfer: "Bank Transfer",
    wire_transfer: "Wire Transfer",
    card: "Card",
    other: "Other",
  };

  const config = statusConfig[payment.status];
  const Icon = config.icon;
  const paymentDate = new Date(payment.paymentDate);
  const createdDate = new Date(payment.createdAt);

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
        <span className="text-text-primary">{payment.referenceNumber || payment.id.slice(0, 8)}</span>
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
            <div className="flex items-center gap-3">
              <h1 className="page-title">
                Payment {payment.referenceNumber || `#${payment.id.slice(0, 8)}`}
              </h1>
              <span className={cn("status-badge", config.class)}>
                <Icon className="w-3 h-3" />
                {config.label}
              </span>
            </div>
            <p className="text-text-muted">
              Recorded on {createdDate.toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Payment Summary */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Payment Summary</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-text-muted mb-1">Amount</p>
                <p className="text-2xl font-bold text-text-primary">
                  ${(payment.amount / 100).toLocaleString()}
                  <span className="text-sm font-normal text-text-muted ml-2">{payment.currency}</span>
                </p>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Payment Method</p>
                <div className="flex items-center gap-2">
                  <Banknote className="w-5 h-5 text-text-secondary" />
                  <span className="text-lg font-medium text-text-primary">
                    {methodLabels[payment.method]}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Payment Date</p>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-text-secondary" />
                  <span className="text-text-primary tabular-nums">
                    {paymentDate.toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Reference Number</p>
                <span className="font-mono text-text-primary">
                  {payment.referenceNumber || "—"}
                </span>
              </div>
            </div>
          </div>

          {/* Notes */}
          {payment.notes && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Notes
              </h2>
              <p className="text-text-secondary whitespace-pre-wrap">{payment.notes}</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Customer Info */}
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
              Customer
            </h3>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent/80 to-highlight/80 flex items-center justify-center text-sm font-semibold text-text-inverse">
                <User className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium text-text-primary">
                  {payment.customerName || "Unknown Customer"}
                </p>
                <p className="text-sm text-text-muted">ID: {payment.customerId.slice(0, 8)}</p>
              </div>
            </div>
          </div>

          {/* Linked Invoice */}
          {payment.invoiceId && (
            <div className="card p-6">
              <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
                Linked Invoice
              </h3>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-overlay flex items-center justify-center">
                  <Receipt className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <Link
                    href={`/billing/invoices/${payment.invoiceId}`}
                    className="font-mono text-accent hover:text-accent-hover"
                  >
                    {payment.invoiceNumber || payment.invoiceId.slice(0, 8)}
                  </Link>
                  <p className="text-sm text-text-muted">View invoice details</p>
                </div>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
              Actions
            </h3>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <CreditCard className="w-4 h-4 mr-2" />
                Issue Refund
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <Receipt className="w-4 h-4 mr-2" />
                Send Receipt
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
