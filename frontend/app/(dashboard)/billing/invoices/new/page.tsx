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
  Calendar,
  Plus,
  Trash2,
  FileText,
  Search,
  DollarSign,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";
import { format, addDays } from "date-fns";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useCreateInvoice } from "@/lib/hooks/api/use-billing";
import { useTenants } from "@/lib/hooks/api/use-tenants";

const lineItemSchema = z.object({
  description: z.string().min(1, "Description is required"),
  quantity: z.coerce.number().min(1, "Quantity must be at least 1"),
  unitPrice: z.coerce.number().min(0, "Price must be positive"),
});

const createInvoiceSchema = z.object({
  customerId: z.string().min(1, "Tenant is required"),
  lineItems: z.array(lineItemSchema).min(1, "At least one line item is required"),
  dueDate: z.string().min(1, "Due date is required"),
  notes: z.string().optional(),
});

type CreateInvoiceFormData = z.infer<typeof createInvoiceSchema>;

const dueDateOptions = [
  { value: "7", label: "Net 7 (Due in 7 days)" },
  { value: "14", label: "Net 14 (Due in 14 days)" },
  { value: "30", label: "Net 30 (Due in 30 days)" },
  { value: "60", label: "Net 60 (Due in 60 days)" },
  { value: "custom", label: "Custom date" },
];

export default function NewInvoicePage() {
  const router = useRouter();
  const { toast } = useToast();
  const createInvoice = useCreateInvoice();

  const [tenantSearch, setTenantSearch] = useState("");
  const [showTenantDropdown, setShowTenantDropdown] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<{ id: string; name: string; slug: string } | null>(null);
  const [dueDateOption, setDueDateOption] = useState("30");
  const [customDueDate, setCustomDueDate] = useState("");

  // Fetch tenants for search
  const { data: tenantsData } = useTenants({ search: tenantSearch, pageSize: 10 });
  const tenants = tenantsData?.items || [];

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
    setValue,
    watch,
  } = useForm<CreateInvoiceFormData>({
    resolver: zodResolver(createInvoiceSchema),
    defaultValues: {
      customerId: "",
      lineItems: [{ description: "", quantity: 1, unitPrice: 0 }],
      dueDate: format(addDays(new Date(), 30), "yyyy-MM-dd"),
      notes: "",
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
  };

  const handleDueDateChange = (value: string) => {
    setDueDateOption(value);
    if (value !== "custom") {
      const days = parseInt(value, 10);
      const newDate = format(addDays(new Date(), days), "yyyy-MM-dd");
      setValue("dueDate", newDate);
    }
  };

  const handleCustomDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCustomDueDate(e.target.value);
    setValue("dueDate", e.target.value);
  };

  const onSubmit = async (data: CreateInvoiceFormData) => {
    try {
      const result = await createInvoice.mutateAsync({
        customerId: data.customerId,
        items: data.lineItems.map((item) => ({
          description: item.description,
          quantity: item.quantity,
          unitPrice: Math.round(item.unitPrice * 100), // Convert to cents
        })),
        dueDate: data.dueDate,
        notes: data.notes,
      });

      toast({
        title: "Invoice created",
        description: `Invoice has been created successfully.`,
      });

      router.push(`/billing/invoices/${result.id}`);
    } catch {
      toast({
        title: "Error",
        description: "Failed to create invoice. Please try again.",
        variant: "error",
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Create Invoice"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Invoices", href: "/billing/invoices" },
          { label: "Create Invoice" },
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
        {/* Tenant Selection */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
              <User className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Tenant</h3>
              <p className="text-sm text-text-muted">Select the tenant for this invoice</p>
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
                    placeholder="Search tenants by name..."
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
                    <p className="text-sm text-text-muted">No tenants found</p>
                  </div>
                )}
              </>
            )}
            {errors.customerId && (
              <p className="text-xs text-status-error mt-1">{errors.customerId.message}</p>
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
                <h3 className="text-lg font-semibold text-text-primary">Line Items</h3>
                <p className="text-sm text-text-muted">Add products or services to invoice</p>
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
                <div className="flex justify-between text-sm">
                  <span className="text-text-muted">Subtotal</span>
                  <span className="font-medium text-text-primary tabular-nums">
                    ${subtotal.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-lg font-semibold pt-2 border-t border-border">
                  <span className="text-text-primary">Total</span>
                  <span className="text-text-primary tabular-nums">${subtotal.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Invoice Details */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-status-info" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Invoice Details</h3>
              <p className="text-sm text-text-muted">Payment terms and additional notes</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Payment Terms <span className="text-status-error">*</span>
              </label>
              <Select
                value={dueDateOption}
                onValueChange={handleDueDateChange}
                options={dueDateOptions}
                placeholder="Select payment terms"
              />
              {dueDateOption === "custom" && (
                <div className="mt-2">
                  <Input
                    type="date"
                    value={customDueDate}
                    onChange={handleCustomDateChange}
                    min={format(new Date(), "yyyy-MM-dd")}
                    className={cn(errors.dueDate && "border-status-error")}
                  />
                </div>
              )}
              {errors.dueDate && (
                <p className="text-xs text-status-error mt-1">{errors.dueDate.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Due Date
              </label>
              <div className="h-10 flex items-center px-3 bg-surface-overlay rounded-lg border border-border">
                <span className="text-text-primary">
                  {watch("dueDate")
                    ? format(new Date(watch("dueDate")), "MMMM d, yyyy")
                    : "Select payment terms"}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              <FileText className="w-4 h-4 inline mr-1" />
              Notes (Optional)
            </label>
            <textarea
              {...register("notes")}
              placeholder="Add any additional notes or payment instructions..."
              rows={3}
              className="w-full px-3 py-2 bg-surface-overlay border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent resize-none"
            />
          </div>
        </Card>

        {/* Summary & Actions */}
        <Card className="p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="text-sm text-text-muted">Invoice Total</p>
              <p className="text-2xl font-semibold text-text-primary">${subtotal.toFixed(2)}</p>
            </div>
            <div className="flex items-center gap-3">
              <Button type="button" variant="ghost" onClick={() => router.back()}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="outline"
                disabled={isSubmitting || createInvoice.isPending}
              >
                Save as Draft
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting || createInvoice.isPending}
                className="shadow-glow-sm hover:shadow-glow"
              >
                {isSubmitting || createInvoice.isPending ? "Creating..." : "Create & Send"}
              </Button>
            </div>
          </div>
        </Card>
      </form>
    </div>
  );
}
