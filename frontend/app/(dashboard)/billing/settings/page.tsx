"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  Receipt,
  CreditCard,
  FileText,
  Bell,
  Save,
  Plus,
  Trash2,
  Check,
  Palette,
} from "lucide-react";
import { Button, Card, Input, Select } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import {
  useBillingSettings,
  useUpdateCompanySettings,
  useUpdateTaxSettings,
  useUpdatePaymentSettings,
  useUpdateNotificationSettings,
  useInvoiceTemplates,
  useUpdateInvoiceTemplate,
  type CompanySettings,
  type TaxSettings,
  type PaymentSettings,
  type NotificationSettings,
  type InvoiceTemplate,
} from "@/lib/hooks/api/use-billing";
import { getCssHslColorHex } from "@/lib/theme/color-utils";

const DEFAULT_FALLBACK_COLOR = "#000000";

type SettingsTab = "company" | "tax" | "payment" | "templates" | "notifications";

const tabs: Array<{ id: SettingsTab; label: string; icon: typeof Building2 }> = [
  { id: "company", label: "Company", icon: Building2 },
  { id: "tax", label: "Tax", icon: Receipt },
  { id: "payment", label: "Payment", icon: CreditCard },
  { id: "templates", label: "Invoice Templates", icon: FileText },
  { id: "notifications", label: "Notifications", icon: Bell },
];

export default function BillingSettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("company");
  const { data: settings, isLoading } = useBillingSettings();

  if (isLoading) {
    return <SettingsPageSkeleton />;
  }

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Billing Settings"
        breadcrumbs={[
          { label: "Billing", href: "/billing" },
          { label: "Settings" },
        ]}
        actions={
          <Link href="/billing">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Billing
            </Button>
          </Link>
        }
      />

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border pb-px overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap",
                activeTab === tab.id
                  ? "bg-surface-overlay text-text-primary border-b-2 border-accent"
                  : "text-text-muted hover:text-text-secondary hover:bg-surface-overlay/50"
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === "company" && settings && (
          <CompanySettingsTab initialData={settings.company} />
        )}
        {activeTab === "tax" && settings && (
          <TaxSettingsTab initialData={settings.tax} />
        )}
        {activeTab === "payment" && settings && (
          <PaymentSettingsTab initialData={settings.payment} />
        )}
        {activeTab === "templates" && <InvoiceTemplatesTab />}
        {activeTab === "notifications" && settings && (
          <NotificationsTab initialData={settings.notifications} />
        )}
      </div>
    </div>
  );
}

