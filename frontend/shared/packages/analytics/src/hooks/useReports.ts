import { useState, useEffect, useCallback } from 'react';
import { AnalyticsService } from '../services/AnalyticsService';
import type { AnalyticsReport } from '../types';

interface UseReportsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const useReports = (options: UseReportsOptions = {}) => {
  const [reports, setReports] = useState<AnalyticsReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState<Record<string, boolean>>({});

  const {
    autoRefresh = false,
    refreshInterval = 60000, // 1 minute
  } = options;

  const fetchReports = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await AnalyticsService.getReports();
      setReports(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch reports';
      setError(errorMessage);
      console.error('Error fetching reports:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchReports, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchReports]);

  const createReport = useCallback(
    async (reportData: Omit<AnalyticsReport, 'id'>) => {
      try {
        const reportId = await AnalyticsService.createReport(reportData);
        await fetchReports(); // Refresh the list
        return reportId;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to create report';
        throw new Error(errorMessage);
      }
    },
    [fetchReports]
  );

  const updateReport = useCallback(
    async (id: string, updates: Partial<AnalyticsReport>) => {
      try {
        await AnalyticsService.updateReport(id, updates);
        await fetchReports(); // Refresh the list
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update report';
        throw new Error(errorMessage);
      }
    },
    [fetchReports]
  );

  const deleteReport = useCallback(async (id: string) => {
    try {
      await AnalyticsService.deleteReport(id);
      setReports((prev) => prev.filter((report) => report.id !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete report';
      throw new Error(errorMessage);
    }
  }, []);

  const generateReport = useCallback(
    async (id: string) => {
      try {
        setIsGenerating((prev) => ({ ...prev, [id]: true }));
        const downloadUrl = await AnalyticsService.generateReport(id);
        await fetchReports(); // Refresh to get updated lastGenerated time
        return downloadUrl;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to generate report';
        throw new Error(errorMessage);
      } finally {
        setIsGenerating((prev) => ({ ...prev, [id]: false }));
      }
    },
    [fetchReports]
  );

  const duplicateReport = useCallback(
    async (id: string, newName?: string) => {
      try {
        const originalReport = reports.find((r) => r.id === id);
        if (!originalReport) throw new Error('Report not found');

        const duplicatedReport = {
          ...originalReport,
          name: newName || `${originalReport.name} (Copy)`,
          id: undefined, // Will be generated
          isActive: false, // Start as inactive
        };

        const newId = await createReport(duplicatedReport);
        return newId;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to duplicate report';
        throw new Error(errorMessage);
      }
    },
    [reports, createReport]
  );

  const getReportById = useCallback(
    (id: string) => {
      return reports.find((report) => report.id === id);
    },
    [reports]
  );

  const getReportsByType = useCallback(
    (type: AnalyticsReport['type']) => {
      return reports.filter((report) => report.type === type);
    },
    [reports]
  );

  const getActiveReports = useCallback(() => {
    return reports.filter((report) => report.isActive);
  }, [reports]);

  const getScheduledReports = useCallback(() => {
    return reports.filter((report) => report.type === 'scheduled' && report.isActive);
  }, [reports]);

  const refresh = useCallback(() => {
    fetchReports();
  }, [fetchReports]);

  // Calculate summary statistics
  const summary = {
    total: reports.length,
    active: reports.filter((r) => r.isActive).length,
    scheduled: reports.filter((r) => r.type === 'scheduled').length,
    adHoc: reports.filter((r) => r.type === 'ad_hoc').length,
    byFormat: reports.reduce(
      (acc, report) => {
        acc[report.format] = (acc[report.format] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    ),
    lastGenerated:
      reports.length > 0
        ? reports
            .filter((r) => r.lastGenerated)
            .sort(
              (a, b) => (b.lastGenerated?.getTime() || 0) - (a.lastGenerated?.getTime() || 0)
            )[0]?.lastGenerated || null
        : null,
  };

  return {
    reports,
    isLoading,
    error,
    isGenerating,
    refresh,
    summary,
    createReport,
    updateReport,
    deleteReport,
    generateReport,
    duplicateReport,
    getReportById,
    getReportsByType,
    getActiveReports,
    getScheduledReports,
  };
};
