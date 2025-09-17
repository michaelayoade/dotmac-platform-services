import type { DataPoint, TimeSeries, TimeGranularity } from '../types';

export const aggregateData = (
  data: DataPoint[],
  method: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'median' | 'first' | 'last'
): number => {
  if (data.length === 0) return 0;

  const values = data.map((point) => point.value);

  switch (method) {
    case 'sum':
      return values.reduce((sum, value) => sum + value, 0);

    case 'avg':
      return values.reduce((sum, value) => sum + value, 0) / values.length;

    case 'min':
      return Math.min(...values);

    case 'max':
      return Math.max(...values);

    case 'count':
      return values.length;

    case 'median':
      const sorted = [...values].sort((a, b) => a - b);
      const middle = Math.floor(sorted.length / 2);
      return sorted.length % 2 === 0 ? (sorted[middle - 1] + sorted[middle]) / 2 : sorted[middle];

    case 'first':
      return values[0];

    case 'last':
      return values[values.length - 1];

    default:
      return 0;
  }
};

export const groupByTimeWindow = (
  data: DataPoint[],
  granularity: TimeGranularity,
  aggregationMethod: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'median' = 'avg'
): DataPoint[] => {
  if (data.length === 0) return [];

  const groups = new Map<string, DataPoint[]>();

  data.forEach((point) => {
    const timeKey = getTimeWindowKey(point.timestamp, granularity);

    if (!groups.has(timeKey)) {
      groups.set(timeKey, []);
    }
    groups.get(timeKey)!.push(point);
  });

  const result: DataPoint[] = [];

  for (const [timeKey, groupData] of groups) {
    const aggregatedValue = aggregateData(groupData, aggregationMethod);
    const timestamp = parseTimeWindowKey(timeKey, granularity);

    result.push({
      timestamp,
      value: aggregatedValue,
      metadata: {
        aggregated: true,
        method: aggregationMethod,
        granularity,
        originalCount: groupData.length,
      },
    });
  }

  return result.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
};

export const getTimeWindowKey = (date: Date, granularity: TimeGranularity): string => {
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();
  const hour = date.getHours();
  const minute = date.getMinutes();

  switch (granularity) {
    case 'minute':
      return `${year}-${month}-${day}-${hour}-${minute}`;

    case 'hour':
      return `${year}-${month}-${day}-${hour}`;

    case 'day':
      return `${year}-${month}-${day}`;

    case 'week':
      const weekStart = new Date(date);
      weekStart.setDate(date.getDate() - date.getDay()); // Start of week (Sunday)
      return `${weekStart.getFullYear()}-W${getWeekNumber(weekStart)}`;

    case 'month':
      return `${year}-${month}`;

    case 'quarter':
      const quarter = Math.floor(month / 3);
      return `${year}-Q${quarter}`;

    case 'year':
      return `${year}`;

    default:
      return `${year}-${month}-${day}`;
  }
};

export const parseTimeWindowKey = (key: string, granularity: TimeGranularity): Date => {
  const parts = key.split('-');

  switch (granularity) {
    case 'minute': {
      const [year, month, day, hour, minute] = parts.map(Number);
      return new Date(year, month, day, hour, minute);
    }

    case 'hour': {
      const [year, month, day, hour] = parts.map(Number);
      return new Date(year, month, day, hour);
    }

    case 'day': {
      const [year, month, day] = parts.map(Number);
      return new Date(year, month, day);
    }

    case 'week': {
      const [year, weekPart] = parts;
      const weekNumber = parseInt(weekPart.substring(1)); // Remove 'W' prefix
      const date = new Date(parseInt(year), 0, 1);
      date.setDate(date.getDate() + weekNumber * 7);
      return date;
    }

    case 'month': {
      const [year, month] = parts.map(Number);
      return new Date(year, month, 1);
    }

    case 'quarter': {
      const [year, quarterPart] = parts;
      const quarter = parseInt(quarterPart.substring(1)); // Remove 'Q' prefix
      return new Date(parseInt(year), quarter * 3, 1);
    }

    case 'year': {
      const year = parseInt(parts[0]);
      return new Date(year, 0, 1);
    }

    default: {
      const [year, month, day] = parts.map(Number);
      return new Date(year, month, day);
    }
  }
};

export const getWeekNumber = (date: Date): number => {
  const startOfYear = new Date(date.getFullYear(), 0, 1);
  const pastDaysOfYear = (date.getTime() - startOfYear.getTime()) / 86400000;
  return Math.ceil((pastDaysOfYear + startOfYear.getDay() + 1) / 7);
};