function CompanySettingsTab({ initialData }: { initialData: CompanySettings }) {
  const { toast } = useToast();
  const updateSettings = useUpdateCompanySettings();
  const [formData, setFormData] = useState(initialData);

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      toast({
        title: "Settings saved",
        description: "Company settings have been updated.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to save settings.",
        variant: "error",
      });
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-accent-subtle flex items-center justify-center">
          <Building2 className="w-5 h-5 text-accent" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-text-primary">Company Information</h3>
          <p className="text-sm text-text-muted">Details shown on invoices and receipts</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            Company Name <span className="text-status-error">*</span>
          </label>
          <Input
            value={formData.companyName}
            onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            Legal Name
          </label>
          <Input
            value={formData.legalName || ""}
            onChange={(e) => setFormData({ ...formData, legalName: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            Tax ID
          </label>
          <Input
            value={formData.taxId || ""}
            onChange={(e) => setFormData({ ...formData, taxId: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            Email <span className="text-status-error">*</span>
          </label>
          <Input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            Phone
          </label>
          <Input
            value={formData.phone || ""}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            Website
          </label>
          <Input
            value={formData.website || ""}
            onChange={(e) => setFormData({ ...formData, website: e.target.value })}
          />
        </div>

        {/* Address */}
        <div className="md:col-span-2">
          <h4 className="text-sm font-semibold text-text-primary mb-4 mt-4">Address</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Street
              </label>
              <Input
                value={formData.address.street}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    address: { ...formData.address, street: e.target.value },
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                City
              </label>
              <Input
                value={formData.address.city}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    address: { ...formData.address, city: e.target.value },
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                State / Province
              </label>
              <Input
                value={formData.address.state}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    address: { ...formData.address, state: e.target.value },
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Postal Code
              </label>
              <Input
                value={formData.address.postalCode}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    address: { ...formData.address, postalCode: e.target.value },
                  })
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1.5">
                Country
              </label>
              <Input
                value={formData.address.country}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    address: { ...formData.address, country: e.target.value },
                  })
                }
              />
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-border flex justify-end">
        <Button
          onClick={handleSave}
          disabled={updateSettings.isPending}
          className="shadow-glow-sm hover:shadow-glow"
        >
          {updateSettings.isPending ? (
            "Saving..."
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </Card>
  );
}

function TaxSettingsTab({ initialData }: { initialData: TaxSettings }) {
  const { toast } = useToast();
  const updateSettings = useUpdateTaxSettings();
  const [formData, setFormData] = useState(initialData);

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      toast({
        title: "Settings saved",
        description: "Tax settings have been updated.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to save settings.",
        variant: "error",
      });
    }
  };

  const addCustomRate = () => {
    setFormData({
      ...formData,
      customTaxRates: [
        ...formData.customTaxRates,
        { id: Date.now().toString(), name: "", rate: 0 },
      ],
    });
  };

  const removeCustomRate = (id: string) => {
    setFormData({
      ...formData,
      customTaxRates: formData.customTaxRates.filter((r) => r.id !== id),
    });
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-status-warning/15 flex items-center justify-center">
          <Receipt className="w-5 h-5 text-status-warning" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-text-primary">Tax Configuration</h3>
          <p className="text-sm text-text-muted">Configure tax rates and rules</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Tax Enabled Toggle */}
        <div className="flex items-center justify-between p-4 bg-surface-overlay rounded-lg">
          <div>
            <p className="font-medium text-text-primary">Enable Tax Calculation</p>
            <p className="text-sm text-text-muted">Automatically calculate tax on invoices</p>
          </div>
          <button
            onClick={() => setFormData({ ...formData, taxEnabled: !formData.taxEnabled })}
            className={cn(
              "w-12 h-6 rounded-full transition-colors relative",
              formData.taxEnabled ? "bg-accent" : "bg-surface-overlay border border-border"
            )}
          >
            <span
              className={cn(
                "absolute top-0.5 w-5 h-5 rounded-full bg-surface shadow transition-transform",
                formData.taxEnabled ? "translate-x-6" : "translate-x-0.5"
              )}
            />
          </button>
        </div>

        {formData.taxEnabled && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Default Tax Rate (%)
                </label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  step={0.01}
                  value={formData.defaultTaxRate}
                  onChange={(e) =>
                    setFormData({ ...formData, defaultTaxRate: parseFloat(e.target.value) || 0 })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1.5">
                  Tax Region
                </label>
                <Input
                  value={formData.taxRegion}
                  onChange={(e) => setFormData({ ...formData, taxRegion: e.target.value })}
                />
              </div>
              <div className="flex items-center gap-3 pt-6">
                <input
                  type="checkbox"
                  id="taxInclusive"
                  checked={formData.taxInclusive}
                  onChange={(e) => setFormData({ ...formData, taxInclusive: e.target.checked })}
                  className="w-4 h-4 rounded border-border"
                />
                <label htmlFor="taxInclusive" className="text-sm text-text-primary">
                  Prices include tax
                </label>
              </div>
            </div>

            {/* Custom Tax Rates */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-semibold text-text-primary">Custom Tax Rates</h4>
                <Button type="button" variant="outline" size="sm" onClick={addCustomRate}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Rate
                </Button>
              </div>
              {formData.customTaxRates.length > 0 ? (
                <div className="space-y-3">
                  {formData.customTaxRates.map((rate) => (
                    <div
                      key={rate.id}
                      className="flex items-center gap-4 p-4 bg-surface-overlay rounded-lg"
                    >
                      <Input
                        placeholder="Rate name"
                        value={rate.name}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            customTaxRates: formData.customTaxRates.map((r) =>
                              r.id === rate.id ? { ...r, name: e.target.value } : r
                            ),
                          })
                        }
                        className="flex-1"
                      />
                      <Input
                        type="number"
                        placeholder="Rate %"
                        value={rate.rate}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            customTaxRates: formData.customTaxRates.map((r) =>
                              r.id === rate.id ? { ...r, rate: parseFloat(e.target.value) || 0 } : r
                            ),
                          })
                        }
                        className="w-24"
                      />
                      <Input
                        placeholder="Region (optional)"
                        value={rate.region || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            customTaxRates: formData.customTaxRates.map((r) =>
                              r.id === rate.id ? { ...r, region: e.target.value } : r
                            ),
                          })
                        }
                        className="w-32"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeCustomRate(rate.id)}
                        className="text-status-error hover:text-status-error"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-text-muted text-center py-8">
                  No custom tax rates configured
                </p>
              )}
            </div>
          </>
        )}
      </div>

      <div className="mt-6 pt-6 border-t border-border flex justify-end">
        <Button
          onClick={handleSave}
          disabled={updateSettings.isPending}
          className="shadow-glow-sm hover:shadow-glow"
        >
          {updateSettings.isPending ? (
            "Saving..."
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </Card>
  );
}

