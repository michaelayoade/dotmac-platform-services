'use client';

import { useState } from 'react';
import { CreditCard, FileDown } from 'lucide-react';
import InvoiceList, { Invoice } from '@/components/billing/InvoiceList';

const DEFAULT_TENANT_ID = process.env.NEXT_PUBLIC_TENANT_ID ?? 'demo-tenant';

export default function BillingPage() {
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Billing &amp; Invoices</h1>
          <p className="text-slate-400">
            Monitor tenant invoices, outstanding balances, and payment activity in one place.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-300">
            <CreditCard className="h-4 w-4 text-sky-400" />
            <span>Tenant</span>
            <span className="font-semibold text-slate-200">{DEFAULT_TENANT_ID || 'Unknown'}</span>
          </div>
          <button
            type="button"
            onClick={() => console.log('Export invoices clicked')}
            className="flex items-center gap-2 rounded-lg border border-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 transition-colors"
          >
            <FileDown className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      <InvoiceList
        tenantId={DEFAULT_TENANT_ID}
        onInvoiceSelect={setSelectedInvoice}
      />

      {selectedInvoice && (
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
          <div className="text-sm text-slate-400 mb-1">Selected invoice</div>
          <div className="text-slate-200 font-semibold">{selectedInvoice.invoice_number}</div>
          <div className="text-xs text-slate-500 mt-1">
            {selectedInvoice.billing_email} • Due {new Date(selectedInvoice.due_date).toLocaleDateString()}
          </div>
        </div>
      )}
    </div>
  );
}
