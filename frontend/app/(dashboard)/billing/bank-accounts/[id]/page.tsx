"use client";

import { use, useState } from "react";
import Link from "next/link";
import {
  Landmark,
  ArrowLeft,
  Save,
  CheckCircle,
  ArrowUpRight,
  ArrowDownLeft,
  RefreshCw,
  DollarSign,
  Filter,
  Check,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useBankAccount,
  useUpdateBankAccount,
  useBankTransactions,
  useReconcileTransactions,
  type BankTransaction,
} from "@/lib/hooks/api/use-billing";

interface PageProps {
  params: Promise<{ id: string }>;
}

const transactionTypeConfig = {
  deposit: {
    label: "Deposit",
    icon: ArrowDownLeft,
    class: "text-status-success",
  },
  withdrawal: {
    label: "Withdrawal",
    icon: ArrowUpRight,
    class: "text-status-error",
  },
  transfer: {
    label: "Transfer",
    icon: RefreshCw,
    class: "text-accent",
  },
  fee: {
    label: "Fee",
    icon: DollarSign,
    class: "text-status-warning",
  },
  interest: {
    label: "Interest",
    icon: DollarSign,
    class: "text-status-success",
  },
};

export default function BankAccountDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { toast } = useToast();
  const { data: account, isLoading } = useBankAccount(id);
  const updateAccount = useUpdateBankAccount();
  const reconcileTransactions = useReconcileTransactions();

  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<{ name: string; isDefault: boolean }>({
    name: "",
    isDefault: false,
  });

  const [transactionFilter, setTransactionFilter] = useState<BankTransaction["type"] | "">("");
  const [showUnreconciledOnly, setShowUnreconciledOnly] = useState(false);
  const [selectedTransactions, setSelectedTransactions] = useState<string[]>([]);
  const [page, setPage] = useState(1);

  const { data: transactionsData, isLoading: transactionsLoading } = useBankTransactions(id, {
    page,
    pageSize: 20,
    type: transactionFilter || undefined,
    reconciled: showUnreconciledOnly ? false : undefined,
  });

  const handleEdit = () => {
    if (account) {
      setEditData({ name: account.name, isDefault: account.isDefault });
      setIsEditing(true);
    }
  };

  const handleSave = async () => {
    try {
      await updateAccount.mutateAsync({ id, data: editData });
      toast({
        title: "Account updated",
        description: "Bank account has been updated.",
      });
      setIsEditing(false);
    } catch {
      toast({
        title: "Error",
        description: "Failed to update account.",
        variant: "error",
      });
    }
  };

  const handleReconcile = async () => {
    if (selectedTransactions.length === 0) {
      toast({
        title: "No transactions selected",
        description: "Select transactions to reconcile.",
        variant: "error",
      });
      return;
    }

    try {
      await reconcileTransactions.mutateAsync({
        accountId: id,
        transactionIds: selectedTransactions,
      });
      toast({
        title: "Transactions reconciled",
        description: `${selectedTransactions.length} transaction(s) have been reconciled.`,
      });
      setSelectedTransactions([]);
    } catch {
      toast({
        title: "Error",
        description: "Failed to reconcile transactions.",
        variant: "error",
      });
    }
  };

  const toggleTransaction = (transactionId: string) => {
    setSelectedTransactions((prev) =>
      prev.includes(transactionId)
        ? prev.filter((id) => id !== transactionId)
        : [...prev, transactionId]
    );
  };

  if (isLoading) {
    return <AccountDetailSkeleton />;
  }

  if (!account) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Account Not Found"
          breadcrumbs={[
            { label: "Billing", href: "/billing" },
            { label: "Bank Accounts", href: "/billing/bank-accounts" },
            { label: "Not Found" },
          ]}
        />
        <Card className="p-12 text-center">
          <Landmark className="w-12 h-12 mx-auto text-text-muted mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">Account not found</h3>
          <Link href="/billing/bank-accounts">
            <Button>Back to Accounts</Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title={account.name}
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Bank Accounts", href: "/billing/bank-accounts" },
          { label: account.name },
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Account Details */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="p-6">
            {isEditing ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Account Name
                  </label>
                  <Input
                    value={editData.name}
                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="editDefault"
                    checked={editData.isDefault}
                    onChange={(e) => setEditData({ ...editData, isDefault: e.target.checked })}
                    className="w-4 h-4 rounded border-border"
                  />
                  <label htmlFor="editDefault" className="text-sm text-text-primary">
                    Default account
                  </label>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" onClick={() => setIsEditing(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleSave} disabled={updateAccount.isPending}>
                    {updateAccount.isPending ? "Saving..." : "Save"}
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-text-primary">Account Details</h3>
                  <Button variant="ghost" size="sm" onClick={handleEdit}>
                    Edit
                  </Button>
                </div>
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-text-muted">Bank</p>
                    <p className="font-medium text-text-primary">{account.bankName}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Account Number</p>
                    <p className="font-medium text-text-primary">****{account.accountNumber.slice(-4)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Type</p>
                    <p className="font-medium text-text-primary capitalize">{account.type}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted">Currency</p>
                    <p className="font-medium text-text-primary">{account.currency}</p>
                  </div>
                  {account.lastReconciled && (
                    <div>
                      <p className="text-xs text-text-muted">Last Reconciled</p>
                      <p className="font-medium text-text-primary">
                        {new Date(account.lastReconciled).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}
          </Card>

          <Card className="p-6">
            <h3 className="font-semibold text-text-primary mb-4">Current Balance</h3>
            <p className="text-3xl font-bold text-text-primary">
              ${(account.balance / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </p>
            <p className="text-sm text-text-muted mt-1">{account.currency}</p>
          </Card>
        </div>

        {/* Transactions */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-text-primary">Transactions</h3>
              <div className="flex gap-2">
                <Select
                  value={transactionFilter}
                  onChange={(e) => {
                    setTransactionFilter(e.target.value as BankTransaction["type"] | "");
                    setPage(1);
                  }}
                  className="w-36"
                >
                  <option value="">All Types</option>
                  <option value="deposit">Deposits</option>
                  <option value="withdrawal">Withdrawals</option>
                  <option value="transfer">Transfers</option>
                  <option value="fee">Fees</option>
                  <option value="interest">Interest</option>
                </Select>
                <Button
                  variant={showUnreconciledOnly ? "primary" : "outline"}
                  size="sm"
                  onClick={() => {
                    setShowUnreconciledOnly(!showUnreconciledOnly);
                    setPage(1);
                  }}
                >
                  <Filter className="w-4 h-4 mr-1" />
                  Unreconciled
                </Button>
                {selectedTransactions.length > 0 && (
                  <Button
                    onClick={handleReconcile}
                    disabled={reconcileTransactions.isPending}
                    className="shadow-glow-sm hover:shadow-glow"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Reconcile ({selectedTransactions.length})
                  </Button>
                )}
              </div>
            </div>

            {transactionsLoading ? (
              <div className="space-y-3 animate-pulse">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-16 bg-surface-overlay rounded-lg" />
                ))}
              </div>
            ) : transactionsData && transactionsData.items.length > 0 ? (
              <div className="space-y-3">
                {transactionsData.items.map((transaction) => {
                  const typeConfig = transactionTypeConfig[transaction.type];
                  const TypeIcon = typeConfig.icon;
                  const isSelected = selectedTransactions.includes(transaction.id);

                  return (
                    <div
                      key={transaction.id}
                      className={cn(
                        "flex items-center gap-4 p-4 rounded-lg transition-colors",
                        transaction.reconciled
                          ? "bg-surface-overlay"
                          : "bg-status-warning/5 border border-status-warning/20",
                        isSelected && "ring-2 ring-accent"
                      )}
                    >
                      {!transaction.reconciled && (
                        <button
                          onClick={() => toggleTransaction(transaction.id)}
                          className={cn(
                            "w-5 h-5 rounded border flex items-center justify-center flex-shrink-0",
                            isSelected
                              ? "bg-accent border-accent text-text-inverse"
                              : "border-border hover:border-accent"
                          )}
                        >
                          {isSelected && <Check className="w-3 h-3" />}
                        </button>
                      )}
                      {transaction.reconciled && (
                        <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
                      )}

                      <div className={cn("w-8 h-8 rounded flex items-center justify-center", typeConfig.class)}>
                        <TypeIcon className="w-4 h-4" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-text-primary truncate">{transaction.description}</p>
                        <div className="flex gap-3 text-sm text-text-muted">
                          <span>{new Date(transaction.date).toLocaleDateString()}</span>
                          {transaction.reference && <span>Ref: {transaction.reference}</span>}
                        </div>
                      </div>

                      <div className="text-right">
                        <p
                          className={cn(
                            "font-semibold",
                            transaction.type === "deposit" || transaction.type === "interest"
                              ? "text-status-success"
                              : "text-text-primary"
                          )}
                        >
                          {transaction.type === "deposit" || transaction.type === "interest" ? "+" : "-"}
                          ${(transaction.amount / 100).toFixed(2)}
                        </p>
                        <span className={cn("text-xs px-2 py-0.5 rounded", typeConfig.class)}>
                          {typeConfig.label}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                <DollarSign className="w-12 h-12 mx-auto text-text-muted mb-4" />
                <p className="text-text-muted">No transactions found</p>
              </div>
            )}

            {/* Pagination */}
            {transactionsData && transactionsData.totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6 pt-6 border-t border-border">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </Button>
                <span className="text-sm text-text-muted">
                  Page {page} of {transactionsData.totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === transactionsData.totalPages}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function AccountDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-24 bg-surface-overlay rounded" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6">
          <div className="card p-6">
            <div className="h-48 bg-surface-overlay rounded" />
          </div>
          <div className="card p-6">
            <div className="h-24 bg-surface-overlay rounded" />
          </div>
        </div>
        <div className="lg:col-span-2 card p-6">
          <div className="h-96 bg-surface-overlay rounded" />
        </div>
      </div>
    </div>
  );
}
