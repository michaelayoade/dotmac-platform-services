import React, { createContext, useReducer, useCallback, useEffect } from 'react';
import { AnalyticsService } from '../services/AnalyticsService';
import type {
  AnalyticsContextValue,
  AnalyticsDashboard,
  AnalyticsReport,
  BusinessIntelligenceInsight,
  DashboardWidget,
  AnalyticsQuery,
  DataExport,
} from '../types';

// State interface
interface AnalyticsState {
  dashboards: AnalyticsDashboard[];
  currentDashboard: AnalyticsDashboard | null;
  reports: AnalyticsReport[];
  insights: BusinessIntelligenceInsight[];
  isLoading: boolean;
  isDashboardLoading: boolean;
  isReportLoading: boolean;
  error: string | null;
}

// Action types
type AnalyticsAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_DASHBOARD_LOADING'; payload: boolean }
  | { type: 'SET_REPORT_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_DASHBOARDS'; payload: AnalyticsDashboard[] }
  | { type: 'SET_CURRENT_DASHBOARD'; payload: AnalyticsDashboard | null }
  | { type: 'UPDATE_DASHBOARD'; payload: AnalyticsDashboard }
  | { type: 'DELETE_DASHBOARD'; payload: string }
  | { type: 'SET_REPORTS'; payload: AnalyticsReport[] }
  | { type: 'UPDATE_REPORT'; payload: AnalyticsReport }
  | { type: 'DELETE_REPORT'; payload: string }
  | { type: 'SET_INSIGHTS'; payload: BusinessIntelligenceInsight[] }
  | { type: 'UPDATE_INSIGHT'; payload: BusinessIntelligenceInsight }
  | { type: 'RESET' };

// Initial state
const initialState: AnalyticsState = {
  dashboards: [],
  currentDashboard: null,
  reports: [],
  insights: [],
  isLoading: false,
  isDashboardLoading: false,
  isReportLoading: false,
  error: null,
};