export const fillMissingDataPoints = (
  data: DataPoint[],
  granularity: TimeGranularity,
  fillValue: number = 0,
  startDate?: Date,
  endDate?: Date
): DataPoint[] => {
  if (data.length === 0) return [];

  const sortedData = [...data].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  const start = startDate || sortedData[0].timestamp;
  const end = endDate || sortedData[sortedData.length - 1].timestamp;

  const result: DataPoint[] = [];
  const existingData = new Map<string, DataPoint>();

  // Index existing data by time window
  sortedData.forEach((point) => {
    const key = getTimeWindowKey(point.timestamp, granularity);
    existingData.set(key, point);
  });

  // Generate all time windows between start and end
  const current = new Date(start);

  while (current <= end) {
    const key = getTimeWindowKey(current, granularity);

    if (existingData.has(key)) {
      result.push(existingData.get(key)!);
    } else {
      result.push({
        timestamp: new Date(current),
        value: fillValue,
        metadata: { filled: true },
      });
    }

    // Advance to next time window
    incrementTimeWindow(current, granularity);
  }

  return result;
};

export const incrementTimeWindow = (date: Date, granularity: TimeGranularity): void => {
  switch (granularity) {
    case 'minute':
      date.setMinutes(date.getMinutes() + 1);
      break;
    case 'hour':
      date.setHours(date.getHours() + 1);
      break;
    case 'day':
      date.setDate(date.getDate() + 1);
      break;
    case 'week':
      date.setDate(date.getDate() + 7);
      break;
    case 'month':
      date.setMonth(date.getMonth() + 1);
      break;
    case 'quarter':
      date.setMonth(date.getMonth() + 3);
      break;
    case 'year':
      date.setFullYear(date.getFullYear() + 1);
      break;
  }
};

export const calculateRollingAggregation = (
  data: DataPoint[],
  windowSize: number,
  method: 'sum' | 'avg' | 'min' | 'max' = 'avg'
): DataPoint[] => {
  if (data.length < windowSize || windowSize <= 0) return data;

  const result: DataPoint[] = [];

  for (let i = windowSize - 1; i < data.length; i++) {
    const window = data.slice(i - windowSize + 1, i + 1);
    const aggregatedValue = aggregateData(window, method);

    result.push({
      timestamp: data[i].timestamp,
      value: aggregatedValue,
      metadata: {
        rollingAggregation: true,
        method,
        windowSize,
      },
    });
  }

  return result;
};

export const resampleTimeSeries = (
  timeSeries: TimeSeries,
  targetGranularity: TimeGranularity,
  aggregationMethod: 'sum' | 'avg' | 'min' | 'max' = 'avg'
): TimeSeries => {
  const resampledData = groupByTimeWindow(timeSeries.data, targetGranularity, aggregationMethod);

  return {
    ...timeSeries,
    data: resampledData,
    resolution: targetGranularity,
    aggregation: aggregationMethod,
  };
};

export const combineTimeSeries = (
  series: TimeSeries[],
  method: 'sum' | 'avg' | 'weighted_avg' = 'avg',
  weights?: number[]
): TimeSeries => {
  if (series.length === 0) {
    return {
      metricId: 'combined',
      data: [],
      startTime: new Date(),
      endTime: new Date(),
      resolution: 'day',
    };
  }

  if (series.length === 1) {
    return series[0];
  }

  // Ensure all series have the same resolution
  const targetResolution = series[0].resolution;
  const alignedSeries = series.map((s) =>
    s.resolution === targetResolution ? s : resampleTimeSeries(s, targetResolution)
  );

  // Get all unique timestamps
  const allTimestamps = new Set<number>();
  alignedSeries.forEach((s) => {
    s.data.forEach((point) => allTimestamps.add(point.timestamp.getTime()));
  });

  const sortedTimestamps = Array.from(allTimestamps).sort((a, b) => a - b);

  // Combine data points
  const combinedData: DataPoint[] = sortedTimestamps.map((timestamp) => {
    const date = new Date(timestamp);
    const values: number[] = [];

    alignedSeries.forEach((s, index) => {
      const point = s.data.find((p) => p.timestamp.getTime() === timestamp);
      if (point) {
        if (method === 'weighted_avg' && weights && weights[index]) {
          values.push(point.value * weights[index]);
        } else {
          values.push(point.value);
        }
      }
    });

    let combinedValue = 0;
    if (values.length > 0) {
      switch (method) {
        case 'sum':
          combinedValue = values.reduce((sum, val) => sum + val, 0);
          break;
        case 'avg':
          combinedValue = values.reduce((sum, val) => sum + val, 0) / values.length;
          break;
        case 'weighted_avg':
          const totalWeight = weights ? weights.reduce((sum, w) => sum + w, 0) : values.length;
          combinedValue = values.reduce((sum, val) => sum + val, 0) / totalWeight;
          break;
      }
    }

    return {
      timestamp: date,
      value: combinedValue,
      metadata: {
        combined: true,
        method,
        sourceCount: values.length,
      },
    };
  });

  return {
    metricId: 'combined',
    data: combinedData,
    startTime: new Date(sortedTimestamps[0]),
    endTime: new Date(sortedTimestamps[sortedTimestamps.length - 1]),
    resolution: targetResolution,
    aggregation: method,
  };
};
