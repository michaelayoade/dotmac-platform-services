/**
 * Integration tests for /api/platform/summary route
 */

import { NextRequest } from 'next/server';
import { GET } from '../../app/api/platform/summary/route';

// Mock fetch globally
global.fetch = jest.fn();

const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

describe('/api/platform/summary', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Reset environment variable
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000/api';
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  const createMockRequest = (headers: Record<string, string> = {}) => {
    const url = 'http://localhost:3000/api/platform/summary';
    const request = new NextRequest(url, {
      method: 'GET',
      headers,
    });
    return request;
  };

  const createMockResponse = (data: any, ok = true, status = 200) => ({
    ok,
    status,
    json: jest.fn().mockResolvedValue(data),
  });

  it('successfully proxies health and metrics data', async () => {
    const mockHealthData = {
      status: 'healthy',
      service: 'api-gateway',
      checks: {
        database: 'healthy',
        cache: 'healthy',
        auth: 'healthy',
      },
    };

    const mockMetricsData = {
      counters: {
        'requests.total': 1234,
        'errors.total': 5,
      },
      histograms: {
        'request.duration': { p50: 100, p95: 250, p99: 500 },
      },
    };

    mockFetch
      .mockResolvedValueOnce(createMockResponse(mockHealthData) as any)
      .mockResolvedValueOnce(createMockResponse(mockMetricsData) as any);

    const request = createMockRequest();
    const response = await GET(request);

    expect(response.status).toBe(200);

    const responseData = await response.json();

    expect(responseData).toMatchObject({
      health: mockHealthData,
      metrics: mockMetricsData,
      metricCards: expect.arrayContaining([
        expect.objectContaining({
          id: 'health-checks',
          label: 'Health checks',
          value: '3/3',
          trend: 'All systems passing',
        }),
        expect.objectContaining({
          id: 'counters',
          label: 'Counters tracked',
          value: '2',
        }),
        expect.objectContaining({
          id: 'histograms',
          label: 'Latency histograms',
          value: '1',
        }),
      ]),
      recentEvents: expect.arrayContaining([
        expect.objectContaining({
          event: 'database probe',
          actor: 'Gateway',
          status: 'healthy',
        }),
        expect.objectContaining({
          event: 'cache probe',
          actor: 'Gateway',
          status: 'healthy',
        }),
        expect.objectContaining({
          event: 'auth probe',
          actor: 'Gateway',
          status: 'healthy',
        }),
      ]),
    });

    // Verify correct API calls were made
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/health',
      expect.objectContaining({
        headers: expect.objectContaining({
          Accept: 'application/json',
        }),
      })
    );
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/metrics',
      expect.objectContaining({
        headers: expect.objectContaining({
          Accept: 'application/json',
        }),
      })
    );
  });

  it('forwards authentication cookies to backend', async () => {
    const mockHealthData = { status: 'healthy', service: 'test', checks: {} };
    const mockMetricsData = { counters: {}, histograms: {} };

    mockFetch
      .mockResolvedValueOnce(createMockResponse(mockHealthData) as any)
      .mockResolvedValueOnce(createMockResponse(mockMetricsData) as any);

    const request = createMockRequest({
      cookie: 'session=abc123; token=xyz789',
    });

    await GET(request);

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/health',
      expect.objectContaining({
        headers: expect.objectContaining({
          Accept: 'application/json',
          cookie: 'session=abc123; token=xyz789',
        }),
      })
    );

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/metrics',
      expect.objectContaining({
        headers: expect.objectContaining({
          Accept: 'application/json',
          cookie: 'session=abc123; token=xyz789',
        }),
      })
    );
  });

  it('handles health check failure gracefully', async () => {
    mockFetch
      .mockResolvedValueOnce(createMockResponse({}, false, 503) as any)
      .mockResolvedValueOnce(createMockResponse({}) as any);

    const request = createMockRequest();
    const response = await GET(request);

    expect(response.status).toBe(502);

    const responseData = await response.json();
    expect(responseData).toEqual({
      error: 'Failed to load platform summary',
    });
  });

  it('handles metrics failure gracefully', async () => {
    const mockHealthData = { status: 'healthy', service: 'test', checks: {} };

    mockFetch
      .mockResolvedValueOnce(createMockResponse(mockHealthData) as any)
      .mockResolvedValueOnce(createMockResponse({}, false, 500) as any);

    const request = createMockRequest();
    const response = await GET(request);

    expect(response.status).toBe(502);

    const responseData = await response.json();
    expect(responseData).toEqual({
      error: 'Failed to load platform summary',
    });
  });

  it('handles network errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const request = createMockRequest();
    const response = await GET(request);

    expect(response.status).toBe(502);

    const responseData = await response.json();
    expect(responseData).toEqual({
      error: 'Failed to load platform summary',
    });
  });

  it('calculates metric cards correctly with mixed health status', async () => {
    const mockHealthData = {
      status: 'degraded',
      service: 'api-gateway',
      checks: {
        database: 'healthy',
        cache: 'degraded',
        auth: 'healthy',
      },
    };

    const mockMetricsData = {
      counters: {
        'requests.total': 1000,
        'errors.total': 10,
        'cache.hits': 800,
      },
      histograms: {},
    };

    mockFetch
      .mockResolvedValueOnce(createMockResponse(mockHealthData) as any)
      .mockResolvedValueOnce(createMockResponse(mockMetricsData) as any);

    const request = createMockRequest();
    const response = await GET(request);

    expect(response.status).toBe(200);

    const responseData = await response.json();

    // Check health checks metric card
    const healthChecksCard = responseData.metricCards.find(
      (card: any) => card.id === 'health-checks'
    );
    expect(healthChecksCard).toMatchObject({
      id: 'health-checks',
      label: 'Health checks',
      value: '2/3', // 2 healthy out of 3 total
      trend: 'Attention required', // Not all systems passing
    });

    // Check counters metric card
    const countersCard = responseData.metricCards.find(
      (card: any) => card.id === 'counters'
    );
    expect(countersCard).toMatchObject({
      id: 'counters',
      label: 'Counters tracked',
      value: '3', // 3 counters
    });

    // Check recent events include degraded status
    const degradedEvent = responseData.recentEvents.find(
      (event: any) => event.event === 'cache probe'
    );
    expect(degradedEvent).toMatchObject({
      status: 'degraded',
    });
  });

  it('handles empty health checks', async () => {
    const mockHealthData = {
      status: 'unknown',
      service: 'api-gateway',
      checks: {}, // No checks available
    };

    const mockMetricsData = {
      counters: {},
      histograms: {},
    };

    mockFetch
      .mockResolvedValueOnce(createMockResponse(mockHealthData) as any)
      .mockResolvedValueOnce(createMockResponse(mockMetricsData) as any);

    const request = createMockRequest();
    const response = await GET(request);

    expect(response.status).toBe(200);

    const responseData = await response.json();

    const healthChecksCard = responseData.metricCards.find(
      (card: any) => card.id === 'health-checks'
    );
    expect(healthChecksCard.value).toBe('N/A');

    expect(responseData.recentEvents).toHaveLength(0);
  });

  it('uses custom API base URL from environment', async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'https://custom-api.example.com/v1';

    const mockHealthData = { status: 'healthy', service: 'test', checks: {} };
    const mockMetricsData = { counters: {}, histograms: {} };

    mockFetch
      .mockResolvedValueOnce(createMockResponse(mockHealthData) as any)
      .mockResolvedValueOnce(createMockResponse(mockMetricsData) as any);

    const request = createMockRequest();
    await GET(request);

    expect(mockFetch).toHaveBeenCalledWith(
      'https://custom-api.example.com/v1/health',
      expect.any(Object)
    );
    expect(mockFetch).toHaveBeenCalledWith(
      'https://custom-api.example.com/v1/metrics',
      expect.any(Object)
    );
  });

  it('logs errors appropriately', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const networkError = new Error('Connection refused');

    mockFetch.mockRejectedValueOnce(networkError);

    const request = createMockRequest();
    await GET(request);

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to load platform summary',
      networkError
    );

    consoleSpy.mockRestore();
  });
});