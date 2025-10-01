import { TrendingUp, Users, DollarSign, Activity } from 'lucide-react';
import { CustomerMetrics } from '@/types';

interface CustomersMetricsProps {
  metrics: CustomerMetrics | null;
  loading: boolean;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  loading?: boolean;
}

function MetricCard({ title, value, change, changeType = 'neutral', icon: Icon, loading }: MetricCardProps) {
  if (loading) {
    return (
      <div className="bg-slate-800 p-6 rounded-lg">
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-4">
            <div className="h-4 bg-slate-700 rounded w-24"></div>
            <div className="h-8 w-8 bg-slate-700 rounded"></div>
          </div>
          <div className="h-8 bg-slate-700 rounded w-20 mb-2"></div>
          <div className="h-4 bg-slate-700 rounded w-16"></div>
        </div>
      </div>
    );
  }

  const changeColorClass = {
    positive: 'text-green-400',
    negative: 'text-red-400',
    neutral: 'text-slate-400'
  }[changeType];

  return (
    <div className="bg-slate-800 p-6 rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-400">{title}</h3>
        <Icon className="h-5 w-5 text-slate-400" />
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      {change && (
        <p className={`text-sm ${changeColorClass}`}>
          {change}
        </p>
      )}
    </div>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function CustomersMetrics({ metrics, loading }: CustomersMetricsProps) {
  if (loading || !metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <MetricCard
            key={i}
            title=""
            value=""
            icon={Users}
            loading={true}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Primary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Customers"
          value={formatNumber(metrics.total_customers)}
          change={`+${metrics.new_customers_this_month} this month`}
          changeType="positive"
          icon={Users}
        />

        <MetricCard
          title="Active Customers"
          value={formatNumber(metrics.active_customers)}
          change={`${metrics.total_customers > 0 ? ((metrics.active_customers / metrics.total_customers) * 100).toFixed(1) : '0'}% of total`}
          changeType="neutral"
          icon={Activity}
        />

        <MetricCard
          title="Total Revenue"
          value={formatCurrency(metrics.total_revenue)}
          icon={DollarSign}
        />

        <MetricCard
          title="Avg Lifetime Value"
          value={formatCurrency(metrics.average_lifetime_value)}
          change={`Churn rate: ${formatPercentage(metrics.churn_rate)}`}
          changeType={metrics.churn_rate > 10 ? 'negative' : 'positive'}
          icon={TrendingUp}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer Status Distribution */}
        <div className="bg-slate-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">By Status</h3>
          <div className="space-y-3">
            {Object.entries(metrics.customers_by_status).map(([status, count]) => {
              const percentage = metrics.total_customers > 0 ? (count / metrics.total_customers) * 100 : 0;
              const statusColors = {
                active: 'bg-green-500',
                prospect: 'bg-yellow-500',
                inactive: 'bg-gray-500',
                churned: 'bg-red-500',
                suspended: 'bg-orange-500',
                archived: 'bg-slate-500',
              } as Record<string, string>;

              return (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${statusColors[status] || 'bg-slate-500'}`}></div>
                    <span className="text-slate-300 capitalize">{status}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{formatNumber(count)}</span>
                    <span className="text-slate-400 text-sm">({percentage.toFixed(1)}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Customer Tier Distribution */}
        <div className="bg-slate-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">By Tier</h3>
          <div className="space-y-3">
            {Object.entries(metrics.customers_by_tier).map(([tier, count]) => {
              const percentage = metrics.total_customers > 0 ? (count / metrics.total_customers) * 100 : 0;
              const tierColors = {
                free: 'bg-slate-500',
                basic: 'bg-blue-500',
                standard: 'bg-purple-500',
                premium: 'bg-yellow-500',
                enterprise: 'bg-green-500',
              } as Record<string, string>;

              return (
                <div key={tier} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${tierColors[tier] || 'bg-slate-500'}`}></div>
                    <span className="text-slate-300 capitalize">{tier}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{formatNumber(count)}</span>
                    <span className="text-slate-400 text-sm">({percentage.toFixed(1)}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Customer Type Distribution */}
        <div className="bg-slate-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">By Type</h3>
          <div className="space-y-3">
            {Object.entries(metrics.customers_by_type).map(([type, count]) => {
              const percentage = metrics.total_customers > 0 ? (count / metrics.total_customers) * 100 : 0;
              const typeColors = {
                individual: 'bg-blue-500',
                business: 'bg-green-500',
                enterprise: 'bg-purple-500',
                partner: 'bg-orange-500',
                vendor: 'bg-red-500',
              } as Record<string, string>;

              return (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${typeColors[type] || 'bg-slate-500'}`}></div>
                    <span className="text-slate-300 capitalize">{type}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium">{formatNumber(count)}</span>
                    <span className="text-slate-400 text-sm">({percentage.toFixed(1)}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Top Segments */}
      {metrics.top_segments && metrics.top_segments.length > 0 && (
        <div className="bg-slate-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">Top Customer Segments</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {metrics.top_segments.map((segment, index) => (
              <div key={segment.name} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-sky-500 rounded-full"></div>
                  <span className="text-slate-200 font-medium">{segment.name}</span>
                </div>
                <span className="text-slate-400">{formatNumber(segment.count)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}