// Reducer
const analyticsReducer = (state: AnalyticsState, action: AnalyticsAction): AnalyticsState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_DASHBOARD_LOADING':
      return { ...state, isDashboardLoading: action.payload };
    case 'SET_REPORT_LOADING':
      return { ...state, isReportLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'SET_DASHBOARDS':
      return { ...state, dashboards: action.payload };
    case 'SET_CURRENT_DASHBOARD':
      return { ...state, currentDashboard: action.payload };
    case 'UPDATE_DASHBOARD':
      return {
        ...state,
        dashboards: state.dashboards.map((d) => (d.id === action.payload.id ? action.payload : d)),
        currentDashboard:
          state.currentDashboard?.id === action.payload.id
            ? action.payload
            : state.currentDashboard,
      };
    case 'DELETE_DASHBOARD':
      return {
        ...state,
        dashboards: state.dashboards.filter((d) => d.id !== action.payload),
        currentDashboard:
          state.currentDashboard?.id === action.payload ? null : state.currentDashboard,
      };
    case 'SET_REPORTS':
      return { ...state, reports: action.payload };
    case 'UPDATE_REPORT':
      return {
        ...state,
        reports: state.reports.map((r) => (r.id === action.payload.id ? action.payload : r)),
      };
    case 'DELETE_REPORT':
      return {
        ...state,
        reports: state.reports.filter((r) => r.id !== action.payload),
      };
    case 'SET_INSIGHTS':
      return { ...state, insights: action.payload };
    case 'UPDATE_INSIGHT':
      return {
        ...state,
        insights: state.insights.map((i) => (i.id === action.payload.id ? action.payload : i)),
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
};

// Context
export const AnalyticsContext = createContext<AnalyticsContextValue | null>(null);

// Provider component
interface AnalyticsProviderProps {
  children: React.ReactNode;
  config?: {
    apiEndpoint?: string;
    realTimeEndpoint?: string;
    defaultRefreshInterval?: number;
    enableRealTime?: boolean;
  };
}

export const AnalyticsProvider: React.FC<AnalyticsProviderProps> = ({ children, config = {} }) => {
  const [state, dispatch] = useReducer(analyticsReducer, initialState);

  // Initialize service with config
  useEffect(() => {
    if (config.apiEndpoint) {
      // Configure AnalyticsService if needed
    }
  }, [config]);

  // Dashboard actions
  const createDashboard = useCallback(
    async (dashboardData: Omit<AnalyticsDashboard, 'id' | 'createdAt' | 'updatedAt'>) => {
      try {
        dispatch({ type: 'SET_DASHBOARD_LOADING', payload: true });
        const dashboardId = await AnalyticsService.createDashboard(dashboardData);

        // Refresh dashboards
        const dashboards = await AnalyticsService.getDashboards();
        dispatch({ type: 'SET_DASHBOARDS', payload: dashboards });

        return dashboardId;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to create dashboard';
        dispatch({ type: 'SET_ERROR', payload: message });
        throw error;
      } finally {
        dispatch({ type: 'SET_DASHBOARD_LOADING', payload: false });
      }
    },
    []
  );

  const updateDashboard = useCallback(async (id: string, updates: Partial<AnalyticsDashboard>) => {
    try {
      dispatch({ type: 'SET_DASHBOARD_LOADING', payload: true });
      await AnalyticsService.updateDashboard(id, updates);

      // Refresh dashboards
      const dashboards = await AnalyticsService.getDashboards();
      dispatch({ type: 'SET_DASHBOARDS', payload: dashboards });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update dashboard';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw error;
    } finally {
      dispatch({ type: 'SET_DASHBOARD_LOADING', payload: false });
    }
  }, []);

  const deleteDashboard = useCallback(async (id: string) => {
    try {
      dispatch({ type: 'SET_DASHBOARD_LOADING', payload: true });
      await AnalyticsService.deleteDashboard(id);
      dispatch({ type: 'DELETE_DASHBOARD', payload: id });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete dashboard';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw error;
    } finally {
      dispatch({ type: 'SET_DASHBOARD_LOADING', payload: false });
    }
  }, []);

  const duplicateDashboard = useCallback(
    async (id: string, name?: string) => {
      try {
        const originalDashboard = state.dashboards.find((d) => d.id === id);
        if (!originalDashboard) throw new Error('Dashboard not found');

        const duplicatedData = {
          ...originalDashboard,
          name: name || `${originalDashboard.name} (Copy)`,
          id: undefined,
          createdAt: undefined,
          updatedAt: undefined,
        };

        return await createDashboard(duplicatedData);
      } catch (error) {
        throw error;
      }
    },
    [state.dashboards, createDashboard]
  );

  // Widget actions
  const addWidget = useCallback(
    async (dashboardId: string, widget: Omit<DashboardWidget, 'id'>) => {
      try {
        await AnalyticsService.addWidget(dashboardId, widget);

        // Refresh current dashboard if it's the one being updated
        if (state.currentDashboard?.id === dashboardId) {
          const updatedDashboard = await AnalyticsService.getDashboard(dashboardId);
          dispatch({ type: 'SET_CURRENT_DASHBOARD', payload: updatedDashboard });
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to add widget';
        dispatch({ type: 'SET_ERROR', payload: message });
        throw error;
      }
    },
    [state.currentDashboard]
  );

  const updateWidget = useCallback(
    async (dashboardId: string, widgetId: string, updates: Partial<DashboardWidget>) => {
      try {
        await AnalyticsService.updateWidget(dashboardId, widgetId, updates);

        // Refresh current dashboard if it's the one being updated
        if (state.currentDashboard?.id === dashboardId) {
          const updatedDashboard = await AnalyticsService.getDashboard(dashboardId);
          dispatch({ type: 'SET_CURRENT_DASHBOARD', payload: updatedDashboard });
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to update widget';
        dispatch({ type: 'SET_ERROR', payload: message });
        throw error;
      }
    },
    [state.currentDashboard]
  );

  const removeWidget = useCallback(
    async (dashboardId: string, widgetId: string) => {
      try {
        await AnalyticsService.removeWidget(dashboardId, widgetId);

        // Refresh current dashboard if it's the one being updated
        if (state.currentDashboard?.id === dashboardId) {
          const updatedDashboard = await AnalyticsService.getDashboard(dashboardId);
          dispatch({ type: 'SET_CURRENT_DASHBOARD', payload: updatedDashboard });
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to remove widget';
        dispatch({ type: 'SET_ERROR', payload: message });
        throw error;
      }
    },
    [state.currentDashboard]
  );

  // Data operations
  const executeQuery = useCallback(async (query: AnalyticsQuery) => {
    try {
      return await AnalyticsService.executeQuery(query);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to execute query';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw error;
    }
  }, []);

  const exportData = useCallback(
    async (config: Omit<DataExport, 'id' | 'status' | 'requestedAt'>) => {
      try {
        return await AnalyticsService.exportData(config);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to export data';
        dispatch({ type: 'SET_ERROR', payload: message });
        throw error;
      }
    },
    []
  );

  // Report actions
  const generateReport = useCallback(async (reportId: string) => {
    try {
      dispatch({ type: 'SET_REPORT_LOADING', payload: true });
      return await AnalyticsService.generateReport(reportId);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to generate report';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw error;
    } finally {
      dispatch({ type: 'SET_REPORT_LOADING', payload: false });
    }
  }, []);

  const scheduleReport = useCallback(async (report: Omit<AnalyticsReport, 'id'>) => {
    try {
      dispatch({ type: 'SET_REPORT_LOADING', payload: true });
      const reportId = await AnalyticsService.createReport(report);

      // Refresh reports
      const reports = await AnalyticsService.getReports();
      dispatch({ type: 'SET_REPORTS', payload: reports });

      return reportId;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to schedule report';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw error;
    } finally {
      dispatch({ type: 'SET_REPORT_LOADING', payload: false });
    }
  }, []);

  // Real-time operations
  const subscribeToMetric = useCallback((metricId: string, callback: (data: any) => void) => {
    try {
      return AnalyticsService.subscribeToMetric(metricId, callback);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to subscribe to metric';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw error;
    }
  }, []);

  // Insights operations
  const getInsights = useCallback(async (filters?: { category?: string; severity?: string }) => {
    try {
      return await AnalyticsService.getInsights(filters);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to get insights';
      dispatch({ type: 'SET_ERROR', payload: message });
      throw error;
    }
  }, []);

  const resolveInsight = useCallback(
    async (id: string) => {
      try {
        await AnalyticsService.resolveInsight(id);

        // Update local state
        const updatedInsight = state.insights.find((i) => i.id === id);
        if (updatedInsight) {
          dispatch({
            type: 'UPDATE_INSIGHT',
            payload: { ...updatedInsight, status: 'resolved', resolvedAt: new Date() },
          });
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to resolve insight';
        dispatch({ type: 'SET_ERROR', payload: message });
        throw error;
      }
    },
    [state.insights]
  );

  // Utility actions
  const refresh = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      // Fetch all data in parallel
      const [dashboards, reports, insights] = await Promise.all([
        AnalyticsService.getDashboards(),
        AnalyticsService.getReports(),
        AnalyticsService.getInsights(),
      ]);

      dispatch({ type: 'SET_DASHBOARDS', payload: dashboards });
      dispatch({ type: 'SET_REPORTS', payload: reports });
      dispatch({ type: 'SET_INSIGHTS', payload: insights });

      // Update current dashboard if one is selected
      if (state.currentDashboard) {
        const currentDashboard = dashboards.find((d) => d.id === state.currentDashboard!.id);
        dispatch({ type: 'SET_CURRENT_DASHBOARD', payload: currentDashboard || null });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to refresh data';
      dispatch({ type: 'SET_ERROR', payload: message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.currentDashboard]);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  // Initial data loading
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Context value
  const contextValue: AnalyticsContextValue = {
    // State
    dashboards: state.dashboards,
    currentDashboard: state.currentDashboard,
    reports: state.reports,
    insights: state.insights,
    isLoading: state.isLoading,
    isDashboardLoading: state.isDashboardLoading,
    isReportLoading: state.isReportLoading,
    error: state.error,

    // Actions
    actions: {
      // Dashboard management
      createDashboard,
      updateDashboard,
      deleteDashboard,
      duplicateDashboard,

      // Widget management
      addWidget,
      updateWidget,
      removeWidget,

      // Data operations
      executeQuery,
      exportData,

      // Reports
      generateReport,
      scheduleReport,

      // Real-time data
      subscribeToMetric,

      // Insights
      getInsights,
      resolveInsight,

      // Utilities
      refresh,
      reset,
    },
  };

  return <AnalyticsContext.Provider value={contextValue}>{children}</AnalyticsContext.Provider>;
};
