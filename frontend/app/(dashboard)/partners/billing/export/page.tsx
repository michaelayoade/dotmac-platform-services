"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Download,
  FileSpreadsheet,
  FileText,
  FileIcon,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  Calendar,
  Building2,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  usePartnerBillingSummary,
  useExportPartnerInvoices,
  usePartnerExportHistory,
  useDownloadExport,
} from "@/lib/hooks/api/use-partner-portal";
import type { ExportJob } from "@/lib/api/partner-portal";

const formatConfig = {
  csv: { icon: FileSpreadsheet, label: "CSV", description: "Spreadsheet format" },
  excel: { icon: FileSpreadsheet, label: "Excel", description: "Microsoft Excel format" },
  pdf: { icon: FileText, label: "PDF", description: "Printable document" },
};

const statusConfig = {
  pending: { icon: Clock, class: "text-text-muted", label: "Pending" },
  processing: { icon: Loader2, class: "text-status-info animate-spin", label: "Processing" },
  completed: { icon: CheckCircle, class: "text-status-success", label: "Completed" },
  failed: { icon: AlertCircle, class: "text-status-error", label: "Failed" },
};

export default function PartnerExportPage() {
  const { toast } = useToast();
  const { data: summary } = usePartnerBillingSummary();
  const { data: historyData, isLoading: historyLoading, refetch } = usePartnerExportHistory();
  const exportInvoices = useExportPartnerInvoices();
  const downloadExport = useDownloadExport();

  const tenants = summary?.revenueByTenant ?? [];
  const exports = historyData?.items ?? [];

  // Export form state
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setMonth(date.getMonth() - 1);
    return date.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [selectedTenants, setSelectedTenants] = useState<string[]>([]);
  const [exportFormat, setExportFormat] = useState<"csv" | "excel" | "pdf">("csv");

  const handleExport = async () => {
    try {
      await exportInvoices.mutateAsync({
        startDate,
        endDate,
        tenantIds: selectedTenants.length > 0 ? selectedTenants : undefined,
        format: exportFormat,
      });

      toast({
        title: "Export started",
        description: "Your export is being processed. Check the history below.",
      });

      // Refetch history to show the new export
      refetch();
    } catch {
      toast({
        title: "Export failed",
        description: "Failed to start export. Please try again.",
        variant: "error",
      });
    }
  };

  const handleDownload = async (exportJob: ExportJob) => {
    if (!exportJob.downloadUrl) return;

    try {
      const blob = await downloadExport.mutateAsync(exportJob.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `invoices-export-${exportJob.id}.${exportJob.format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      toast({
        title: "Download failed",
        description: "Failed to download export. Please try again.",
        variant: "error",
      });
    }
  };

  const toggleTenant = (tenantId: string) => {
    setSelectedTenants((prev) =>
      prev.includes(tenantId)
        ? prev.filter((id) => id !== tenantId)
        : [...prev, tenantId]
    );
  };

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Export Invoices"
        breadcrumbs={[
          { label: "Partners", href: "/partners" },
          { label: "Billing", href: "/partners/billing" },
          { label: "Export" },
        ]}
        actions={
          <Link href="/partners/billing/invoices">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Invoices
            </Button>
          </Link>
        }
      />

      {/* Export Configuration */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
            <Download className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">New Export</h3>
            <p className="text-sm text-text-muted">
              Configure and generate a new invoice export
            </p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-3">
              Date Range
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-text-muted mb-1.5">Start Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1.5">End Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Tenant Selection */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-3">
              Tenants
              <span className="text-text-muted font-normal ml-2">
                (Leave empty for all tenants)
              </span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {tenants.map((tenant) => {
                const isSelected = selectedTenants.includes(tenant.tenantId);
                return (
                  <button
                    key={tenant.tenantId}
                    type="button"
                    onClick={() => toggleTenant(tenant.tenantId)}
                    className={cn(
                      "flex items-center gap-3 p-3 rounded-lg border-2 transition-all text-left",
                      isSelected
                        ? "border-accent bg-accent-subtle/30"
                        : "border-border hover:border-accent/50 bg-surface-overlay"
                    )}
                  >
                    <div
                      className={cn(
                        "w-5 h-5 rounded border-2 flex items-center justify-center",
                        isSelected
                          ? "border-accent bg-accent"
                          : "border-border bg-surface"
                      )}
                    >
                      {isSelected && <CheckCircle className="w-3 h-3 text-text-inverse" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-text-primary truncate">
                        {tenant.tenantName}
                      </p>
                      <p className="text-xs text-text-muted">
                        ${(tenant.revenue / 100).toLocaleString()} revenue
                      </p>
                    </div>
                  </button>
                );
              })}
              {tenants.length === 0 && (
                <div className="col-span-full p-6 text-center text-text-muted">
                  <Building2 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No tenants available</p>
                </div>
              )}
            </div>
          </div>

          {/* Export Format */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-3">
              Export Format
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {(Object.entries(formatConfig) as [keyof typeof formatConfig, typeof formatConfig.csv][]).map(
                ([key, config]) => {
                  const isSelected = exportFormat === key;
                  const FormatIcon = config.icon;
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setExportFormat(key)}
                      className={cn(
                        "flex items-center gap-3 p-4 rounded-lg border-2 transition-all text-left",
                        isSelected
                          ? "border-accent bg-accent-subtle/30"
                          : "border-border hover:border-accent/50 bg-surface-overlay"
                      )}
                    >
                      <FormatIcon
                        className={cn(
                          "w-5 h-5",
                          isSelected ? "text-accent" : "text-text-muted"
                        )}
                      />
                      <div>
                        <p className="text-sm font-medium text-text-primary">
                          {config.label}
                        </p>
                        <p className="text-xs text-text-muted">{config.description}</p>
                      </div>
                    </button>
                  );
                }
              )}
            </div>
          </div>

          {/* Export Button */}
          <div className="flex justify-end pt-4 border-t border-border">
            <Button
              onClick={handleExport}
              disabled={exportInvoices.isPending}
              className="shadow-glow-sm hover:shadow-glow"
            >
              {exportInvoices.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Starting Export...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Generate Export
                </>
              )}
            </Button>
          </div>
        </div>
      </Card>

      {/* Export History */}
      <Card className="overflow-hidden">
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                <FileIcon className="w-5 h-5 text-highlight" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Export History</h3>
                <p className="text-sm text-text-muted">
                  Previous exports and their download links
                </p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => refetch()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        <div className="overflow-x-auto">
          {historyLoading ? (
            <div className="p-8 text-center">
              <Loader2 className="w-8 h-8 mx-auto text-text-muted animate-spin mb-4" />
              <p className="text-text-muted">Loading export history...</p>
            </div>
          ) : exports.length > 0 ? (
            <table className="data-table" aria-label="Export history"><caption className="sr-only">Export history</caption>
              <thead>
                <tr>
                  <th>Created</th>
                  <th>Format</th>
                  <th>Status</th>
                  <th>Completed</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {exports.map((exportJob) => {
                  const config = statusConfig[exportJob.status];
                  const StatusIcon = config.icon;
                  const formatInfo = formatConfig[exportJob.format as keyof typeof formatConfig];
                  const FormatIcon = formatInfo?.icon || FileIcon;

                  return (
                    <tr key={exportJob.id} className="group">
                      <td>
                        <span className="text-sm text-text-primary tabular-nums">
                          {format(new Date(exportJob.createdAt), "MMM d, yyyy h:mm a")}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <FormatIcon className="w-4 h-4 text-text-muted" />
                          <span className="text-sm text-text-primary uppercase">
                            {exportJob.format}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className={cn("inline-flex items-center gap-1.5 text-sm", config.class)}>
                          <StatusIcon className="w-4 h-4" />
                          {config.label}
                        </span>
                        {exportJob.error && (
                          <p className="text-xs text-status-error mt-1">{exportJob.error}</p>
                        )}
                      </td>
                      <td>
                        {exportJob.completedAt ? (
                          <span className="text-sm text-text-muted tabular-nums">
                            {format(new Date(exportJob.completedAt), "MMM d, yyyy h:mm a")}
                          </span>
                        ) : (
                          <span className="text-sm text-text-muted">—</span>
                        )}
                      </td>
                      <td>
                        {exportJob.status === "completed" && exportJob.downloadUrl && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(exportJob)}
                            disabled={downloadExport.isPending}
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Download className="w-4 h-4 mr-1" />
                            Download
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <FileIcon className="w-12 h-12 mx-auto text-text-muted mb-4" />
              <h3 className="text-lg font-semibold text-text-primary mb-2">No exports yet</h3>
              <p className="text-text-muted">
                Generate your first export using the form above
              </p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
