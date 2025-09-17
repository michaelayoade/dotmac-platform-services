import type {
  MaintenanceSchedule,
  MaintenanceRecord,
  MaintenanceFrequency,
  MaintenanceType,
  MaintenancePriority,
  MaintenanceStatus,
  Asset,
} from '../types';

export const maintenanceHelpers = {
  calculateNextDueDate: (
    frequency: MaintenanceFrequency,
    frequencyValue: number,
    lastCompletedDate?: Date
  ): Date => {
    const baseDate = lastCompletedDate || new Date();
    const nextDate = new Date(baseDate);

    switch (frequency) {
      case 'daily':
        nextDate.setDate(nextDate.getDate() + frequencyValue);
        break;
      case 'weekly':
        nextDate.setDate(nextDate.getDate() + frequencyValue * 7);
        break;
      case 'monthly':
        nextDate.setMonth(nextDate.getMonth() + frequencyValue);
        break;
      case 'quarterly':
        nextDate.setMonth(nextDate.getMonth() + frequencyValue * 3);
        break;
      case 'semi_annual':
        nextDate.setMonth(nextDate.getMonth() + frequencyValue * 6);
        break;
      case 'annual':
        nextDate.setFullYear(nextDate.getFullYear() + frequencyValue);
        break;
      case 'custom':
        // For custom frequency, treat frequency_value as days
        nextDate.setDate(nextDate.getDate() + frequencyValue);
        break;
    }

    return nextDate;
  },

  getMaintenanceTypeIcon: (type: MaintenanceType): string => {
    switch (type) {
      case 'preventive':
        return '🛡️';
      case 'corrective':
        return '🔧';
      case 'predictive':
        return '📊';
      case 'condition_based':
        return '📈';
      case 'calibration':
        return '⚖️';
      case 'inspection':
        return '🔍';
      case 'upgrade':
        return '⬆️';
      case 'replacement':
        return '🔄';
      default:
        return '🔧';
    }
  },

  getMaintenanceTypeColor: (type: MaintenanceType): string => {
    switch (type) {
      case 'preventive':
        return '#22c55e';
      case 'corrective':
        return '#ef4444';
      case 'predictive':
        return '#3b82f6';
      case 'condition_based':
        return '#8b5cf6';
      case 'calibration':
        return '#f59e0b';
      case 'inspection':
        return '#06b6d4';
      case 'upgrade':
        return '#10b981';
      case 'replacement':
        return '#f97316';
      default:
        return '#6b7280';
    }
  },

  isMaintenanceOverdue: (schedule: MaintenanceSchedule): boolean => {
    return new Date(schedule.next_due_date) < new Date();
  },

  isDueSoon: (schedule: MaintenanceSchedule, daysAhead: number = 7): boolean => {
    const dueDate = new Date(schedule.next_due_date);
    const checkDate = new Date(Date.now() + daysAhead * 24 * 60 * 60 * 1000);
    return dueDate <= checkDate;
  },

  getDaysUntilDue: (schedule: MaintenanceSchedule): number => {
    const dueDate = new Date(schedule.next_due_date);
    const today = new Date();
    const diffTime = dueDate.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  },

  getMaintenanceUrgency: (
    schedule: MaintenanceSchedule
  ): 'overdue' | 'due_today' | 'due_soon' | 'scheduled' => {
    const daysUntilDue = maintenanceHelpers.getDaysUntilDue(schedule);

    if (daysUntilDue < 0) return 'overdue';
    if (daysUntilDue === 0) return 'due_today';
    if (daysUntilDue <= 7) return 'due_soon';
    return 'scheduled';
  },

  getUrgencyColor: (urgency: 'overdue' | 'due_today' | 'due_soon' | 'scheduled'): string => {
    switch (urgency) {
      case 'overdue':
        return '#dc2626';
      case 'due_today':
        return '#ef4444';
      case 'due_soon':
        return '#f59e0b';
      case 'scheduled':
        return '#22c55e';
      default:
        return '#6b7280';
    }
  },

  calculateMaintenanceCost: (
    records: MaintenanceRecord[]
  ): {
    totalCost: number;
    averageCost: number;
    costByType: Record<MaintenanceType, number>;
    monthlyTrend: Array<{ month: string; cost: number }>;
  } => {
    const totalCost = records.reduce((sum, record) => sum + (record.actual_cost || 0), 0);
    const averageCost = records.length > 0 ? totalCost / records.length : 0;

    const costByType = records.reduce(
      (acc, record) => {
        acc[record.maintenance_type] =
          (acc[record.maintenance_type] || 0) + (record.actual_cost || 0);
        return acc;
      },
      {} as Record<MaintenanceType, number>
    );

    // Calculate monthly trend for the last 12 months
    const monthlyTrend: Array<{ month: string; cost: number }> = [];
    const now = new Date();

    for (let i = 11; i >= 0; i--) {
      const month = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthStr = month.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

      const monthCost = records
        .filter((record) => {
          const recordDate = new Date(record.performed_date);
          return (
            recordDate.getMonth() === month.getMonth() &&
            recordDate.getFullYear() === month.getFullYear()
          );
        })
        .reduce((sum, record) => sum + (record.actual_cost || 0), 0);

      monthlyTrend.push({ month: monthStr, cost: monthCost });
    }

    return {
      totalCost,
      averageCost,
      costByType,
      monthlyTrend,
    };
  },

  getMaintenanceEfficiency: (
    records: MaintenanceRecord[]
  ): {
    onTimeCompletion: number;
    averageCompletionTime: number;
    preventiveVsCorrective: { preventive: number; corrective: number };
    repeatIssues: number;
  } => {
    if (records.length === 0) {
      return {
        onTimeCompletion: 0,
        averageCompletionTime: 0,
        preventiveVsCorrective: { preventive: 0, corrective: 0 },
        repeatIssues: 0,
      };
    }

    // Calculate on-time completion rate (assuming there's a scheduled date)
    const onTimeCount = records.filter((record) => record.status === 'completed').length;
    const onTimeCompletion = (onTimeCount / records.length) * 100;

    // Calculate average completion time
    const totalTime = records.reduce((sum, record) => sum + record.duration_minutes, 0);
    const averageCompletionTime = totalTime / records.length;

    // Calculate preventive vs corrective ratio
    const preventiveCount = records.filter((r) => r.maintenance_type === 'preventive').length;
    const correctiveCount = records.filter((r) => r.maintenance_type === 'corrective').length;
    const preventiveVsCorrective = {
      preventive: preventiveCount,
      corrective: correctiveCount,
    };

    // Calculate repeat issues (simplified - assets with multiple corrective maintenances)
    const assetMaintenanceCount = records.reduce(
      (acc, record) => {
        if (record.maintenance_type === 'corrective') {
          acc[record.asset_id] = (acc[record.asset_id] || 0) + 1;
        }
        return acc;
      },
      {} as Record<string, number>
    );

    const repeatIssues = Object.values(assetMaintenanceCount).filter((count) => count > 1).length;

    return {
      onTimeCompletion,
      averageCompletionTime,
      preventiveVsCorrective,
      repeatIssues,
    };
  },

  generateMaintenanceReport: (
    asset: Asset,
    schedules: MaintenanceSchedule[],
    records: MaintenanceRecord[]
  ) => {
    const assetSchedules = schedules.filter((s) => s.asset_id === asset.id);
    const assetRecords = records.filter((r) => r.asset_id === asset.id);

    const overdueSchedules = assetSchedules.filter((s) =>
      maintenanceHelpers.isMaintenanceOverdue(s)
    );
    const upcomingSchedules = assetSchedules.filter((s) => maintenanceHelpers.isDueSoon(s, 30));

    const costAnalysis = maintenanceHelpers.calculateMaintenanceCost(assetRecords);
    const efficiency = maintenanceHelpers.getMaintenanceEfficiency(assetRecords);

    const lastMaintenance = assetRecords.sort(
      (a, b) => new Date(b.performed_date).getTime() - new Date(a.performed_date).getTime()
    )[0];

    return {
      asset,
      summary: {
        totalSchedules: assetSchedules.length,
        overdueSchedules: overdueSchedules.length,
        upcomingSchedules: upcomingSchedules.length,
        totalRecords: assetRecords.length,
        lastMaintenanceDate: lastMaintenance?.performed_date,
      },
      costAnalysis,
      efficiency,
      recommendations: maintenanceHelpers.generateMaintenanceRecommendations(
        asset,
        assetRecords,
        overdueSchedules
      ),
    };
  },

  generateMaintenanceRecommendations: (
    asset: Asset,
    records: MaintenanceRecord[],
    overdueSchedules: MaintenanceSchedule[]
  ): string[] => {
    const recommendations: string[] = [];

    // Check for overdue maintenance
    if (overdueSchedules.length > 0) {
      recommendations.push(
        `${overdueSchedules.length} maintenance task(s) are overdue. Schedule immediately to prevent downtime.`
      );
    }

    // Check for frequent corrective maintenance
    const correctiveRecords = records.filter((r) => r.maintenance_type === 'corrective');
    if (correctiveRecords.length > 2) {
      recommendations.push(
        'High frequency of corrective maintenance detected. Consider increasing preventive maintenance intervals.'
      );
    }

    // Check asset age vs maintenance frequency
    if (asset.purchase_date) {
      const ageInYears =
        (Date.now() - new Date(asset.purchase_date).getTime()) / (1000 * 60 * 60 * 24 * 365);
      const recentRecords = records.filter(
        (r) => (Date.now() - new Date(r.performed_date).getTime()) / (1000 * 60 * 60 * 24) <= 365
      );

      if (ageInYears > 5 && recentRecords.length < 2) {
        recommendations.push(
          'Asset is aging and requires more frequent maintenance. Consider quarterly inspections.'
        );
      }
    }

    // Check for condition-based recommendations
    switch (asset.condition) {
      case 'poor':
        recommendations.push(
          'Asset condition is poor. Schedule comprehensive inspection and consider replacement planning.'
        );
        break;
      case 'needs_repair':
        recommendations.push(
          'Asset needs repair. Address immediately to prevent further deterioration.'
        );
        break;
      case 'beyond_repair':
        recommendations.push('Asset is beyond repair. Initiate replacement process immediately.');
        break;
    }

    // Check maintenance costs
    const costAnalysis = maintenanceHelpers.calculateMaintenanceCost(records);
    if (asset.purchase_price && costAnalysis.totalCost > asset.purchase_price * 0.5) {
      recommendations.push(
        'Total maintenance costs exceed 50% of asset value. Evaluate replacement options.'
      );
    }

    return recommendations;
  },

  createMaintenanceCalendar: (schedules: MaintenanceSchedule[], records: MaintenanceRecord[]) => {
    const calendarEvents = [];

    // Add scheduled maintenance
    schedules.forEach((schedule) => {
      const urgency = maintenanceHelpers.getMaintenanceUrgency(schedule);
      calendarEvents.push({
        id: `schedule-${schedule.id}`,
        title: `${schedule.maintenance_type} - ${schedule.description}`,
        date: schedule.next_due_date,
        type: 'scheduled',
        urgency,
        priority: schedule.priority,
        assetId: schedule.asset_id,
        duration: schedule.estimated_duration,
        cost: schedule.estimated_cost,
      });
    });

    // Add completed maintenance records
    records.forEach((record) => {
      calendarEvents.push({
        id: `record-${record.id}`,
        title: `${record.maintenance_type} - Completed`,
        date: record.performed_date,
        type: 'completed',
        assetId: record.asset_id,
        duration: record.duration_minutes,
        cost: record.actual_cost,
      });
    });

    return calendarEvents.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  },

  validateMaintenanceSchedule: (schedule: Partial<MaintenanceSchedule>): string[] => {
    const errors: string[] = [];

    if (!schedule.asset_id) {
      errors.push('Asset is required');
    }

    if (!schedule.maintenance_type) {
      errors.push('Maintenance type is required');
    }

    if (!schedule.frequency) {
      errors.push('Frequency is required');
    }

    if (!schedule.frequency_value || schedule.frequency_value <= 0) {
      errors.push('Frequency value must be greater than 0');
    }

    if (!schedule.next_due_date) {
      errors.push('Next due date is required');
    }

    if (schedule.next_due_date && new Date(schedule.next_due_date) < new Date()) {
      errors.push('Next due date cannot be in the past');
    }

    if (!schedule.estimated_duration || schedule.estimated_duration <= 0) {
      errors.push('Estimated duration must be greater than 0');
    }

    if (!schedule.priority) {
      errors.push('Priority is required');
    }

    if (!schedule.description || schedule.description.trim().length === 0) {
      errors.push('Description is required');
    }

    return errors;
  },
};
