"use client";

import { usePartnerDashboard } from "@/hooks/usePartnerPortal";
import {
  Users,
  DollarSign,
  TrendingUp,
  UserPlus,
  Clock,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";

export default function PartnerDashboardPage() {
  const { data: stats, isLoading, error } = usePartnerDashboard();

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-slate-400">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-red-400">Failed to load dashboard</div>
          <div className="text-sm text-slate-500 mt-2">
            {error?.message || "Please try again"}
          </div>
        </div>
      </div>
    );
  }

  const conversionRate = stats.conversion_rate || 0;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white">Partner Dashboard</h1>
        <p className="text-slate-400 mt-1">
          Track your performance and manage your partnership
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">Total Customers</div>
              <div className="text-3xl font-bold text-white">
                {stats.total_customers}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {stats.active_customers} active
              </div>
            </div>
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </div>

        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">Total Revenue</div>
              <div className="text-3xl font-bold text-white">
                ${stats.total_revenue_generated.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 mt-1">Generated</div>
            </div>
            <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>

        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">
                Pending Commissions
              </div>
              <div className="text-3xl font-bold text-yellow-400">
                ${stats.pending_commissions.toLocaleString()}
              </div>
              <div className="text-xs text-slate-500 mt-1">Awaiting payout</div>
            </div>
            <div className="w-12 h-12 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-yellow-400" />
            </div>
          </div>
        </div>

        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400 mb-1">Conversion Rate</div>
              <div className="text-3xl font-bold text-white">
                {conversionRate.toFixed(1)}%
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {stats.converted_referrals} of {stats.total_referrals}
              </div>
            </div>
            <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Commission Overview */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <h2 className="text-xl font-semibold text-white mb-4">
            Commission Summary
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div className="text-sm text-slate-400">Total Earned</div>
              <div className="text-lg font-semibold text-white">
                ${stats.total_commissions_earned.toLocaleString()}
              </div>
            </div>
            <div className="flex justify-between items-center">
              <div className="text-sm text-slate-400">Total Paid</div>
              <div className="text-lg font-semibold text-green-400">
                ${stats.total_commissions_paid.toLocaleString()}
              </div>
            </div>
            <div className="flex justify-between items-center">
              <div className="text-sm text-slate-400">Pending</div>
              <div className="text-lg font-semibold text-yellow-400">
                ${stats.pending_commissions.toLocaleString()}
              </div>
            </div>
            <div className="pt-4 border-t border-slate-800">
              <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                <DollarSign className="w-4 h-4" />
                Commission Model: {stats.commission_model.replace("_", " ")}
              </div>
              <div className="text-sm text-slate-400">
                Default Rate:{" "}
                {(stats.default_commission_rate * 100).toFixed(2)}%
              </div>
            </div>
          </div>
          <Link
            href="/portal/commissions"
            className="mt-4 block w-full text-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            View All Commissions
          </Link>
        </div>

        <div className="bg-slate-900 p-6 rounded-lg border border-slate-800">
          <h2 className="text-xl font-semibold text-white mb-4">
            Referral Overview
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div className="text-sm text-slate-400">Total Referrals</div>
              <div className="text-lg font-semibold text-white">
                {stats.total_referrals}
              </div>
            </div>
            <div className="flex justify-between items-center">
              <div className="text-sm text-slate-400">Converted</div>
              <div className="text-lg font-semibold text-green-400">
                {stats.converted_referrals}
              </div>
            </div>
            <div className="flex justify-between items-center">
              <div className="text-sm text-slate-400">Pending</div>
              <div className="text-lg font-semibold text-yellow-400">
                {stats.pending_referrals}
              </div>
            </div>
            <div className="pt-4 border-t border-slate-800">
              <div className="text-sm text-slate-400 mb-2">
                Your conversion rate is{" "}
                {conversionRate > 25 ? "excellent" : conversionRate > 15 ? "good" : "average"}
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${Math.min(conversionRate, 100)}%` }}
                />
              </div>
            </div>
          </div>
          <Link
            href="/portal/referrals"
            className="mt-4 block w-full text-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Manage Referrals
          </Link>
        </div>
      </div>

      {/* Partner Tier Status */}
      <div className="bg-slate-900 p-6 rounded-lg border border-slate-800 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Partner Status
            </h2>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-purple-500/10 text-purple-400 rounded-lg text-sm font-medium">
                {stats.current_tier.toUpperCase()} Tier
              </span>
              <span className="text-sm text-slate-400">
                Commission Rate: {(stats.default_commission_rate * 100).toFixed(2)}%
              </span>
            </div>
          </div>
          <Link
            href="/portal/settings"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
          >
            View Details
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6">
        <Link
          href="/portal/referrals"
          className="bg-slate-900 p-6 rounded-lg border border-slate-800 hover:border-blue-600 transition-colors group"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
              <UserPlus className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <div className="text-white font-semibold">Submit Referral</div>
              <div className="text-sm text-slate-400">Refer a new customer</div>
            </div>
          </div>
        </Link>

        <Link
          href="/portal/customers"
          className="bg-slate-900 p-6 rounded-lg border border-slate-800 hover:border-blue-600 transition-colors group"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center group-hover:bg-green-500/20 transition-colors">
              <Users className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <div className="text-white font-semibold">My Customers</div>
              <div className="text-sm text-slate-400">
                View your {stats.total_customers} customers
              </div>
            </div>
          </div>
        </Link>

        <Link
          href="/portal/performance"
          className="bg-slate-900 p-6 rounded-lg border border-slate-800 hover:border-blue-600 transition-colors group"
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
              <TrendingUp className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <div className="text-white font-semibold">Performance</div>
              <div className="text-sm text-slate-400">View detailed analytics</div>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
