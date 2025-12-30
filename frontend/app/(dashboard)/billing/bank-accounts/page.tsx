"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Landmark,
  Plus,
  DollarSign,
  Wallet,
  PiggyBank,
  ChevronRight,
  CheckCircle,
  CreditCard,
  Banknote,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useBankAccounts,
  useCreateBankAccount,
  type BankAccount,
} from "@/lib/hooks/api/use-billing";

const accountTypeConfig = {
  checking: { label: "Checking", icon: Wallet, class: "bg-accent-subtle text-accent" },
  savings: { label: "Savings", icon: PiggyBank, class: "bg-status-success/15 text-status-success" },
  cash: { label: "Cash", icon: Banknote, class: "bg-status-warning/15 text-status-warning" },
};

export default function BankAccountsPage() {
  const { toast } = useToast();
  const { data: accounts, isLoading } = useBankAccounts();
  const createAccount = useCreateBankAccount();
  const [showNewForm, setShowNewForm] = useState(false);
  const [newAccount, setNewAccount] = useState({
    name: "",
    accountNumber: "",
    bankName: "",
    type: "checking" as BankAccount["type"],
    currency: "USD",
    isDefault: false,
  });

  const handleCreate = async () => {
    if (!newAccount.name || !newAccount.accountNumber || !newAccount.bankName) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields.",
        variant: "error",
      });
      return;
    }

    try {
      await createAccount.mutateAsync(newAccount);
      toast({
        title: "Account created",
        description: "Bank account has been added successfully.",
      });
      setShowNewForm(false);
      setNewAccount({
        name: "",
        accountNumber: "",
        bankName: "",
        type: "checking",
        currency: "USD",
        isDefault: false,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to create bank account.",
        variant: "error",
      });
    }
  };

  const totalBalance = accounts?.reduce((sum, acc) => sum + acc.balance, 0) ?? 0;

  if (isLoading) {
    return <BankAccountsSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Bank Accounts"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Bank Accounts" },
        ]}
        actions={
          <div className="flex gap-3">
            <Link href="/billing/bank-accounts/payments">
              <Button variant="outline">
                <CreditCard className="w-4 h-4 mr-2" />
                Manual Payments
              </Button>
            </Link>
            <Link href="/billing/bank-accounts/registers">
              <Button variant="outline">
                <Banknote className="w-4 h-4 mr-2" />
                Cash Registers
              </Button>
            </Link>
            <Button onClick={() => setShowNewForm(true)} className="shadow-glow-sm hover:shadow-glow">
              <Plus className="w-4 h-4 mr-2" />
              Add Account
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <DollarSign className="w-5 h-5 text-status-success" />
            <div>
              <p className="text-sm text-text-muted">Total Balance</p>
              <p className="text-xl font-bold text-text-primary">
                ${(totalBalance / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Landmark className="w-5 h-5 text-accent" />
            <div>
              <p className="text-sm text-text-muted">Total Accounts</p>
              <p className="text-xl font-bold text-text-primary">{accounts?.length ?? 0}</p>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-status-info" />
            <div>
              <p className="text-sm text-text-muted">Last Reconciled</p>
              <p className="text-xl font-bold text-text-primary">
                {accounts?.some((a) => a.lastReconciled)
                  ? new Date(
                      Math.max(...accounts.filter((a) => a.lastReconciled).map((a) => new Date(a.lastReconciled!).getTime()))
                    ).toLocaleDateString()
                  : "Never"}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* New Account Form */}
      {showNewForm && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-6">Add Bank Account</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Account Name <span className="text-status-error">*</span>
              </label>
              <Input
                value={newAccount.name}
                onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                placeholder="e.g., Main Operating Account"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Bank Name <span className="text-status-error">*</span>
              </label>
              <Input
                value={newAccount.bankName}
                onChange={(e) => setNewAccount({ ...newAccount, bankName: e.target.value })}
                placeholder="e.g., Chase Bank"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Account Number <span className="text-status-error">*</span>
              </label>
              <Input
                value={newAccount.accountNumber}
                onChange={(e) => setNewAccount({ ...newAccount, accountNumber: e.target.value })}
                placeholder="****1234"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Account Type
              </label>
              <Select
                value={newAccount.type}
                onChange={(e) =>
                  setNewAccount({ ...newAccount, type: e.target.value as BankAccount["type"] })
                }
              >
                <option value="checking">Checking</option>
                <option value="savings">Savings</option>
                <option value="cash">Cash</option>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Currency
              </label>
              <Select
                value={newAccount.currency}
                onChange={(e) => setNewAccount({ ...newAccount, currency: e.target.value })}
              >
                <option value="USD">USD - US Dollar</option>
                <option value="EUR">EUR - Euro</option>
                <option value="GBP">GBP - British Pound</option>
              </Select>
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="isDefault"
                checked={newAccount.isDefault}
                onChange={(e) => setNewAccount({ ...newAccount, isDefault: e.target.checked })}
                className="w-4 h-4 rounded border-border"
              />
              <label htmlFor="isDefault" className="text-sm text-text-primary">
                Set as default account
              </label>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border">
            <Button variant="ghost" onClick={() => setShowNewForm(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createAccount.isPending}
              className="shadow-glow-sm hover:shadow-glow"
            >
              {createAccount.isPending ? "Creating..." : "Add Account"}
            </Button>
          </div>
        </Card>
      )}

      {/* Accounts List */}
      {accounts && accounts.length > 0 ? (
        <div className="space-y-4">
          {accounts.map((account) => {
            const typeConfig = accountTypeConfig[account.type];
            const TypeIcon = typeConfig.icon;

            return (
              <Link key={account.id} href={`/billing/bank-accounts/${account.id}`}>
                <Card className="p-6 hover:border-accent transition-colors">
                  <div className="flex items-center gap-4">
                    <div
                      className={cn(
                        "w-12 h-12 rounded-lg flex items-center justify-center",
                        typeConfig.class
                      )}
                    >
                      <TypeIcon className="w-6 h-6" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-text-primary">{account.name}</span>
                        {account.isDefault && (
                          <span className="px-2 py-0.5 bg-accent-subtle text-accent text-xs rounded">
                            Default
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-text-muted">
                        <span>{account.bankName}</span>
                        <span>****{account.accountNumber.slice(-4)}</span>
                        <span className={cn("capitalize px-2 py-0.5 rounded text-xs", typeConfig.class)}>
                          {typeConfig.label}
                        </span>
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="text-xl font-bold text-text-primary">
                        ${(account.balance / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </p>
                      <p className="text-sm text-text-muted">{account.currency}</p>
                    </div>

                    <ChevronRight className="w-5 h-5 text-text-muted flex-shrink-0" />
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      ) : (
        <Card className="p-12 text-center">
          <Landmark className="w-12 h-12 mx-auto text-text-muted mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No bank accounts</h3>
          <p className="text-text-muted mb-6">Add a bank account to track your finances</p>
          <Button onClick={() => setShowNewForm(true)} className="shadow-glow-sm hover:shadow-glow">
            <Plus className="w-4 h-4 mr-2" />
            Add Your First Account
          </Button>
        </Card>
      )}
    </div>
  );
}

function BankAccountsSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-36 bg-surface-overlay rounded" />
          <div className="h-10 w-32 bg-surface-overlay rounded" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-4">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 bg-surface-overlay rounded" />
              <div>
                <div className="h-4 w-24 bg-surface-overlay rounded mb-2" />
                <div className="h-6 w-20 bg-surface-overlay rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-surface-overlay" />
              <div className="flex-1">
                <div className="h-5 w-40 bg-surface-overlay rounded mb-2" />
                <div className="h-4 w-64 bg-surface-overlay rounded" />
              </div>
              <div className="h-6 w-24 bg-surface-overlay rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
