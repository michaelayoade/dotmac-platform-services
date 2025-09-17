import React, { useState } from 'react';
import { cn } from '@dotmac/primitives/utils/cn';
import type { BusinessIntelligenceInsight } from '../../types';

interface InsightsPanelProps {
  insights: BusinessIntelligenceInsight[];
  loading?: boolean;
  error?: string | null;
  onInsightClick?: (insight: BusinessIntelligenceInsight) => void;
  onResolve?: (insightId: string) => void;
  onDismiss?: (insightId: string) => void;
  className?: string;
  maxHeight?: string;
  showActions?: boolean;
}

const getSeverityColor = (severity: BusinessIntelligenceInsight['severity']) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low':
      return 'bg-blue-100 text-blue-800 border-blue-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getStatusColor = (status: BusinessIntelligenceInsight['status']) => {
  switch (status) {
    case 'new':
      return 'bg-green-500';
    case 'investigating':
      return 'bg-yellow-500';
    case 'resolved':
      return 'bg-gray-500';
    case 'dismissed':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
};

const getTypeIcon = (type: BusinessIntelligenceInsight['type']) => {
  switch (type) {
    case 'anomaly':
      return '⚠️';
    case 'trend':
      return '📈';
    case 'correlation':
      return '🔗';
    case 'prediction':
      return '🔮';
    case 'recommendation':
      return '💡';
    default:
      return '📊';
  }
};

