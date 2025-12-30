"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Plus,
  Banknote,
  DollarSign,
  Clock,
  User,
  AlertTriangle,
  CheckCircle,
  XCircle,
  MapPin,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useCashRegisters,
  useOpenCashRegister,
  useCloseCashRegister,
  type CashRegister,
} from "@/lib/hooks/api/use-billing";

const statusConfig = {
  open: {
    label: "Open",
    icon: CheckCircle,
    class: "bg-status-success/15 text-status-success",
  },
  closed: {
    label: "Closed",
    icon: XCircle,
    class: "bg-surface-overlay text-text-muted",
  },
};

export default function CashRegistersPage() {
  const { toast } = useToast();
  const { data: registers, isLoading } = useCashRegisters();
  const openRegister = useOpenCashRegister();
  const closeRegister = useCloseCashRegister();

  const [openingId, setOpeningId] = useState<string | null>(null);
  const [closingId, setClosingId] = useState<string | null>(null);
  const [openingBalance, setOpeningBalance] = useState<number>(0);
  const [expectedBalance, setExpectedBalance] = useState<number>(0);

  const handleOpen = async (registerId: string) => {
    try {
      await openRegister.mutateAsync({
        id: registerId,
        openingBalance: Math.round(openingBalance * 100),
      });
      toast({
        title: "Register opened",
        description: "Cash register has been opened successfully.",
      });
      setOpeningId(null);
      setOpeningBalance(0);
    } catch {
      toast({
        title: "Error",
        description: "Failed to open register.",
        variant: "error",
      });
    }
  };

  const handleClose = async (registerId: string) => {
    try {
      await closeRegister.mutateAsync({
        id: registerId,
        expectedBalance: Math.round(expectedBalance * 100),
      });
      toast({
        title: "Register closed",
        description: "Cash register has been closed.",
      });
      setClosingId(null);
      setExpectedBalance(0);
    } catch {
      toast({
        title: "Error",
        description: "Failed to close register.",
        variant: "error",
      });
    }
  };

  const openRegisters = registers?.filter((r) => r.status === "open") ?? [];
  const closedRegisters = registers?.filter((r) => r.status === "closed") ?? [];
  const totalInRegisters = openRegisters.reduce((sum, r) => sum + r.currentBalance, 0);

  if (isLoading) {
    return <CashRegistersSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Cash Registers"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Bank Accounts", href: "/billing/bank-accounts" },
          { label: "Cash Registers" },
        ]}
        actions={
          <Link href="/billing/bank-accounts">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
        }
      />

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <DollarSign className="w-5 h-5 text-status-success" />
            <div>
              <p className="text-sm text-text-muted">Cash in Open Registers</p>
              <p className="text-xl font-bold text-text-primary">
                ${(totalInRegisters / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-status-success" />
            <div>
              <p className="text-sm text-text-muted">Open Registers</p>
              <p className="text-xl font-bold text-text-primary">{openRegisters.length}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <XCircle className="w-5 h-5 text-text-muted" />
            <div>
              <p className="text-sm text-text-muted">Closed Registers</p>
              <p className="text-xl font-bold text-text-primary">{closedRegisters.length}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Open Registers */}
      {openRegisters.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">Open Registers</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {openRegisters.map((register) => (
              <RegisterCard
                key={register.id}
                register={register}
                isClosing={closingId === register.id}
                expectedBalance={expectedBalance}
                onExpectedBalanceChange={setExpectedBalance}
                onStartClose={() => {
                  setClosingId(register.id);
                  setExpectedBalance(register.currentBalance / 100);
                }}
                onCancelClose={() => setClosingId(null)}
                onClose={() => handleClose(register.id)}
                isLoading={closeRegister.isPending}
              />
            ))}
          </div>
        </div>
      )}

      {/* Closed Registers */}
      {closedRegisters.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">Closed Registers</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {closedRegisters.map((register) => (
              <RegisterCard
                key={register.id}
                register={register}
                isOpening={openingId === register.id}
                openingBalance={openingBalance}
                onOpeningBalanceChange={setOpeningBalance}
                onStartOpen={() => {
                  setOpeningId(register.id);
                  setOpeningBalance(0);
                }}
                onCancelOpen={() => setOpeningId(null)}
                onOpen={() => handleOpen(register.id)}
                isLoading={openRegister.isPending}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {registers?.length === 0 && (
        <Card className="p-12 text-center">
          <Banknote className="w-12 h-12 mx-auto text-text-muted mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No cash registers</h3>
          <p className="text-text-muted">Cash registers will appear here once configured</p>
        </Card>
      )}
    </div>
  );
}

