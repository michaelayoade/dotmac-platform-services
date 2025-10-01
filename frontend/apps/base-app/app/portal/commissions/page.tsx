"use client";

import { usePartnerCommissions } from "@/hooks/usePartnerPortal";
import { DollarSign, Clock, CheckCircle, AlertCircle, XCircle } from "lucide-react";

export default function PartnerCommissionsPage() {
  const { data: commissions, isLoading, error } = usePartnerCommissions();

  const STATUS_COLORS = {
    pending: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    approved: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    paid: "bg-green-500/10 text-green-400 border-green-500/20",
    disputed: "bg-red-500/10 text-red-400 border-red-500/20",
    cancelled: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  };

  const STATUS_ICONS = {
    pending: Clock,
    approved: AlertCircle,
    paid: CheckCircle,
    disputed: XCircle,
    cancelled: XCircle,
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-slate-400">Loading commissions...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-red-400">Failed to load commissions</div>
          <div className="text-sm text-slate-500 mt-2">{error.message}</div>
        </div>
      </div>
    );
  }

  const commissionList = commissions || [];
  const totalEarned = commissionList.reduce(
    (sum, c) => sum + c.commission_amount,
    0
  );
  const totalPaid = commissionList
    .filter((c) => c.status === "paid")
    .reduce((sum, c) => sum + c.commission_amount, 0);
  const totalPending = commissionList
    .filter((c) => c.status === "pending" || c.status === "approved")
    .reduce((sum, c) => sum + c.commission_amount, 0);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white">Commissions</h1>
        <p className="text-slate-400 mt-1">
          Track your commission earnings and payments
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">Total Earned</div>
              <div className="text-3xl font-bold text-white">
                ${totalEarned.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {commissionList.length} events
              </div>
            </div>
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </div>

        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">Paid</div>
              <div className="text-3xl font-bold text-green-400">
                ${totalPaid.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 mt-1">Received</div>
            </div>
            <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>

        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">Pending</div>
              <div className="text-3xl font-bold text-yellow-400">
                ${totalPending.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 mt-1">Awaiting payout</div>
            </div>
            <div className="w-12 h-12 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-yellow-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Commissions Table */}
      <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
        {commissionList.length === 0 ? (
          <div className="text-center py-12">
            <DollarSign className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 mb-2">No commissions yet</p>
            <p className="text-sm text-slate-500">
              Commissions will appear here when your referrals convert
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-950 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Rate
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Commission
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Payment Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {commissionList.map((commission) => {
                  const StatusIcon = STATUS_ICONS[commission.status];

                  return (
                    <tr
                      key={commission.id}
                      className="hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="px-4 py-3 text-sm text-white">
                        {new Date(commission.event_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {commission.customer_id.substring(0, 8)}...
                      </td>
                      <td className="px-4 py-3 text-sm text-white">
                        ${commission.amount.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {(commission.commission_rate * 100).toFixed(2)}%
                      </td>
                      <td className="px-4 py-3 text-sm font-semibold text-white">
                        ${commission.commission_amount.toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-1 text-xs rounded border flex items-center gap-1 w-fit ${
                            STATUS_COLORS[commission.status]
                          }`}
                        >
                          <StatusIcon className="w-3 h-3" />
                          {commission.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {commission.payment_date
                          ? new Date(commission.payment_date).toLocaleDateString()
                          : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Payment Information */}
      <div className="mt-6 bg-slate-900 p-6 rounded-lg border border-slate-800">
        <h2 className="text-lg font-semibold text-white mb-3">
          Payment Information
        </h2>
        <div className="space-y-2 text-sm text-slate-400">
          <p>• Commissions are typically paid monthly on the 15th</p>
          <p>
            • Minimum payout threshold: $100 (pending commissions below this
            amount will roll over to the next month)
          </p>
          <p>
            • Payment method can be configured in{" "}
            <a href="/portal/settings" className="text-blue-400 hover:text-blue-300">
              Settings
            </a>
          </p>
          <p>
            • For questions about commissions, contact{" "}
            <a
              href="mailto:partners@dotmac.com"
              className="text-blue-400 hover:text-blue-300"
            >
              partners@dotmac.com
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
