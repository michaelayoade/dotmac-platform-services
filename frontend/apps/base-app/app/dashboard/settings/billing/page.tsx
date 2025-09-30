'use client';

import { useState, useEffect } from 'react';
import {
  Building2,
  Receipt,
  CreditCard,
  Calculator,
  Bell,
  FileText,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle,
  ChevronRight,
  Globe,
  Mail,
  Phone,
  MapPin,
  Hash,
  Calendar,
  DollarSign,
  Percent,
  Clock,
  RefreshCw,
  Webhook,
  ToggleLeft,
  ToggleRight,
  Palette
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';

interface BillingSettings {
  company_info: {
    name: string;
    legal_name: string;
    tax_id: string;
    registration_number: string;
    address_line1: string;
    address_line2: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
    phone: string;
    email: string;
    website: string;
    logo_url: string;
    brand_color: string;
  };
  tax_settings: {
    calculate_tax: boolean;
    tax_inclusive_pricing: boolean;
    tax_registrations: Array<{ jurisdiction: string; registration_number: string }>;
    default_tax_rate: number;
    tax_provider: string;
  };
  payment_settings: {
    enabled_payment_methods: string[];
    default_currency: string;
    supported_currencies: string[];
    default_payment_terms: number;
    late_payment_fee: number;
    retry_failed_payments: boolean;
    max_retry_attempts: number;
    retry_interval_hours: number;
  };
  invoice_settings: {
    invoice_number_prefix: string;
    invoice_number_format: string;
    default_due_days: number;
    include_payment_instructions: boolean;
    payment_instructions: string;
    footer_text: string;
    terms_and_conditions: string;
    send_invoice_emails: boolean;
    send_payment_reminders: boolean;
    reminder_schedule_days: number[];
    logo_on_invoices: boolean;
    color_scheme: string;
  };
  notification_settings: {
    send_invoice_notifications: boolean;
    send_payment_confirmations: boolean;
    send_overdue_notices: boolean;
    send_receipt_emails: boolean;
    webhook_url: string;
    webhook_events: string[];
    webhook_secret: string;
  };
  features_enabled: {
    invoicing: boolean;
    payments: boolean;
    credit_notes: boolean;
    receipts: boolean;
    tax_calculation: boolean;
    webhooks: boolean;
    reporting: boolean;
  };
}

const defaultSettings: BillingSettings = {
  company_info: {
    name: '',
    legal_name: '',
    tax_id: '',
    registration_number: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'US',
    phone: '',
    email: '',
    website: '',
    logo_url: '',
    brand_color: '#0EA5E9'
  },
  tax_settings: {
    calculate_tax: true,
    tax_inclusive_pricing: false,
    tax_registrations: [],
    default_tax_rate: 0,
    tax_provider: ''
  },
  payment_settings: {
    enabled_payment_methods: ['card', 'bank_account'],
    default_currency: 'USD',
    supported_currencies: ['USD'],
    default_payment_terms: 30,
    late_payment_fee: 0,
    retry_failed_payments: true,
    max_retry_attempts: 3,
    retry_interval_hours: 24
  },
  invoice_settings: {
    invoice_number_prefix: 'INV',
    invoice_number_format: '{prefix}-{year}-{sequence:06d}',
    default_due_days: 30,
    include_payment_instructions: true,
    payment_instructions: '',
    footer_text: '',
    terms_and_conditions: '',
    send_invoice_emails: true,
    send_payment_reminders: true,
    reminder_schedule_days: [7, 3, 1],
    logo_on_invoices: true,
    color_scheme: '#0EA5E9'
  },
  notification_settings: {
    send_invoice_notifications: true,
    send_payment_confirmations: true,
    send_overdue_notices: true,
    send_receipt_emails: true,
    webhook_url: '',
    webhook_events: [],
    webhook_secret: ''
  },
  features_enabled: {
    invoicing: true,
    payments: true,
    credit_notes: true,
    receipts: true,
    tax_calculation: true,
    webhooks: true,
    reporting: true
  }
};

const tabs = [
  { id: 'company', label: 'Company', icon: Building2 },
  { id: 'invoice', label: 'Invoice & Numbering', icon: FileText },
  { id: 'payment', label: 'Payment', icon: CreditCard },
  { id: 'tax', label: 'Tax', icon: Calculator },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'features', label: 'Features', icon: ToggleRight },
];