function PaymentSettingsTab({ initialData }: { initialData: PaymentSettings }) {
  const { toast } = useToast();
  const updateSettings = useUpdatePaymentSettings();
  const [formData, setFormData] = useState(initialData);

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      toast({
        title: "Settings saved",
        description: "Payment settings have been updated.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to save settings.",
        variant: "error",
      });
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-status-success/15 flex items-center justify-center">
          <CreditCard className="w-5 h-5 text-status-success" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-text-primary">Payment Configuration</h3>
          <p className="text-sm text-text-muted">Configure payment methods and retry behavior</p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Default Currency
            </label>
            <Select
              value={formData.defaultCurrency}
              onChange={(e) => setFormData({ ...formData, defaultCurrency: e.target.value })}
            >
              <option value="USD">USD - US Dollar</option>
              <option value="EUR">EUR - Euro</option>
              <option value="GBP">GBP - British Pound</option>
              <option value="CAD">CAD - Canadian Dollar</option>
              <option value="AUD">AUD - Australian Dollar</option>
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Invoice Due Days
            </label>
            <Input
              type="number"
              min={1}
              value={formData.invoiceDueDays}
              onChange={(e) =>
                setFormData({ ...formData, invoiceDueDays: parseInt(e.target.value) || 30 })
              }
            />
            <p className="text-xs text-text-muted mt-1">Days until invoice is due</p>
          </div>
        </div>

        {/* Payment Methods */}
        <div>
          <h4 className="text-sm font-semibold text-text-primary mb-4">Payment Methods</h4>
          <div className="space-y-3">
            {formData.paymentMethods.map((method) => (
              <div
                key={method.id}
                className="flex items-center justify-between p-4 bg-surface-overlay rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-text-primary capitalize">
                    {method.type.replace("_", " ")}
                  </span>
                  {method.isDefault && (
                    <span className="text-xs px-2 py-0.5 bg-accent-subtle text-accent rounded">
                      Default
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() =>
                      setFormData({
                        ...formData,
                        paymentMethods: formData.paymentMethods.map((m) =>
                          m.id === method.id ? { ...m, enabled: !m.enabled } : m
                        ),
                      })
                    }
                    className={cn(
                      "w-10 h-5 rounded-full transition-colors relative",
                      method.enabled ? "bg-status-success" : "bg-surface-overlay border border-border"
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-0.5 w-4 h-4 rounded-full bg-surface shadow transition-transform",
                        method.enabled ? "translate-x-5" : "translate-x-0.5"
                      )}
                    />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Auto Retry */}
        <div>
          <h4 className="text-sm font-semibold text-text-primary mb-4">Payment Retry</h4>
          <div className="p-4 bg-surface-overlay rounded-lg space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-text-primary">Auto-retry failed payments</p>
                <p className="text-sm text-text-muted">Automatically retry failed payment attempts</p>
              </div>
              <button
                onClick={() =>
                  setFormData({
                    ...formData,
                    autoRetry: { ...formData.autoRetry, enabled: !formData.autoRetry.enabled },
                  })
                }
                className={cn(
                  "w-12 h-6 rounded-full transition-colors relative",
                  formData.autoRetry.enabled ? "bg-accent" : "bg-surface-overlay border border-border"
                )}
              >
                <span
                  className={cn(
                    "absolute top-0.5 w-5 h-5 rounded-full bg-surface shadow transition-transform",
                    formData.autoRetry.enabled ? "translate-x-6" : "translate-x-0.5"
                  )}
                />
              </button>
            </div>
            {formData.autoRetry.enabled && (
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Max Attempts
                  </label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    value={formData.autoRetry.maxAttempts}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        autoRetry: {
                          ...formData.autoRetry,
                          maxAttempts: parseInt(e.target.value) || 3,
                        },
                      })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Retry Interval (days)
                  </label>
                  <Input
                    type="number"
                    min={1}
                    value={formData.autoRetry.intervalDays}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        autoRetry: {
                          ...formData.autoRetry,
                          intervalDays: parseInt(e.target.value) || 3,
                        },
                      })
                    }
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-border flex justify-end">
        <Button
          onClick={handleSave}
          disabled={updateSettings.isPending}
          className="shadow-glow-sm hover:shadow-glow"
        >
          {updateSettings.isPending ? (
            "Saving..."
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </Card>
  );
}

function InvoiceTemplatesTab() {
  const { toast } = useToast();
  const { data: templates, isLoading } = useInvoiceTemplates();
  const updateTemplate = useUpdateInvoiceTemplate();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<InvoiceTemplate>>({});
  const [defaultPrimaryColor, setDefaultPrimaryColor] = useState(
    DEFAULT_FALLBACK_COLOR
  );

  useEffect(() => {
    setDefaultPrimaryColor(getCssHslColorHex("--color-accent", DEFAULT_FALLBACK_COLOR));
  }, []);

  if (isLoading) {
    return (
      <Card className="p-6 animate-pulse">
        <div className="h-48 bg-surface-overlay rounded" />
      </Card>
    );
  }

  const handleEdit = (template: InvoiceTemplate) => {
    setEditingId(template.id);
    setEditData(template);
  };

  const handleSave = async () => {
    if (!editingId) return;

    try {
      await updateTemplate.mutateAsync({ id: editingId, data: editData });
      toast({
        title: "Template saved",
        description: "Invoice template has been updated.",
      });
      setEditingId(null);
      setEditData({});
    } catch {
      toast({
        title: "Error",
        description: "Failed to save template.",
        variant: "error",
      });
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditData({});
  };

  return (
    <div className="space-y-4">
      {templates?.map((template) => (
        <Card key={template.id} className="p-6">
          {editingId === template.id ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Template Name
                  </label>
                  <Input
                    value={editData.name || ""}
                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Logo Position
                  </label>
                  <Select
                    value={editData.logoPosition || "left"}
                    onChange={(e) =>
                      setEditData({
                        ...editData,
                        logoPosition: e.target.value as "left" | "center" | "right",
                      })
                    }
                  >
                    <option value="left">Left</option>
                    <option value="center">Center</option>
                    <option value="right">Right</option>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Primary Color
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={editData.primaryColor || defaultPrimaryColor}
                      onChange={(e) => setEditData({ ...editData, primaryColor: e.target.value })}
                      className="w-10 h-10 rounded border border-border"
                    />
                    <Input
                      value={editData.primaryColor || ""}
                      onChange={(e) => setEditData({ ...editData, primaryColor: e.target.value })}
                      className="flex-1"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-6 pt-6">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editData.showTaxBreakdown ?? true}
                      onChange={(e) =>
                        setEditData({ ...editData, showTaxBreakdown: e.target.checked })
                      }
                      className="w-4 h-4 rounded border-border"
                    />
                    <span className="text-sm text-text-primary">Show tax breakdown</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={editData.showPaymentInstructions ?? true}
                      onChange={(e) =>
                        setEditData({ ...editData, showPaymentInstructions: e.target.checked })
                      }
                      className="w-4 h-4 rounded border-border"
                    />
                    <span className="text-sm text-text-primary">Show payment instructions</span>
                  </label>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Footer Text
                  </label>
                  <Input
                    value={editData.footerText || ""}
                    onChange={(e) => setEditData({ ...editData, footerText: e.target.value })}
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-text-primary mb-1.5">
                    Terms & Conditions
                  </label>
                  <textarea
                    value={editData.termsAndConditions || ""}
                    onChange={(e) =>
                      setEditData({ ...editData, termsAndConditions: e.target.value })
                    }
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-transparent text-text-primary resize-none focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3">
                <Button variant="ghost" onClick={handleCancel}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={updateTemplate.isPending}
                  className="shadow-glow-sm hover:shadow-glow"
                >
                  {updateTemplate.isPending ? "Saving..." : "Save Template"}
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: template.primaryColor + "20" }}
                >
                  <Palette className="w-5 h-5" style={{ color: template.primaryColor }} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-text-primary">{template.name}</span>
                    {template.isDefault && (
                      <span className="text-xs px-2 py-0.5 bg-accent-subtle text-accent rounded">
                        Default
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-text-muted">
                    Logo: {template.logoPosition} | Color: {template.primaryColor}
                  </p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={() => handleEdit(template)}>
                Edit
              </Button>
            </div>
          )}
        </Card>
      ))}
    </div>
  );
}

function NotificationsTab({ initialData }: { initialData: NotificationSettings }) {
  const { toast } = useToast();
  const updateSettings = useUpdateNotificationSettings();
  const [formData, setFormData] = useState(initialData);

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(formData);
      toast({
        title: "Settings saved",
        description: "Notification settings have been updated.",
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to save settings.",
        variant: "error",
      });
    }
  };

  const notificationItems = [
    { key: "invoiceCreated", label: "Invoice Created", desc: "When a new invoice is generated" },
    { key: "invoiceSent", label: "Invoice Sent", desc: "When an invoice is sent to customer" },
    { key: "paymentReceived", label: "Payment Received", desc: "When a payment is received" },
    { key: "paymentFailed", label: "Payment Failed", desc: "When a payment attempt fails" },
    { key: "subscriptionRenewing", label: "Subscription Renewing", desc: "Before a subscription renews" },
    { key: "subscriptionCancelled", label: "Subscription Cancelled", desc: "When a subscription is cancelled" },
  ] as const;

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-status-info/15 flex items-center justify-center">
          <Bell className="w-5 h-5 text-status-info" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-text-primary">Email Notifications</h3>
          <p className="text-sm text-text-muted">Configure when to send email notifications</p>
        </div>
      </div>

      <div className="space-y-3 mb-8">
        {notificationItems.map((item) => (
          <div
            key={item.key}
            className="flex items-center justify-between p-4 bg-surface-overlay rounded-lg"
          >
            <div>
              <p className="font-medium text-text-primary">{item.label}</p>
              <p className="text-sm text-text-muted">{item.desc}</p>
            </div>
            <button
              onClick={() =>
                setFormData({
                  ...formData,
                  emailNotifications: {
                    ...formData.emailNotifications,
                    [item.key]: !formData.emailNotifications[item.key],
                  },
                })
              }
              className={cn(
                "w-10 h-5 rounded-full transition-colors relative",
                formData.emailNotifications[item.key]
                  ? "bg-status-success"
                  : "bg-surface-overlay border border-border"
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 w-4 h-4 rounded-full bg-surface shadow transition-transform",
                  formData.emailNotifications[item.key] ? "translate-x-5" : "translate-x-0.5"
                )}
              />
            </button>
          </div>
        ))}
      </div>

      {/* Reminder Schedule */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-text-primary mb-4">Payment Reminder Schedule</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-surface-overlay rounded-lg">
            <p className="text-sm font-medium text-text-primary mb-2">Before Due Date</p>
            <p className="text-xs text-text-muted mb-3">Days before due date to send reminders</p>
            <div className="flex flex-wrap gap-2">
              {formData.reminderSchedule.beforeDue.map((days, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-accent-subtle text-accent text-sm rounded-full"
                >
                  {days} days
                </span>
              ))}
            </div>
          </div>
          <div className="p-4 bg-surface-overlay rounded-lg">
            <p className="text-sm font-medium text-text-primary mb-2">After Due Date</p>
            <p className="text-xs text-text-muted mb-3">Days after due date to send reminders</p>
            <div className="flex flex-wrap gap-2">
              {formData.reminderSchedule.afterDue.map((days, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-status-warning/15 text-status-warning text-sm rounded-full"
                >
                  {days} days
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="pt-6 border-t border-border flex justify-end">
        <Button
          onClick={handleSave}
          disabled={updateSettings.isPending}
          className="shadow-glow-sm hover:shadow-glow"
        >
          {updateSettings.isPending ? (
            "Saving..."
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </Card>
  );
}

function SettingsPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-4 w-32 bg-surface-overlay rounded mb-2" />
          <div className="h-8 w-48 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-32 bg-surface-overlay rounded" />
      </div>
      <div className="flex gap-2 border-b border-border pb-px">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-10 w-32 bg-surface-overlay rounded" />
        ))}
      </div>
      <div className="card p-6">
        <div className="h-96 bg-surface-overlay rounded" />
      </div>
    </div>
  );
}
