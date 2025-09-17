import type { DataPoint, TimeSeries } from '../types';

export const calculateTrend = (data: DataPoint[]): 'up' | 'down' | 'stable' => {
  if (data.length < 2) return 'stable';

  const recentData = data.slice(-10); // Look at last 10 points
  let upCount = 0;
  let downCount = 0;

  for (let i = 1; i < recentData.length; i++) {
    const current = recentData[i].value;
    const previous = recentData[i - 1].value;

    if (current > previous) upCount++;
    else if (current < previous) downCount++;
  }

  const threshold = recentData.length * 0.6; // 60% threshold

  if (upCount >= threshold) return 'up';
  if (downCount >= threshold) return 'down';
  return 'stable';
};

export const calculateGrowthRate = (current: number, previous: number): number => {
  if (previous === 0) return current > 0 ? 1 : 0;
  return (current - previous) / previous;
};

export const calculateMovingAverage = (data: DataPoint[], window: number): DataPoint[] => {
  if (data.length < window || window <= 0) return data;

  const result: DataPoint[] = [];

  for (let i = window - 1; i < data.length; i++) {
    const windowData = data.slice(i - window + 1, i + 1);
    const average = windowData.reduce((sum, point) => sum + point.value, 0) / window;

    result.push({
      timestamp: data[i].timestamp,
      value: average,
      metadata: { isMovingAverage: true, window },
    });
  }

  return result;
};

export const calculateVariance = (values: number[]): number => {
  if (values.length === 0) return 0;

  const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
  const squaredDiffs = values.map((val) => Math.pow(val - mean, 2));

  return squaredDiffs.reduce((sum, diff) => sum + diff, 0) / values.length;
};

export const calculateStandardDeviation = (values: number[]): number => {
  return Math.sqrt(calculateVariance(values));
};

export const calculatePercentile = (values: number[], percentile: number): number => {
  if (values.length === 0) return 0;

  const sorted = [...values].sort((a, b) => a - b);
  const index = (percentile / 100) * (sorted.length - 1);

  if (Number.isInteger(index)) {
    return sorted[index];
  } else {
    const lower = sorted[Math.floor(index)];
    const upper = sorted[Math.ceil(index)];
    return lower + (upper - lower) * (index - Math.floor(index));
  }
};

export const calculateCorrelation = (series1: DataPoint[], series2: DataPoint[]): number => {
  if (series1.length !== series2.length || series1.length === 0) return 0;

  const values1 = series1.map((p) => p.value);
  const values2 = series2.map((p) => p.value);

  const mean1 = values1.reduce((sum, val) => sum + val, 0) / values1.length;
  const mean2 = values2.reduce((sum, val) => sum + val, 0) / values2.length;

  let numerator = 0;
  let sumSquares1 = 0;
  let sumSquares2 = 0;

  for (let i = 0; i < values1.length; i++) {
    const diff1 = values1[i] - mean1;
    const diff2 = values2[i] - mean2;

    numerator += diff1 * diff2;
    sumSquares1 += diff1 * diff1;
    sumSquares2 += diff2 * diff2;
  }

  const denominator = Math.sqrt(sumSquares1 * sumSquares2);
  return denominator === 0 ? 0 : numerator / denominator;
};

export const detectAnomalies = (
  data: DataPoint[],
  options: {
    method?: 'zscore' | 'iqr' | 'isolation';
    threshold?: number;
    windowSize?: number;
  } = {}
): Array<{ index: number; value: number; severity: 'low' | 'medium' | 'high' }> => {
  const { method = 'zscore', threshold = 2, windowSize = 20 } = options;
  const anomalies: Array<{ index: number; value: number; severity: 'low' | 'medium' | 'high' }> =
    [];

  if (data.length < 3) return anomalies;

  switch (method) {
    case 'zscore': {
      const values = data.map((p) => p.value);
      const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
      const stdDev = calculateStandardDeviation(values);

      if (stdDev === 0) break;

      data.forEach((point, index) => {
        const zScore = Math.abs((point.value - mean) / stdDev);

        if (zScore > threshold) {
          let severity: 'low' | 'medium' | 'high' = 'low';
          if (zScore > threshold * 2) severity = 'high';
          else if (zScore > threshold * 1.5) severity = 'medium';

          anomalies.push({ index, value: point.value, severity });
        }
      });
      break;
    }

    case 'iqr': {
      const values = data.map((p) => p.value);
      const q1 = calculatePercentile(values, 25);
      const q3 = calculatePercentile(values, 75);
      const iqr = q3 - q1;
      const lowerBound = q1 - 1.5 * iqr;
      const upperBound = q3 + 1.5 * iqr;

      data.forEach((point, index) => {
        if (point.value < lowerBound || point.value > upperBound) {
          const distance = Math.min(
            Math.abs(point.value - lowerBound),
            Math.abs(point.value - upperBound)
          );

          let severity: 'low' | 'medium' | 'high' = 'low';
          if (distance > iqr * 2) severity = 'high';
          else if (distance > iqr) severity = 'medium';

          anomalies.push({ index, value: point.value, severity });
        }
      });
      break;
    }

    case 'isolation': {
      // Simple isolation forest approximation using moving windows
      for (let i = windowSize; i < data.length; i++) {
        const window = data.slice(i - windowSize, i);
        const windowValues = window.map((p) => p.value);
        const currentValue = data[i].value;

        const mean = windowValues.reduce((sum, val) => sum + val, 0) / windowValues.length;
        const stdDev = calculateStandardDeviation(windowValues);

        if (stdDev > 0) {
          const isolationScore = Math.abs((currentValue - mean) / stdDev);

          if (isolationScore > threshold) {
            let severity: 'low' | 'medium' | 'high' = 'low';
            if (isolationScore > threshold * 2) severity = 'high';
            else if (isolationScore > threshold * 1.5) severity = 'medium';

            anomalies.push({ index: i, value: currentValue, severity });
          }
        }
      }
      break;
    }
  }

  return anomalies;
};

