import type {
  AssetStatus,
  AssetCondition,
  Asset,
  MaintenanceStatus,
  MaintenancePriority,
} from '../types';

export const assetStatusHelpers = {
  getStatusColor: (status: AssetStatus): string => {
    switch (status) {
      case 'active':
        return '#22c55e';
      case 'inactive':
        return '#6b7280';
      case 'in_maintenance':
        return '#f59e0b';
      case 'retired':
        return '#9ca3af';
      case 'disposed':
        return '#374151';
      case 'lost':
        return '#ef4444';
      case 'stolen':
        return '#dc2626';
      case 'reserved':
        return '#3b82f6';
      default:
        return '#9ca3af';
    }
  },

  getConditionColor: (condition: AssetCondition): string => {
    switch (condition) {
      case 'excellent':
        return '#22c55e';
      case 'good':
        return '#84cc16';
      case 'fair':
        return '#f59e0b';
      case 'poor':
        return '#f97316';
      case 'needs_repair':
        return '#ef4444';
      case 'beyond_repair':
        return '#dc2626';
      default:
        return '#9ca3af';
    }
  },

  getStatusIcon: (status: AssetStatus): string => {
    switch (status) {
      case 'active':
        return '✅';
      case 'inactive':
        return '⏸️';
      case 'in_maintenance':
        return '🔧';
      case 'retired':
        return '📦';
      case 'disposed':
        return '🗑️';
      case 'lost':
        return '❓';
      case 'stolen':
        return '🚨';
      case 'reserved':
        return '🔒';
      default:
        return '❓';
    }
  },

  getConditionIcon: (condition: AssetCondition): string => {
    switch (condition) {
      case 'excellent':
        return '⭐';
      case 'good':
        return '👍';
      case 'fair':
        return '👌';
      case 'poor':
        return '👎';
      case 'needs_repair':
        return '🔧';
      case 'beyond_repair':
        return '💀';
      default:
        return '❓';
    }
  },

  isAssetOperational: (asset: Asset): boolean => {
    return asset.status === 'active' && ['excellent', 'good', 'fair'].includes(asset.condition);
  },

  needsAttention: (asset: Asset): boolean => {
    return (
      asset.condition === 'needs_repair' ||
      asset.status === 'in_maintenance' ||
      (asset.warranty_expiry &&
        new Date(asset.warranty_expiry) < new Date(Date.now() + 30 * 24 * 60 * 60 * 1000))
    ); // 30 days
  },

  getAssetAge: (asset: Asset): string => {
    if (!asset.purchase_date) return 'Unknown';

    const now = new Date();
    const purchaseDate = new Date(asset.purchase_date);
    const diffTime = Math.abs(now.getTime() - purchaseDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 365) {
      return `${Math.floor(diffDays / 30)} months`;
    }

    const years = Math.floor(diffDays / 365);
    const months = Math.floor((diffDays % 365) / 30);

    return months > 0 ? `${years}y ${months}m` : `${years} years`;
  },

  getWarrantyStatus: (asset: Asset): 'active' | 'expiring_soon' | 'expired' | 'unknown' => {
    if (!asset.warranty_expiry) return 'unknown';

    const now = new Date();
    const warrantyExpiry = new Date(asset.warranty_expiry);
    const daysUntilExpiry = Math.ceil(
      (warrantyExpiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysUntilExpiry < 0) return 'expired';
    if (daysUntilExpiry <= 90) return 'expiring_soon'; // 90 days
    return 'active';
  },

  getMaintenancePriorityColor: (priority: MaintenancePriority): string => {
    switch (priority) {
      case 'low':
        return '#10b981';
      case 'medium':
        return '#f59e0b';
      case 'high':
        return '#f97316';
      case 'critical':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  },

  getMaintenanceStatusColor: (status: MaintenanceStatus): string => {
    switch (status) {
      case 'scheduled':
        return '#3b82f6';
      case 'in_progress':
        return '#f59e0b';
      case 'completed':
        return '#22c55e';
      case 'cancelled':
        return '#6b7280';
      case 'deferred':
        return '#f97316';
      default:
        return '#9ca3af';
    }
  },

  formatCurrency: (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  },

  calculateUtilizationRate: (assets: Asset[]): number => {
    if (assets.length === 0) return 0;

    const activeAssets = assets.filter((asset) => asset.status === 'active');
    return (activeAssets.length / assets.length) * 100;
  },

  getAssetValue: (asset: Asset): number => {
    // Simple depreciation calculation if no depreciation schedule exists
    if (!asset.purchase_price) return 0;

    if (asset.depreciation_schedule) {
      return asset.depreciation_schedule.current_value;
    }

    // Simple straight-line depreciation over 5 years as fallback
    if (asset.purchase_date) {
      const ageInYears =
        (Date.now() - new Date(asset.purchase_date).getTime()) / (1000 * 60 * 60 * 24 * 365);
      const depreciationRate = Math.min(ageInYears / 5, 0.8); // Max 80% depreciation
      return asset.purchase_price * (1 - depreciationRate);
    }

    return asset.purchase_price;
  },
};
