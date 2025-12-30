"use client";

import { useState, useEffect, useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";
import { Button } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";
import type { Invoice } from "@/lib/api/billing";

interface InvoiceFiltersProps {
  currentStatus?: Invoice["status"];
}

export function InvoiceFilters({ currentStatus }: InvoiceFiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [searchValue, setSearchValue] = useState(searchParams.get("search") || "");

  useEffect(() => {
    setSearchValue(searchParams.get("search") || "");
  }, [searchParams]);

  const updateParams = (updates: Record<string, string | undefined>) => {
    const params = new URLSearchParams(searchParams.toString());

    Object.entries(updates).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    });

    // Reset to page 1 when filters change
    if (updates.search !== undefined || updates.status !== undefined) {
      params.delete("page");
    }

    startTransition(() => {
      router.push(`/billing/invoices?${params.toString()}`);
    });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    updateParams({ search: searchValue || undefined });
  };

  const handleStatusChange = (status: Invoice["status"] | undefined) => {
    updateParams({ status });
  };

  return (
    <div className="card p-4">
      <div className="flex flex-col sm:flex-row gap-4">
        <form onSubmit={handleSearch} className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Search invoices by number, customer..."
            className={cn(
              "w-full pl-10 pr-4 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent",
              isPending && "opacity-70"
            )}
          />
        </form>
        <div className="flex items-center gap-2">
          <StatusFilterButton
            status={undefined}
            label="All"
            currentStatus={currentStatus}
            onClick={() => handleStatusChange(undefined)}
            isPending={isPending}
          />
          <StatusFilterButton
            status="pending"
            label="Pending"
            currentStatus={currentStatus}
            onClick={() => handleStatusChange("pending")}
            isPending={isPending}
          />
          <StatusFilterButton
            status="paid"
            label="Paid"
            currentStatus={currentStatus}
            onClick={() => handleStatusChange("paid")}
            isPending={isPending}
          />
          <StatusFilterButton
            status="overdue"
            label="Overdue"
            currentStatus={currentStatus}
            onClick={() => handleStatusChange("overdue")}
            isPending={isPending}
          />
        </div>
      </div>
    </div>
  );
}

function StatusFilterButton({
  status,
  label,
  currentStatus,
  onClick,
  isPending,
}: {
  status: Invoice["status"] | undefined;
  label: string;
  currentStatus: Invoice["status"] | undefined;
  onClick: () => void;
  isPending: boolean;
}) {
  const isActive = status === currentStatus;

  return (
    <Button
      variant={isActive ? "default" : "outline"}
      size="sm"
      onClick={onClick}
      disabled={isPending}
      className={cn(isActive && "shadow-glow-sm")}
    >
      {label}
    </Button>
  );
}