function RegisterCard({
  register,
  isOpening,
  isClosing,
  openingBalance,
  expectedBalance,
  onOpeningBalanceChange,
  onExpectedBalanceChange,
  onStartOpen,
  onCancelOpen,
  onStartClose,
  onCancelClose,
  onOpen,
  onClose,
  isLoading,
}: {
  register: CashRegister;
  isOpening?: boolean;
  isClosing?: boolean;
  openingBalance?: number;
  expectedBalance?: number;
  onOpeningBalanceChange?: (value: number) => void;
  onExpectedBalanceChange?: (value: number) => void;
  onStartOpen?: () => void;
  onCancelOpen?: () => void;
  onStartClose?: () => void;
  onCancelClose?: () => void;
  onOpen?: () => void;
  onClose?: () => void;
  isLoading?: boolean;
}) {
  const statusInfo = statusConfig[register.status];
  const StatusIcon = statusInfo.icon;

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", statusInfo.class)}>
            <Banknote className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-text-primary">{register.name}</span>
              <span className={cn("status-badge", statusInfo.class)}>
                <StatusIcon className="w-3 h-3 mr-1" />
                {statusInfo.label}
              </span>
            </div>
            {register.location && (
              <p className="text-sm text-text-muted flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {register.location}
              </p>
            )}
          </div>
        </div>
      </div>

      {register.status === "open" && (
        <>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-3 bg-surface-overlay rounded-lg">
              <p className="text-xs text-text-muted">Opening Balance</p>
              <p className="font-semibold text-text-primary">
                ${(register.openingBalance / 100).toFixed(2)}
              </p>
            </div>
            <div className="p-3 bg-status-success/15 rounded-lg">
              <p className="text-xs text-text-muted">Current Balance</p>
              <p className="font-semibold text-status-success">
                ${(register.currentBalance / 100).toFixed(2)}
              </p>
            </div>
          </div>

          <div className="text-sm text-text-muted mb-4">
            <p className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Opened: {new Date(register.openedAt!).toLocaleString()}
            </p>
            <p className="flex items-center gap-1">
              <User className="w-3 h-3" />
              By: {register.openedBy}
            </p>
          </div>

          {isClosing ? (
            <div className="space-y-4 p-4 bg-surface-overlay rounded-lg">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Expected Cash Balance
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    type="number"
                    min={0}
                    step={0.01}
                    value={expectedBalance}
                    onChange={(e) => onExpectedBalanceChange?.(parseFloat(e.target.value) || 0)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={onCancelClose}>
                  Cancel
                </Button>
                <Button size="sm" onClick={onClose} disabled={isLoading}>
                  {isLoading ? "Closing..." : "Close Register"}
                </Button>
              </div>
            </div>
          ) : (
            <Button variant="outline" onClick={onStartClose} className="w-full">
              Close Register
            </Button>
          )}
        </>
      )}

      {register.status === "closed" && (
        <>
          {register.closedAt && (
            <div className="text-sm text-text-muted mb-4">
              <p className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Closed: {new Date(register.closedAt).toLocaleString()}
              </p>
              {register.closedBy && (
                <p className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  By: {register.closedBy}
                </p>
              )}
            </div>
          )}

          {register.variance !== undefined && register.variance !== 0 && (
            <div
              className={cn(
                "p-3 rounded-lg mb-4 flex items-center gap-2",
                register.variance > 0
                  ? "bg-status-success/15 text-status-success"
                  : "bg-status-error/15 text-status-error"
              )}
            >
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm font-medium">
                Variance: {register.variance > 0 ? "+" : ""}${(register.variance / 100).toFixed(2)}
              </span>
            </div>
          )}

          {isOpening ? (
            <div className="space-y-4 p-4 bg-surface-overlay rounded-lg">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Opening Balance
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    type="number"
                    min={0}
                    step={0.01}
                    value={openingBalance}
                    onChange={(e) => onOpeningBalanceChange?.(parseFloat(e.target.value) || 0)}
                    className="pl-10"
                    placeholder="0.00"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={onCancelOpen}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={onOpen}
                  disabled={isLoading}
                  className="shadow-glow-sm hover:shadow-glow"
                >
                  {isLoading ? "Opening..." : "Open Register"}
                </Button>
              </div>
            </div>
          ) : (
            <Button onClick={onStartOpen} className="w-full shadow-glow-sm hover:shadow-glow">
              Open Register
            </Button>
          )}
        </>
      )}
    </Card>
  );
}

function CashRegistersSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-24 bg-surface-overlay rounded" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-4">
            <div className="h-12 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2].map((i) => (
          <div key={i} className="card p-6">
            <div className="h-48 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
