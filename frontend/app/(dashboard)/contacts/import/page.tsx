"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft, Upload, FileSpreadsheet, AlertCircle } from "lucide-react";
import { Button, Card } from "@dotmac/core";

import { PageHeader } from "@/components/shared/page-header";

export default function ImportContactsPage() {
  const router = useRouter();

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Import Contacts"
        breadcrumbs={[{ label: "Contacts", href: "/contacts" }, { label: "Import" }]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      {/* Coming Soon Notice */}
      <Card className="p-8">
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-full bg-status-warning/15 flex items-center justify-center mb-6">
            <AlertCircle className="w-8 h-8 text-status-warning" />
          </div>
          <h2 className="text-xl font-semibold text-text-primary mb-2">
            Import Feature Coming Soon
          </h2>
          <p className="text-text-muted max-w-md mb-8">
            The contact import feature is currently under development. Soon you&apos;ll be able to
            import contacts from CSV, Excel, and other formats.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-md">
            <div className="p-4 rounded-lg border border-border-default bg-surface-secondary">
              <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center mb-3 mx-auto">
                <FileSpreadsheet className="w-5 h-5 text-accent" />
              </div>
              <h3 className="text-sm font-medium text-text-primary mb-1">CSV Import</h3>
              <p className="text-xs text-text-muted">
                Import contacts from comma-separated value files
              </p>
            </div>

            <div className="p-4 rounded-lg border border-border-default bg-surface-secondary">
              <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center mb-3 mx-auto">
                <Upload className="w-5 h-5 text-status-success" />
              </div>
              <h3 className="text-sm font-medium text-text-primary mb-1">Excel Import</h3>
              <p className="text-xs text-text-muted">Upload .xlsx or .xls spreadsheet files</p>
            </div>
          </div>

          <div className="mt-8">
            <Button variant="outline" onClick={() => router.push("/contacts/new")}>
              Add Contact Manually
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