export default function BillingSettingsPage() {
  const [activeTab, setActiveTab] = useState('company');
  const [settings, setSettings] = useState<BillingSettings>(defaultSettings);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/api/v1/billing/settings');
      if (response.success && response.data) {
        setSettings(response.data as BillingSettings);
      } else {
        throw new Error(response.error?.message || 'Failed to load settings');
      }
    } catch (error) {
      console.error('Failed to load billing settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async (section?: string) => {
    setSaving(true);
    setMessage(null);

    try {
      const body = section
        ? settings[`${section}_settings` as keyof BillingSettings] || settings[section as keyof BillingSettings]
        : settings;

      const response = await apiClient.put('/api/v1/billing/settings', body);
      if (response.success && response.data) {
        setSettings(response.data as BillingSettings);
        setMessage({ type: 'success', text: 'Settings saved successfully!' });
        setTimeout(() => setMessage(null), 3000);
      } else {
        throw new Error(response.error?.message || 'Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = async () => {
    if (!confirm('Are you sure you want to reset all settings to defaults?')) return;

    setSaving(true);
    try {
      const response = await apiClient.post('/api/v1/billing/settings/reset');
      if (response.success && response.data) {
        setSettings(response.data as BillingSettings);
        setMessage({ type: 'success', text: 'Settings reset to defaults!' });
        setTimeout(() => setMessage(null), 3000);
      } else {
        throw new Error(response.error?.message || 'Failed to reset settings');
      }
    } catch (error) {
      console.error('Error resetting settings:', error);
      setMessage({ type: 'error', text: 'Failed to reset settings' });
    } finally {
      setSaving(false);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'company':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-slate-100 mb-4">Company Information</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Building2 className="inline h-4 w-4 mr-1" />
                    Company Name *
                  </label>
                  <input
                    type="text"
                    value={settings.company_info.name}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, name: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="Acme Corporation"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Legal Name
                  </label>
                  <input
                    type="text"
                    value={settings.company_info.legal_name}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, legal_name: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="Acme Corporation Ltd."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Tax ID
                  </label>
                  <input
                    type="text"
                    value={settings.company_info.tax_id}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, tax_id: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="12-3456789"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Registration Number
                  </label>
                  <input
                    type="text"
                    value={settings.company_info.registration_number}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, registration_number: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="C123456"
                  />
                </div>
              </div>

              <h4 className="text-md font-medium text-slate-200 mt-6 mb-3">Address</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <MapPin className="inline h-4 w-4 mr-1" />
                    Street Address *
                  </label>
                  <input
                    type="text"
                    value={settings.company_info.address_line1}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, address_line1: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="123 Business Street"
                  />
                  <input
                    type="text"
                    value={settings.company_info.address_line2}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, address_line2: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 mt-2"
                    placeholder="Suite 100 (optional)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">City *</label>
                  <input
                    type="text"
                    value={settings.company_info.city}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, city: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="San Francisco"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">State/Province</label>
                  <input
                    type="text"
                    value={settings.company_info.state}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, state: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="CA"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Postal Code *</label>
                  <input
                    type="text"
                    value={settings.company_info.postal_code}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, postal_code: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="94105"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Globe className="inline h-4 w-4 mr-1" />
                    Country *
                  </label>
                  <select
                    value={settings.company_info.country}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, country: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  >
                    <option value="US">United States</option>
                    <option value="CA">Canada</option>
                    <option value="GB">United Kingdom</option>
                    <option value="AU">Australia</option>
                    <option value="DE">Germany</option>
                    <option value="FR">France</option>
                  </select>
                </div>
              </div>

              <h4 className="text-md font-medium text-slate-200 mt-6 mb-3">Contact & Branding</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Phone className="inline h-4 w-4 mr-1" />
                    Phone
                  </label>
                  <input
                    type="tel"
                    value={settings.company_info.phone}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, phone: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Mail className="inline h-4 w-4 mr-1" />
                    Email
                  </label>
                  <input
                    type="email"
                    value={settings.company_info.email}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, email: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="billing@company.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Globe className="inline h-4 w-4 mr-1" />
                    Website
                  </label>
                  <input
                    type="url"
                    value={settings.company_info.website}
                    onChange={(e) => setSettings({
                      ...settings,
                      company_info: { ...settings.company_info, website: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="https://company.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Palette className="inline h-4 w-4 mr-1" />
                    Brand Color
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={settings.company_info.brand_color}
                      onChange={(e) => setSettings({
                        ...settings,
                        company_info: { ...settings.company_info, brand_color: e.target.value }
                      })}
                      className="h-10 w-20 bg-slate-800 border border-slate-700 rounded cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.company_info.brand_color}
                      onChange={(e) => setSettings({
                        ...settings,
                        company_info: { ...settings.company_info, brand_color: e.target.value }
                      })}
                      className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                      placeholder="#0EA5E9"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <button
                  onClick={() => saveSettings('company')}
                  disabled={saving}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Company Info'}
                </button>
              </div>
            </div>
          </div>
        );

      case 'invoice':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-slate-100 mb-4">Invoice & Numbering Settings</h3>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-6">
                <h4 className="text-sm font-medium text-slate-200 mb-3">Invoice Numbering System</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      <Hash className="inline h-4 w-4 mr-1" />
                      Invoice Number Prefix
                    </label>
                    <input
                      type="text"
                      value={settings.invoice_settings.invoice_number_prefix}
                      onChange={(e) => setSettings({
                        ...settings,
                        invoice_settings: { ...settings.invoice_settings, invoice_number_prefix: e.target.value }
                      })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                      placeholder="INV"
                      maxLength={10}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Number Format Template
                    </label>
                    <select
                      value={settings.invoice_settings.invoice_number_format}
                      onChange={(e) => setSettings({
                        ...settings,
                        invoice_settings: { ...settings.invoice_settings, invoice_number_format: e.target.value }
                      })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    >
                      <option value="{prefix}-{year}-{sequence:06d}">{settings.invoice_settings.invoice_number_prefix}-2024-000001</option>
                      <option value="{prefix}/{year}/{sequence:04d}">{settings.invoice_settings.invoice_number_prefix}/2024/0001</option>
                      <option value="{prefix}-{sequence:08d}">{settings.invoice_settings.invoice_number_prefix}-00000001</option>
                      <option value="{year}{month:02d}-{sequence:04d}">202401-0001</option>
                      <option value="{prefix}_{year}_{month:02d}_{sequence:04d}">{settings.invoice_settings.invoice_number_prefix}_2024_01_0001</option>
                    </select>
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  Preview: Your next invoice number will be formatted like the selected template
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Calendar className="inline h-4 w-4 mr-1" />
                    Default Due Days
                  </label>
                  <input
                    type="number"
                    value={settings.invoice_settings.default_due_days}
                    onChange={(e) => setSettings({
                      ...settings,
                      invoice_settings: { ...settings.invoice_settings, default_due_days: parseInt(e.target.value) }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    min="0"
                    max="365"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Palette className="inline h-4 w-4 mr-1" />
                    Invoice Color Scheme
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={settings.invoice_settings.color_scheme}
                      onChange={(e) => setSettings({
                        ...settings,
                        invoice_settings: { ...settings.invoice_settings, color_scheme: e.target.value }
                      })}
                      className="h-10 w-20 bg-slate-800 border border-slate-700 rounded cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.invoice_settings.color_scheme}
                      onChange={(e) => setSettings({
                        ...settings,
                        invoice_settings: { ...settings.invoice_settings, color_scheme: e.target.value }
                      })}
                      className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4 mt-6">
                <div className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-slate-200">Include Payment Instructions</div>
                    <div className="text-xs text-slate-400">Show payment instructions on invoices</div>
                  </div>
                  <button
                    onClick={() => setSettings({
                      ...settings,
                      invoice_settings: {
                        ...settings.invoice_settings,
                        include_payment_instructions: !settings.invoice_settings.include_payment_instructions
                      }
                    })}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    {settings.invoice_settings.include_payment_instructions ?
                      <ToggleRight className="h-6 w-6 text-sky-500" /> :
                      <ToggleLeft className="h-6 w-6" />
                    }
                  </button>
                </div>

                {settings.invoice_settings.include_payment_instructions && (
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Payment Instructions
                    </label>
                    <textarea
                      value={settings.invoice_settings.payment_instructions}
                      onChange={(e) => setSettings({
                        ...settings,
                        invoice_settings: { ...settings.invoice_settings, payment_instructions: e.target.value }
                      })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                      rows={3}
                      maxLength={500}
                      placeholder="Please pay within the specified due date. Bank details are provided below..."
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Footer Text
                  </label>
                  <textarea
                    value={settings.invoice_settings.footer_text}
                    onChange={(e) => setSettings({
                      ...settings,
                      invoice_settings: { ...settings.invoice_settings, footer_text: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    rows={2}
                    maxLength={500}
                    placeholder="Thank you for your business!"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Terms and Conditions
                  </label>
                  <textarea
                    value={settings.invoice_settings.terms_and_conditions}
                    onChange={(e) => setSettings({
                      ...settings,
                      invoice_settings: { ...settings.invoice_settings, terms_and_conditions: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    rows={4}
                    maxLength={2000}
                    placeholder="Standard terms and conditions apply..."
                  />
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-slate-200">Logo on Invoices</div>
                    <div className="text-xs text-slate-400">Display company logo on PDF invoices</div>
                  </div>
                  <button
                    onClick={() => setSettings({
                      ...settings,
                      invoice_settings: {
                        ...settings.invoice_settings,
                        logo_on_invoices: !settings.invoice_settings.logo_on_invoices
                      }
                    })}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    {settings.invoice_settings.logo_on_invoices ?
                      <ToggleRight className="h-6 w-6 text-sky-500" /> :
                      <ToggleLeft className="h-6 w-6" />
                    }
                  </button>
                </div>
              </div>

              <h4 className="text-md font-medium text-slate-200 mt-6 mb-3">Email Settings</h4>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-slate-200">Send Invoice Emails</div>
                    <div className="text-xs text-slate-400">Automatically email invoices to customers</div>
                  </div>
                  <button
                    onClick={() => setSettings({
                      ...settings,
                      invoice_settings: {
                        ...settings.invoice_settings,
                        send_invoice_emails: !settings.invoice_settings.send_invoice_emails
                      }
                    })}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    {settings.invoice_settings.send_invoice_emails ?
                      <ToggleRight className="h-6 w-6 text-sky-500" /> :
                      <ToggleLeft className="h-6 w-6" />
                    }
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-slate-200">Send Payment Reminders</div>
                    <div className="text-xs text-slate-400">Send reminder emails for unpaid invoices</div>
                  </div>
                  <button
                    onClick={() => setSettings({
                      ...settings,
                      invoice_settings: {
                        ...settings.invoice_settings,
                        send_payment_reminders: !settings.invoice_settings.send_payment_reminders
                      }
                    })}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    {settings.invoice_settings.send_payment_reminders ?
                      <ToggleRight className="h-6 w-6 text-sky-500" /> :
                      <ToggleLeft className="h-6 w-6" />
                    }
                  </button>
                </div>

                {settings.invoice_settings.send_payment_reminders && (
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Reminder Schedule (days before due date)
                    </label>
                    <div className="flex gap-2">
                      {settings.invoice_settings.reminder_schedule_days.map((days, index) => (
                        <input
                          key={index}
                          type="number"
                          value={days}
                          onChange={(e) => {
                            const newDays = [...settings.invoice_settings.reminder_schedule_days];
                            newDays[index] = parseInt(e.target.value);
                            setSettings({
                              ...settings,
                              invoice_settings: { ...settings.invoice_settings, reminder_schedule_days: newDays }
                            });
                          }}
                          className="w-20 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                          min="1"
                          max="30"
                        />
                      ))}
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Reminders will be sent 7, 3, and 1 day(s) before due date</p>
                  </div>
                )}
              </div>

              <div className="mt-6">
                <button
                  onClick={() => saveSettings('invoice')}
                  disabled={saving}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Invoice Settings'}
                </button>
              </div>
            </div>
          </div>
        );

      case 'payment':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-slate-100 mb-4">Payment Settings</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Enabled Payment Methods</label>
                  <div className="space-y-2">
                    {['card', 'bank_account', 'digital_wallet', 'check', 'wire_transfer'].map((method) => (
                      <label key={method} className="flex items-center gap-3 p-3 bg-slate-800/50 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-800">
                        <input
                          type="checkbox"
                          checked={settings.payment_settings.enabled_payment_methods.includes(method)}
                          onChange={(e) => {
                            const methods = e.target.checked
                              ? [...settings.payment_settings.enabled_payment_methods, method]
                              : settings.payment_settings.enabled_payment_methods.filter(m => m !== method);
                            setSettings({
                              ...settings,
                              payment_settings: { ...settings.payment_settings, enabled_payment_methods: methods }
                            });
                          }}
                          className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-sky-500"
                        />
                        <span className="text-sm text-slate-200 capitalize">{method.replace('_', ' ')}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      <DollarSign className="inline h-4 w-4 mr-1" />
                      Default Currency
                    </label>
                    <select
                      value={settings.payment_settings.default_currency}
                      onChange={(e) => setSettings({
                        ...settings,
                        payment_settings: { ...settings.payment_settings, default_currency: e.target.value }
                      })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    >
                      <option value="USD">USD - US Dollar</option>
                      <option value="EUR">EUR - Euro</option>
                      <option value="GBP">GBP - British Pound</option>
                      <option value="CAD">CAD - Canadian Dollar</option>
                      <option value="AUD">AUD - Australian Dollar</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      <Clock className="inline h-4 w-4 mr-1" />
                      Default Payment Terms (days)
                    </label>
                    <input
                      type="number"
                      value={settings.payment_settings.default_payment_terms}
                      onChange={(e) => setSettings({
                        ...settings,
                        payment_settings: { ...settings.payment_settings, default_payment_terms: parseInt(e.target.value) }
                      })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                      min="0"
                      max="365"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      <Percent className="inline h-4 w-4 mr-1" />
                      Late Payment Fee (%)
                    </label>
                    <input
                      type="number"
                      value={settings.payment_settings.late_payment_fee}
                      onChange={(e) => setSettings({
                        ...settings,
                        payment_settings: { ...settings.payment_settings, late_payment_fee: parseFloat(e.target.value) }
                      })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                      min="0"
                      max="100"
                      step="0.1"
                    />
                  </div>
                </div>

                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-slate-200 mb-3">Failed Payment Retry Settings</h4>

                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-sm font-medium text-slate-200">Retry Failed Payments</div>
                      <div className="text-xs text-slate-400">Automatically retry failed payment attempts</div>
                    </div>
                    <button
                      onClick={() => setSettings({
                        ...settings,
                        payment_settings: {
                          ...settings.payment_settings,
                          retry_failed_payments: !settings.payment_settings.retry_failed_payments
                        }
                      })}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      {settings.payment_settings.retry_failed_payments ?
                        <ToggleRight className="h-6 w-6 text-sky-500" /> :
                        <ToggleLeft className="h-6 w-6" />
                      }
                    </button>
                  </div>

                  {settings.payment_settings.retry_failed_payments && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          <RefreshCw className="inline h-4 w-4 mr-1" />
                          Max Retry Attempts
                        </label>
                        <input
                          type="number"
                          value={settings.payment_settings.max_retry_attempts}
                          onChange={(e) => setSettings({
                            ...settings,
                            payment_settings: { ...settings.payment_settings, max_retry_attempts: parseInt(e.target.value) }
                          })}
                          className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                          min="1"
                          max="10"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Retry Interval (hours)
                        </label>
                        <input
                          type="number"
                          value={settings.payment_settings.retry_interval_hours}
                          onChange={(e) => setSettings({
                            ...settings,
                            payment_settings: { ...settings.payment_settings, retry_interval_hours: parseInt(e.target.value) }
                          })}
                          className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                          min="1"
                          max="168"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-6">
                <button
                  onClick={() => saveSettings('payment')}
                  disabled={saving}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Payment Settings'}
                </button>
              </div>
            </div>
          </div>
        );

      case 'tax':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-slate-100 mb-4">Tax Settings</h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-slate-200">Calculate Tax Automatically</div>
                    <div className="text-xs text-slate-400">Enable automatic tax calculation on invoices</div>
                  </div>
                  <button
                    onClick={() => setSettings({
                      ...settings,
                      tax_settings: {
                        ...settings.tax_settings,
                        calculate_tax: !settings.tax_settings.calculate_tax
                      }
                    })}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    {settings.tax_settings.calculate_tax ?
                      <ToggleRight className="h-6 w-6 text-sky-500" /> :
                      <ToggleLeft className="h-6 w-6" />
                    }
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                  <div>
                    <div className="text-sm font-medium text-slate-200">Tax-Inclusive Pricing</div>
                    <div className="text-xs text-slate-400">Prices already include tax</div>
                  </div>
                  <button
                    onClick={() => setSettings({
                      ...settings,
                      tax_settings: {
                        ...settings.tax_settings,
                        tax_inclusive_pricing: !settings.tax_settings.tax_inclusive_pricing
                      }
                    })}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    {settings.tax_settings.tax_inclusive_pricing ?
                      <ToggleRight className="h-6 w-6 text-sky-500" /> :
                      <ToggleLeft className="h-6 w-6" />
                    }
                  </button>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Percent className="inline h-4 w-4 mr-1" />
                    Default Tax Rate (%)
                  </label>
                  <input
                    type="number"
                    value={settings.tax_settings.default_tax_rate}
                    onChange={(e) => setSettings({
                      ...settings,
                      tax_settings: { ...settings.tax_settings, default_tax_rate: parseFloat(e.target.value) }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    min="0"
                    max="100"
                    step="0.01"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-slate-300">
                      Tax Registrations
                    </label>
                    <button
                      onClick={() => {
                        const newReg = { jurisdiction: '', registration_number: '' };
                        setSettings({
                          ...settings,
                          tax_settings: {
                            ...settings.tax_settings,
                            tax_registrations: [...settings.tax_settings.tax_registrations, newReg]
                          }
                        });
                      }}
                      className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg"
                    >
                      Add Registration
                    </button>
                  </div>

                  <div className="space-y-2">
                    {settings.tax_settings.tax_registrations.map((reg, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={reg.jurisdiction}
                          onChange={(e) => {
                            const newRegs = [...settings.tax_settings.tax_registrations];
                            newRegs[index] = { ...newRegs[index], jurisdiction: e.target.value };
                            setSettings({
                              ...settings,
                              tax_settings: { ...settings.tax_settings, tax_registrations: newRegs }
                            });
                          }}
                          className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                          placeholder="Jurisdiction (e.g., US-CA)"
                        />
                        <input
                          type="text"
                          value={reg.registration_number}
                          onChange={(e) => {
                            const newRegs = [...settings.tax_settings.tax_registrations];
                            newRegs[index] = { ...newRegs[index], registration_number: e.target.value };
                            setSettings({
                              ...settings,
                              tax_settings: { ...settings.tax_settings, tax_registrations: newRegs }
                            });
                          }}
                          className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                          placeholder="Registration Number"
                        />
                        <button
                          onClick={() => {
                            const newRegs = settings.tax_settings.tax_registrations.filter((_, i) => i !== index);
                            setSettings({
                              ...settings,
                              tax_settings: { ...settings.tax_settings, tax_registrations: newRegs }
                            });
                          }}
                          className="px-3 py-2 text-rose-400 hover:text-rose-300"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <button
                  onClick={() => saveSettings('tax')}
                  disabled={saving}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Tax Settings'}
                </button>
              </div>
            </div>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-slate-100 mb-4">Notification Settings</h3>

              <h4 className="text-md font-medium text-slate-200 mb-3">Email Notifications</h4>
              <div className="space-y-4">
                {[
                  { key: 'send_invoice_notifications', label: 'Invoice Notifications', desc: 'Send emails when invoices are created' },
                  { key: 'send_payment_confirmations', label: 'Payment Confirmations', desc: 'Send emails when payments are received' },
                  { key: 'send_overdue_notices', label: 'Overdue Notices', desc: 'Send emails for overdue invoices' },
                  { key: 'send_receipt_emails', label: 'Receipt Emails', desc: 'Send receipts after successful payments' },
                ].map((item) => (
                  <div key={item.key} className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                    <div>
                      <div className="text-sm font-medium text-slate-200">{item.label}</div>
                      <div className="text-xs text-slate-400">{item.desc}</div>
                    </div>
                    <button
                      onClick={() => setSettings({
                        ...settings,
                        notification_settings: {
                          ...settings.notification_settings,
                          [item.key]: !settings.notification_settings[item.key as keyof typeof settings.notification_settings]
                        }
                      })}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      {settings.notification_settings[item.key as keyof typeof settings.notification_settings] ?
                        <ToggleRight className="h-6 w-6 text-sky-500" /> :
                        <ToggleLeft className="h-6 w-6" />
                      }
                    </button>
                  </div>
                ))}
              </div>

              <h4 className="text-md font-medium text-slate-200 mt-6 mb-3">Webhook Settings</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Webhook className="inline h-4 w-4 mr-1" />
                    Webhook URL
                  </label>
                  <input
                    type="url"
                    value={settings.notification_settings.webhook_url}
                    onChange={(e) => setSettings({
                      ...settings,
                      notification_settings: { ...settings.notification_settings, webhook_url: e.target.value }
                    })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                    placeholder="https://your-api.com/webhooks/billing"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Webhook Events
                  </label>
                  <div className="space-y-2">
                    {['invoice.created', 'invoice.paid', 'payment.succeeded', 'payment.failed', 'subscription.updated'].map((event) => (
                      <label key={event} className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={settings.notification_settings.webhook_events.includes(event)}
                          onChange={(e) => {
                            const events = e.target.checked
                              ? [...settings.notification_settings.webhook_events, event]
                              : settings.notification_settings.webhook_events.filter(e => e !== event);
                            setSettings({
                              ...settings,
                              notification_settings: { ...settings.notification_settings, webhook_events: events }
                            });
                          }}
                          className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-sky-500"
                        />
                        <span className="text-sm text-slate-300">{event}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <button
                  onClick={() => saveSettings('notifications')}
                  disabled={saving}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Notification Settings'}
                </button>
              </div>
            </div>
          </div>
        );

      case 'features':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-slate-100 mb-4">Feature Toggles</h3>
              <p className="text-sm text-slate-400 mb-6">Enable or disable specific billing features for your organization</p>

              <div className="space-y-4">
                {Object.entries(settings.features_enabled).map(([feature, enabled]) => (
                  <div key={feature} className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                    <div>
                      <div className="text-sm font-medium text-slate-200 capitalize">{feature.replace('_', ' ')}</div>
                      <div className="text-xs text-slate-400">
                        {feature === 'invoicing' && 'Create and manage invoices'}
                        {feature === 'payments' && 'Accept and process payments'}
                        {feature === 'credit_notes' && 'Issue credit notes and refunds'}
                        {feature === 'receipts' && 'Generate payment receipts'}
                        {feature === 'tax_calculation' && 'Automatic tax calculation'}
                        {feature === 'webhooks' && 'Send webhook notifications'}
                        {feature === 'reporting' && 'Advanced reporting and analytics'}
                      </div>
                    </div>
                    <button
                      onClick={() => setSettings({
                        ...settings,
                        features_enabled: {
                          ...settings.features_enabled,
                          [feature]: !enabled
                        }
                      })}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      {enabled ?
                        <ToggleRight className="h-6 w-6 text-sky-500" /> :
                        <ToggleLeft className="h-6 w-6" />
                      }
                    </button>
                  </div>
                ))}
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => saveSettings('features')}
                  disabled={saving}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Feature Settings'}
                </button>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-100">Billing Settings</h1>
          <p className="text-slate-400 mt-1">Configure billing, invoicing, and payment settings for your organization</p>
        </div>

        {/* Success/Error Messages */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
              : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
            )}
            <span className="text-sm">{message.text}</span>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-6 border-b border-slate-800">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-3 px-1 border-b-2 transition-colors text-sm font-medium ${
                  activeTab === tab.id
                    ? 'border-sky-500 text-sky-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content Area */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-slate-400">Loading settings...</div>
            </div>
          ) : (
            renderTabContent()
          )}
        </div>

        {/* Global Actions */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={resetToDefaults}
            disabled={saving}
            className="px-4 py-2 border border-slate-700 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  );
}