export const InsightsPanel: React.FC<InsightsPanelProps> = ({
  insights,
  loading = false,
  error = null,
  onInsightClick,
  onResolve,
  onDismiss,
  className,
  maxHeight = '500px',
  showActions = true,
}) => {
  const [filter, setFilter] = useState<{
    severity?: string;
    type?: string;
    status?: string;
  }>({});

  const filteredInsights = insights.filter((insight) => {
    if (filter.severity && insight.severity !== filter.severity) return false;
    if (filter.type && insight.type !== filter.type) return false;
    if (filter.status && insight.status !== filter.status) return false;
    return true;
  });

  const groupedInsights = filteredInsights.reduce(
    (groups, insight) => {
      const key = insight.status;
      if (!groups[key]) groups[key] = [];
      groups[key].push(insight);
      return groups;
    },
    {} as Record<string, BusinessIntelligenceInsight[]>
  );

  const statusOrder = ['new', 'investigating', 'resolved', 'dismissed'];

  if (error) {
    return (
      <div className='text-center p-8'>
        <div className='text-red-600 mb-2'>
          <svg className='w-12 h-12 mx-auto mb-4' fill='currentColor' viewBox='0 0 20 20'>
            <path
              fillRule='evenodd'
              d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z'
              clipRule='evenodd'
            />
          </svg>
        </div>
        <p className='text-gray-600'>{error}</p>
      </div>
    );
  }

  return (
    <div className={cn('bg-white rounded-lg border', className)}>
      {/* Header */}
      <div className='p-4 border-b border-gray-200'>
        <div className='flex items-center justify-between mb-4'>
          <h3 className='text-lg font-semibold text-gray-900'>Business Insights</h3>
          <span className='text-sm text-gray-500'>
            {filteredInsights.length} insight{filteredInsights.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Filters */}
        <div className='flex flex-wrap gap-2'>
          <select
            value={filter.severity || ''}
            onChange={(e) => setFilter({ ...filter, severity: e.target.value || undefined })}
            className='text-sm border border-gray-300 rounded px-2 py-1'
          >
            <option value=''>All Severities</option>
            <option value='critical'>Critical</option>
            <option value='high'>High</option>
            <option value='medium'>Medium</option>
            <option value='low'>Low</option>
          </select>

          <select
            value={filter.type || ''}
            onChange={(e) => setFilter({ ...filter, type: e.target.value || undefined })}
            className='text-sm border border-gray-300 rounded px-2 py-1'
          >
            <option value=''>All Types</option>
            <option value='anomaly'>Anomaly</option>
            <option value='trend'>Trend</option>
            <option value='correlation'>Correlation</option>
            <option value='prediction'>Prediction</option>
            <option value='recommendation'>Recommendation</option>
          </select>

          <select
            value={filter.status || ''}
            onChange={(e) => setFilter({ ...filter, status: e.target.value || undefined })}
            className='text-sm border border-gray-300 rounded px-2 py-1'
          >
            <option value=''>All Statuses</option>
            <option value='new'>New</option>
            <option value='investigating'>Investigating</option>
            <option value='resolved'>Resolved</option>
            <option value='dismissed'>Dismissed</option>
          </select>
        </div>
      </div>

      {/* Content */}
      <div className='overflow-y-auto' style={{ maxHeight }}>
        {loading ? (
          <div className='p-4 space-y-4'>
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className='animate-pulse p-4 border rounded'>
                <div className='flex items-start space-x-3'>
                  <div className='w-6 h-6 bg-gray-200 rounded'></div>
                  <div className='flex-1 space-y-2'>
                    <div className='h-4 bg-gray-200 rounded w-3/4'></div>
                    <div className='h-3 bg-gray-200 rounded w-1/2'></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredInsights.length === 0 ? (
          <div className='text-center p-8 text-gray-500'>
            <svg
              className='w-12 h-12 mx-auto mb-4 text-gray-300'
              fill='currentColor'
              viewBox='0 0 20 20'
            >
              <path
                fillRule='evenodd'
                d='M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V8zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2z'
                clipRule='evenodd'
              />
            </svg>
            <p>No insights available</p>
          </div>
        ) : (
          <div className='p-4 space-y-6'>
            {statusOrder.map((status) => {
              if (!groupedInsights[status] || groupedInsights[status].length === 0) return null;

              return (
                <div key={status} className='space-y-3'>
                  <h4 className='text-sm font-medium text-gray-700 uppercase tracking-wider'>
                    {status} ({groupedInsights[status].length})
                  </h4>

                  {groupedInsights[status].map((insight) => (
                    <div
                      key={insight.id}
                      className={cn(
                        'p-4 border rounded-lg cursor-pointer transition-all hover:shadow-sm',
                        onInsightClick && 'hover:border-blue-300'
                      )}
                      onClick={() => onInsightClick?.(insight)}
                    >
                      <div className='flex items-start space-x-3'>
                        {/* Type Icon */}
                        <div className='text-xl' title={insight.type}>
                          {getTypeIcon(insight.type)}
                        </div>

                        {/* Content */}
                        <div className='flex-1 min-w-0'>
                          <div className='flex items-start justify-between'>
                            <div className='flex-1 min-w-0'>
                              <h5 className='text-sm font-medium text-gray-900 truncate'>
                                {insight.title}
                              </h5>
                              <p className='text-sm text-gray-600 mt-1 line-clamp-2'>
                                {insight.description}
                              </p>
                            </div>

                            {/* Status and Severity */}
                            <div className='flex items-center space-x-2 ml-4'>
                              <div
                                className={cn(
                                  'w-2 h-2 rounded-full',
                                  getStatusColor(insight.status)
                                )}
                                title={insight.status}
                              />
                              <span
                                className={cn(
                                  'px-2 py-1 text-xs font-medium rounded-full border',
                                  getSeverityColor(insight.severity)
                                )}
                              >
                                {insight.severity}
                              </span>
                            </div>
                          </div>

                          {/* Metadata */}
                          <div className='flex items-center space-x-4 mt-3 text-xs text-gray-500'>
                            <span>Confidence: {Math.round(insight.confidence * 100)}%</span>
                            <span>Created: {insight.createdAt.toLocaleDateString()}</span>
                            {insight.resolvedAt && (
                              <span>Resolved: {insight.resolvedAt.toLocaleDateString()}</span>
                            )}
                          </div>

                          {/* Actions */}
                          {showActions && insight.actions && insight.actions.length > 0 && (
                            <div className='mt-3 flex flex-wrap gap-2'>
                              {insight.actions.map((action, index) => (
                                <span
                                  key={index}
                                  className={cn(
                                    'px-2 py-1 text-xs rounded-full',
                                    action.priority === 'high' && 'bg-red-100 text-red-700',
                                    action.priority === 'medium' && 'bg-yellow-100 text-yellow-700',
                                    action.priority === 'low' && 'bg-green-100 text-green-700'
                                  )}
                                >
                                  {action.type}: {action.description}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Action Buttons */}
                          {showActions &&
                            insight.status !== 'resolved' &&
                            insight.status !== 'dismissed' && (
                              <div className='flex space-x-2 mt-3'>
                                {onResolve && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onResolve(insight.id);
                                    }}
                                    className='px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700'
                                  >
                                    Resolve
                                  </button>
                                )}
                                {onDismiss && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onDismiss(insight.id);
                                    }}
                                    className='px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700'
                                  >
                                    Dismiss
                                  </button>
                                )}
                              </div>
                            )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
