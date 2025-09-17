import type {
  Asset,
  AssetEventType,
  DepreciationMethod,
  DepreciationSchedule,
  AssetHistory,
} from '../types';

export const lifecycleHelpers = {
  calculateDepreciation: (
    purchasePrice: number,
    method: DepreciationMethod,
    usefulLifeYears: number,
    salvageValue: number,
    ageInYears: number
  ): { currentValue: number; annualDepreciation: number; accumulatedDepreciation: number } => {
    let annualDepreciation = 0;
    let currentValue = purchasePrice;
    let accumulatedDepreciation = 0;

    switch (method) {
      case 'straight_line':
        annualDepreciation = (purchasePrice - salvageValue) / usefulLifeYears;
        accumulatedDepreciation = Math.min(
          annualDepreciation * ageInYears,
          purchasePrice - salvageValue
        );
        currentValue = purchasePrice - accumulatedDepreciation;
        break;

      case 'declining_balance':
        // Double declining balance method (200% declining)
        const declineRate = 2 / usefulLifeYears;
        let bookValue = purchasePrice;

        for (let year = 0; year < Math.floor(ageInYears); year++) {
          const yearlyDepreciation = Math.max(bookValue * declineRate, bookValue - salvageValue);
          accumulatedDepreciation += yearlyDepreciation;
          bookValue -= yearlyDepreciation;

          if (bookValue <= salvageValue) {
            bookValue = salvageValue;
            break;
          }
        }

        // Handle partial year
        if (ageInYears % 1 > 0 && bookValue > salvageValue) {
          const partialYearDepreciation = bookValue * declineRate * (ageInYears % 1);
          accumulatedDepreciation += Math.min(partialYearDepreciation, bookValue - salvageValue);
        }

        currentValue = Math.max(purchasePrice - accumulatedDepreciation, salvageValue);
        annualDepreciation = accumulatedDepreciation / ageInYears;
        break;

      case 'units_of_production':
        // This would require usage data, so fallback to straight line
        annualDepreciation = (purchasePrice - salvageValue) / usefulLifeYears;
        accumulatedDepreciation = Math.min(
          annualDepreciation * ageInYears,
          purchasePrice - salvageValue
        );
        currentValue = purchasePrice - accumulatedDepreciation;
        break;
    }

    return {
      currentValue: Math.max(currentValue, salvageValue),
      annualDepreciation,
      accumulatedDepreciation,
    };
  },

  generateDepreciationSchedule: (
    purchasePrice: number,
    method: DepreciationMethod,
    usefulLifeYears: number,
    salvageValue: number
  ): DepreciationSchedule => {
    const { currentValue, annualDepreciation } = lifecycleHelpers.calculateDepreciation(
      purchasePrice,
      method,
      usefulLifeYears,
      salvageValue,
      0 // Start from purchase date
    );

    return {
      method,
      useful_life_years: usefulLifeYears,
      salvage_value: salvageValue,
      current_value: currentValue,
      annual_depreciation: annualDepreciation,
    };
  },

  getAssetLifecycleStage: (
    asset: Asset
  ): 'new' | 'active' | 'mature' | 'declining' | 'end_of_life' => {
    if (!asset.purchase_date) return 'active';

    const ageInYears =
      (Date.now() - new Date(asset.purchase_date).getTime()) / (1000 * 60 * 60 * 24 * 365);
    const usefulLife = asset.depreciation_schedule?.useful_life_years || 5; // Default 5 years

    const lifePercentage = ageInYears / usefulLife;

    if (lifePercentage < 0.2) return 'new';
    if (lifePercentage < 0.5) return 'active';
    if (lifePercentage < 0.8) return 'mature';
    if (lifePercentage < 1.0) return 'declining';
    return 'end_of_life';
  },

  shouldConsiderReplacement: (asset: Asset): boolean => {
    const stage = lifecycleHelpers.getAssetLifecycleStage(asset);
    const needsRepair = asset.condition === 'needs_repair';
    const beyondRepair = asset.condition === 'beyond_repair';
    const highMaintenanceCost = false; // Would need maintenance cost data

    return (
      stage === 'end_of_life' ||
      beyondRepair ||
      (stage === 'declining' && (needsRepair || highMaintenanceCost))
    );
  },

  getLifecycleMetrics: (assets: Asset[]) => {
    const stages = {
      new: 0,
      active: 0,
      mature: 0,
      declining: 0,
      end_of_life: 0,
    };

    const totalValue = assets.reduce((sum, asset) => sum + (asset.purchase_price || 0), 0);
    const currentValue = assets.reduce((sum, asset) => {
      if (asset.depreciation_schedule) {
        return sum + asset.depreciation_schedule.current_value;
      }
      // Simple depreciation fallback
      const ageInYears = asset.purchase_date
        ? (Date.now() - new Date(asset.purchase_date).getTime()) / (1000 * 60 * 60 * 24 * 365)
        : 0;
      const depreciated = (asset.purchase_price || 0) * Math.min(ageInYears * 0.2, 0.8); // 20% per year, max 80%
      return (
        sum + Math.max((asset.purchase_price || 0) - depreciated, (asset.purchase_price || 0) * 0.1)
      );
    }, 0);

    assets.forEach((asset) => {
      const stage = lifecycleHelpers.getAssetLifecycleStage(asset);
      stages[stage]++;
    });

    const replacementCandidates = assets.filter((asset) =>
      lifecycleHelpers.shouldConsiderReplacement(asset)
    );

    return {
      totalAssets: assets.length,
      lifecycleStages: stages,
      totalPurchaseValue: totalValue,
      currentValue,
      depreciationAmount: totalValue - currentValue,
      depreciationPercentage: totalValue > 0 ? ((totalValue - currentValue) / totalValue) * 100 : 0,
      replacementCandidates: replacementCandidates.length,
      averageAge:
        assets.length > 0
          ? assets.reduce((sum, asset) => {
              if (!asset.purchase_date) return sum;
              const ageInYears =
                (Date.now() - new Date(asset.purchase_date).getTime()) /
                (1000 * 60 * 60 * 24 * 365);
              return sum + ageInYears;
            }, 0) / assets.length
          : 0,
    };
  },

  generateAssetEvent: (
    assetId: string,
    eventType: AssetEventType,
    description: string,
    performedBy: string,
    metadata?: Record<string, any>
  ): Omit<AssetHistory, 'id'> => {
    return {
      asset_id: assetId,
      event_type: eventType,
      event_date: new Date(),
      description,
      performed_by: performedBy,
      metadata,
    };
  },

  getEventTypeIcon: (eventType: AssetEventType): string => {
    switch (eventType) {
      case 'created':
        return '➕';
      case 'updated':
        return '✏️';
      case 'transferred':
        return '📦';
      case 'assigned':
        return '👤';
      case 'unassigned':
        return '👤';
      case 'maintenance_scheduled':
        return '📅';
      case 'maintenance_completed':
        return '✅';
      case 'condition_changed':
        return '🔄';
      case 'status_changed':
        return '🚦';
      case 'disposed':
        return '🗑️';
      case 'warranty_expired':
        return '⏰';
      default:
        return '📝';
    }
  },

  getEventTypeColor: (eventType: AssetEventType): string => {
    switch (eventType) {
      case 'created':
        return '#22c55e';
      case 'updated':
        return '#3b82f6';
      case 'transferred':
        return '#f59e0b';
      case 'assigned':
        return '#8b5cf6';
      case 'unassigned':
        return '#6b7280';
      case 'maintenance_scheduled':
        return '#0ea5e9';
      case 'maintenance_completed':
        return '#22c55e';
      case 'condition_changed':
        return '#f97316';
      case 'status_changed':
        return '#ef4444';
      case 'disposed':
        return '#374151';
      case 'warranty_expired':
        return '#dc2626';
      default:
        return '#6b7280';
    }
  },

  calculateROI: (
    asset: Asset,
    maintenanceCosts: number = 0,
    revenueGenerated: number = 0
  ): number => {
    const initialInvestment = asset.purchase_price || 0;
    const currentValue = asset.depreciation_schedule?.current_value || initialInvestment;
    const totalCosts = initialInvestment + maintenanceCosts;

    if (totalCosts === 0) return 0;

    const totalReturns = revenueGenerated + currentValue;
    return ((totalReturns - totalCosts) / totalCosts) * 100;
  },

  predictMaintenanceNeeds: (
    asset: Asset,
    historicalRecords: any[] = []
  ): {
    nextMaintenanceDate: Date;
    estimatedCost: number;
    priority: 'low' | 'medium' | 'high' | 'critical';
  } => {
    // Simple prediction based on asset age and condition
    const ageInYears = asset.purchase_date
      ? (Date.now() - new Date(asset.purchase_date).getTime()) / (1000 * 60 * 60 * 24 * 365)
      : 1;

    let maintenanceFrequencyDays = 365; // Default annual
    let estimatedCost = 1000; // Default cost
    let priority: 'low' | 'medium' | 'high' | 'critical' = 'medium';

    // Adjust based on asset condition
    switch (asset.condition) {
      case 'excellent':
        maintenanceFrequencyDays = 365;
        priority = 'low';
        estimatedCost = 500;
        break;
      case 'good':
        maintenanceFrequencyDays = 180;
        priority = 'low';
        estimatedCost = 750;
        break;
      case 'fair':
        maintenanceFrequencyDays = 90;
        priority = 'medium';
        estimatedCost = 1000;
        break;
      case 'poor':
        maintenanceFrequencyDays = 30;
        priority = 'high';
        estimatedCost = 1500;
        break;
      case 'needs_repair':
        maintenanceFrequencyDays = 7;
        priority = 'critical';
        estimatedCost = 2000;
        break;
      case 'beyond_repair':
        maintenanceFrequencyDays = 1;
        priority = 'critical';
        estimatedCost = 5000;
        break;
    }

    // Adjust based on age
    if (ageInYears > 5) {
      maintenanceFrequencyDays *= 0.7; // More frequent maintenance
      estimatedCost *= 1.5; // Higher costs
    }

    const nextMaintenanceDate = new Date(
      Date.now() + maintenanceFrequencyDays * 24 * 60 * 60 * 1000
    );

    return {
      nextMaintenanceDate,
      estimatedCost,
      priority,
    };
  },
};
