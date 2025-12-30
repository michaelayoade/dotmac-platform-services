"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  ArrowLeft,
  User,
  Receipt,
  Plus,
  Trash2,
  FileText,
  Search,
  DollarSign,
  Link as LinkIcon,
} from "lucide-react";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useCreateCreditNote } from "@/lib/hooks/api/use-billing";
import { useTenants } from "@/lib/hooks/api/use-tenants";
import { useInvoices } from "@/lib/hooks/api/use-billing";

const lineItemSchema = z.object({
  description: z.string().min(1, "Description is required"),
  quantity: z.coerce.number().min(1, "Quantity must be at least 1"),
  unitPrice: z.coerce.number().min(0, "Price must be positive"),
});

const createCreditNoteSchema = z.object({
  customerId: z.string().min(1, "Customer is required"),
  invoiceId: z.string().optional(),
  reason: z.string().min(1, "Reason is required"),
  lineItems: z.array(lineItemSchema).min(1, "At least one line item is required"),
});

type CreateCreditNoteFormData = z.infer<typeof createCreditNoteSchema>;

export default function NewCreditNotePage() {
  const router = useRouter();
  const { toast } = useToast();
  const createCreditNote = useCreateCreditNote();

  const [tenantSearch, setTenantSearch] = useState("");
  const [showTenantDropdown, setShowTenantDropdown] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<{ id: string; name: string; slug: string } | null>(null);
  const [showInvoiceDropdown, setShowInvoiceDropdown] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<{ id: string; number: string; amount: number } | null>(null);

  // Fetch tenants for search
  const { data: tenantsData } = useTenants({ search: tenantSearch, pageSize: 10 });
  const tenants = tenantsData?.items || [];

  // Fetch invoices for selected tenant
  const { data: invoicesData } = useInvoices({
    customerId: selectedTenant?.id,
    pageSize: 20,
  });
  const availableInvoices = invoicesData?.items?.filter(
    (inv) => inv.status === "paid" || inv.status === "pending"
  ) || [];

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateCreditNoteFormData>({
    resolver: zodResolver(createCreditNoteSchema),
    defaultValues: {
      customerId: "",
      invoiceId: "",
      reason: "",
      lineItems: [{ description: "", quantity: 1, unitPrice: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "lineItems",
  });

  const lineItems = watch("lineItems");

  // Calculate totals
  const subtotal = lineItems.reduce((sum, item) => {
    const qty = Number(item.quantity) || 0;
    const price = Number(item.unitPrice) || 0;
    return sum + qty * price;
  }, 0);

  const handleSelectTenant = (tenant: { id: string; name: string; slug: string }) => {
    setSelectedTenant(tenant);
    setValue("customerId", tenant.id);
    setShowTenantDropdown(false);
    setTenantSearch("");
    // Clear selected invoice when tenant changes
    setSelectedInvoice(null);
    setValue("invoiceId", "");
  };

  const handleSelectInvoice = (invoice: { id: string; number: string; amount: number }) => {
    setSelectedInvoice(invoice);
    setValue("invoiceId", invoice.id);
    setShowInvoiceDropdown(false);
  };

  const onSubmit = async (data: CreateCreditNoteFormData) => {
    try {
      const result = await createCreditNote.mutateAsync({
        customerId: data.customerId,
        invoiceId: data.invoiceId || undefined,
        reason: data.reason,
        lineItems: data.lineItems.map((item) => ({
          description: item.description,
          quantity: item.quantity,
          unitPrice: Math.round(item.unitPrice * 100), // Convert to cents
        })),
      });

      toast({
        title: "Credit note created",
        description: "Credit note has been created successfully.",
      });

      router.push(`/billing/credit-notes/${result.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to create credit note. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Create Credit Note"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Credit Notes", href: "/billing/credit-notes" },
          { label: "Create Credit Note" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Customer Selection */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <User className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Customer</h3>
              <p className="text-sm text-text-muted">Select the customer for this credit note</p>
            </div>
          </div>

          <div className="relative">
            {selectedTenant ? (
              <div className="flex items-center justify-between p-4 bg-surface-overlay rounded-lg border border-border">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent/20 to-highlight/20 flex items-center justify-center text-sm font-semibold text-accent">
                    {selectedTenant.name.charAt(0)}
                  </div>
                  <div>
                    <p className="font-medium text-text-primary">{selectedTenant.name}</p>
                    <p className="text-sm text-text-muted">{selectedTenant.slug}</p>
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSelectedTenant(null);
                    setValue("customerId", "");
                    setSelectedInvoice(null);
                    setValue("invoiceId", "");
                  }}
                >
                  Change
                </Button>
              </div>
            ) : (
              <>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <Input
                    value={tenantSearch}
                    onChange={(e) => {
                      setTenantSearch(e.target.value);
                      setShowTenantDropdown(true);
                    }}
                    onFocus={() => setShowTenantDropdown(true)}
                    placeholder="Search customers by name..."
                    className={cn("pl-10", errors.customerId && "border-status-error")}
                  />
                </div>

                {showTenantDropdown && tenants.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-surface-elevated border border-border rounded-lg shadow-lg max-h-64 overflow-auto">
                    {tenants.map((tenant) => (
                      <button
                        key={tenant.id}
                        type="button"
                        onClick={() => handleSelectTenant(tenant)}
                        className="w-full flex items-center gap-3 p-3 hover:bg-surface-overlay transition-colors text-left"
                      >
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent/20 to-highlight/20 flex items-center justify-center text-xs font-semibold text-accent">
                          {tenant.name.charAt(0)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-text-primary">{tenant.name}</p>
                          <p className="text-xs text-text-muted">{tenant.slug}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {showTenantDropdown && tenantSearch && tenants.length === 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-surface-elevated border border-border rounded-lg shadow-lg p-4 text-center">
                    <p className="text-sm text-text-muted">No customers found</p>
                  </div>
                )}
              </>
            )}
            {errors.customerId && (
              <p className="text-xs text-status-error mt-1">{errors.customerId.message}</p>
            )}
          </div>
        </Card>

        {/* Related Invoice (Optional) */}
        {selectedTenant && (
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
                <LinkIcon className="w-5 h-5 text-status-info" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Related Invoice</h3>
                <p className="text-sm text-text-muted">Optionally link to an existing invoice</p>
              </div>
            </div>

            <div className="relative">
              {selectedInvoice ? (
                <div className="flex items-center justify-between p-4 bg-surface-overlay rounded-lg border border-border">
                  <div className="flex items-center gap-3">
                    <Receipt className="w-5 h-5 text-text-muted" />
                    <div>
                      <p className="font-mono text-sm font-medium text-text-primary">
                        {selectedInvoice.number}
                      </p>
                      <p className="text-sm text-text-muted">
                        ${(selectedInvoice.amount / 100).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedInvoice(null);
                      setValue("invoiceId", "");
                    }}
                  >
                    Remove
                  </Button>
                </div>
              ) : (
                <>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowInvoiceDropdown(!showInvoiceDropdown)}
                    className="w-full justify-start"
                  >
                    <Receipt className="w-4 h-4 mr-2 text-text-muted" />
                    <span className="text-text-muted">Select related invoice (optional)</span>
                  </Button>

                  {showInvoiceDropdown && availableInvoices.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-surface-elevated border border-border rounded-lg shadow-lg max-h-64 overflow-auto">
                      {availableInvoices.map((invoice) => (
                        <button
                          key={invoice.id}
                          type="button"
                          onClick={() => handleSelectInvoice({
                            id: invoice.id,
                            number: invoice.number,
                            amount: invoice.amount,
                          })}
                          className="w-full flex items-center justify-between p-3 hover:bg-surface-overlay transition-colors text-left"
                        >
                          <div>
                            <p className="font-mono text-sm font-medium text-text-primary">
                              {invoice.number}
                            </p>
                            <p className="text-xs text-text-muted">
                              {invoice.customer?.name}
                            </p>
                          </div>
                          <span className="text-sm font-medium text-text-primary tabular-nums">
                            ${(invoice.amount / 100).toLocaleString()}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}

                  {showInvoiceDropdown && availableInvoices.length === 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-surface-elevated border border-border rounded-lg shadow-lg p-4 text-center">
                      <p className="text-sm text-text-muted">No invoices available for this customer</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </Card>
        )}

        {/* Reason */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
              <FileText className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Reason</h3>
              <p className="text-sm text-text-muted">Explain why this credit note is being issued</p>
            </div>
          </div>

          <div>
            <textarea
              {...register("reason")}
              placeholder="e.g., Product returned, Service not delivered, Billing error..."
              rows={3}
              className={cn(
                "w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent resize-none",
                errors.reason && "border-status-error"
              )}
            />
            {errors.reason && (
              <p className="text-xs text-status-error mt-1">{errors.reason.message}</p>
            )}
          </div>
        </Card>

        {/* Line Items */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-highlight-subtle flex items-center justify-center">
                <Receipt className="w-5 h-5 text-highlight" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Credit Items</h3>
                <p className="text-sm text-text-muted">Items to credit back to the customer</p>
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ description: "", quantity: 1, unitPrice: 0 })}
            >
              <Plus className="w-4 h-4 mr-1" />
              Add Item
            </Button>
          </div>

          {/* Table Header */}
          <div className="grid grid-cols-12 gap-4 mb-2 text-sm font-medium text-text-muted px-2">
            <div className="col-span-5">Description</div>
            <div className="col-span-2 text-right">Quantity</div>
            <div className="col-span-2 text-right">Unit Price</div>
            <div className="col-span-2 text-right">Amount</div>
            <div className="col-span-1"></div>
          </div>

          {/* Line Items */}
          <div className="space-y-3">
            {fields.map((field, index) => {
              const qty = Number(lineItems[index]?.quantity) || 0;
              const price = Number(lineItems[index]?.unitPrice) || 0;
              const amount = qty * price;

              return (
                <div
                  key={field.id}
                  className="grid grid-cols-12 gap-4 items-start p-3 bg-surface-overlay rounded-lg"
                >
                  <div className="col-span-5">
                    <Input
                      {...register(`lineItems.${index}.description`)}
                      placeholder="Item description"
                      className={cn(
                        "bg-surface",
                        errors.lineItems?.[index]?.description && "border-status-error"
                      )}
                    />
                    {errors.lineItems?.[index]?.description && (
                      <p className="text-xs text-status-error mt-1">
                        {errors.lineItems[index]?.description?.message}
                      </p>
                    )}
                  </div>
                  <div className="col-span-2">
                    <Input
                      {...register(`lineItems.${index}.quantity`)}
                      type="number"
                      min="1"
                      className={cn(
                        "text-right bg-surface",
                        errors.lineItems?.[index]?.quantity && "border-status-error"
                      )}
                    />
                  </div>
                  <div className="col-span-2">
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                      <Input
                        {...register(`lineItems.${index}.unitPrice`)}
                        type="number"
                        min="0"
                        step="0.01"
                        className={cn(
                          "pl-8 text-right bg-surface",
                          errors.lineItems?.[index]?.unitPrice && "border-status-error"
                        )}
                      />
                    </div>
                  </div>
                  <div className="col-span-2 flex items-center justify-end h-10">
                    <span className="text-sm font-medium text-text-primary tabular-nums">
                      ${amount.toFixed(2)}
                    </span>
                  </div>
                  <div className="col-span-1 flex items-center justify-center h-10">
                    {fields.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => remove(index)}
                        className="text-text-muted hover:text-status-error"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {errors.lineItems?.message && (
            <p className="text-xs text-status-error mt-2">{errors.lineItems.message}</p>
          )}

          {/* Totals */}
          <div className="mt-6 pt-4 border-t border-border">
            <div className="flex justify-end">
              <div className="w-64 space-y-2">
                <div className="flex justify-between text-lg font-semibold pt-2 border-t border-border">
                  <span className="text-text-primary">Credit Total</span>
                  <span className="text-status-success tabular-nums">-${subtotal.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Summary & Actions */}
        <Card className="p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-sm text-text-muted">Credit Note Total</p>
              <p className="text-2xl font-semibold text-status-success">-${subtotal.toFixed(2)}</p>
            </div>
            <div className="flex items-center gap-3">
              <Button type="button" variant="ghost" onClick={() => router.back()}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting || createCreditNote.isPending}
                className="shadow-glow-sm hover:shadow-glow"
              >
                {isSubmitting || createCreditNote.isPending ? "Creating..." : "Create Credit Note"}
              </Button>
            </div>
          </div>
        </Card>
      </form>
    </div>
  );
}