export const predictNextValues = (
  data: DataPoint[],
  periods: number,
  method: 'linear' | 'exponential' | 'seasonal' = 'linear'
): DataPoint[] => {
  if (data.length < 2) return [];

  const predictions: DataPoint[] = [];
  const values = data.map((p) => p.value);
  const timestamps = data.map((p) => p.timestamp.getTime());

  switch (method) {
    case 'linear': {
      // Simple linear regression
      const n = data.length;
      const sumX = timestamps.reduce((sum, t) => sum + t, 0);
      const sumY = values.reduce((sum, v) => sum + v, 0);
      const sumXY = timestamps.reduce((sum, t, i) => sum + t * values[i], 0);
      const sumXX = timestamps.reduce((sum, t) => sum + t * t, 0);

      const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
      const intercept = (sumY - slope * sumX) / n;

      const lastTimestamp = timestamps[timestamps.length - 1];
      const interval =
        timestamps.length > 1 ? lastTimestamp - timestamps[timestamps.length - 2] : 60000; // Default 1 minute

      for (let i = 1; i <= periods; i++) {
        const nextTimestamp = lastTimestamp + interval * i;
        const predictedValue = slope * nextTimestamp + intercept;

        predictions.push({
          timestamp: new Date(nextTimestamp),
          value: predictedValue,
          metadata: { isPrediction: true, method: 'linear' },
        });
      }
      break;
    }

    case 'exponential': {
      // Simple exponential smoothing
      const alpha = 0.3; // Smoothing factor
      let forecast = values[values.length - 1];

      const lastTimestamp = timestamps[timestamps.length - 1];
      const interval =
        timestamps.length > 1 ? lastTimestamp - timestamps[timestamps.length - 2] : 60000;

      for (let i = 1; i <= periods; i++) {
        const nextTimestamp = lastTimestamp + interval * i;

        predictions.push({
          timestamp: new Date(nextTimestamp),
          value: forecast,
          metadata: { isPrediction: true, method: 'exponential' },
        });

        // Update forecast for next iteration (simple decay)
        forecast = forecast * 0.95;
      }
      break;
    }

    case 'seasonal': {
      // Simple seasonal pattern detection (weekly pattern)
      const seasonLength = 7; // Assume weekly seasonality
      const recentValues = values.slice(-seasonLength);

      const lastTimestamp = timestamps[timestamps.length - 1];
      const interval =
        timestamps.length > 1 ? lastTimestamp - timestamps[timestamps.length - 2] : 60000;

      for (let i = 1; i <= periods; i++) {
        const nextTimestamp = lastTimestamp + interval * i;
        const seasonIndex = (i - 1) % seasonLength;
        const seasonalValue = recentValues[seasonIndex] || values[values.length - 1];

        predictions.push({
          timestamp: new Date(nextTimestamp),
          value: seasonalValue,
          metadata: { isPrediction: true, method: 'seasonal' },
        });
      }
      break;
    }
  }

  return predictions;
};

export const calculateYearOverYearGrowth = (
  currentPeriodData: DataPoint[],
  previousPeriodData: DataPoint[]
): number => {
  const currentSum = currentPeriodData.reduce((sum, point) => sum + point.value, 0);
  const previousSum = previousPeriodData.reduce((sum, point) => sum + point.value, 0);

  return calculateGrowthRate(currentSum, previousSum);
};
