import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

type HealthResponse = {
  status: string;
  service: string;
  checks: Record<string, string>;
};

type MetricsResponse = {
  counters?: Record<string, number>;
  histograms?: Record<string, unknown>;
};

type MetricCard = {
  id: string;
  label: string;
  value: string;
  trend?: string;
};

type RecentEvent = {
  id: string;
  timestamp: string;
  event: string;
  actor: string;
  status: string;
};

export async function GET(request: NextRequest) {
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };

  const cookie = request.headers.get('cookie');
  if (cookie) {
    headers.cookie = cookie;
  }

  try {
    const [healthRes, metricsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/health`, { headers }),
      fetch(`${API_BASE_URL}/metrics`, { headers }),
    ]);

    if (!healthRes.ok) {
      throw new Error(`Health check failed: ${healthRes.status}`);
    }
    if (!metricsRes.ok) {
      throw new Error(`Metrics retrieval failed: ${metricsRes.status}`);
    }

    const health: HealthResponse = await healthRes.json();
    const metrics: MetricsResponse = await metricsRes.json();

    const totalChecks = Object.keys(health.checks ?? {}).length;
    const healthyChecks = Object.values(health.checks ?? {}).filter(
      (status) => status === 'healthy',
    ).length;

    const metricCards: MetricCard[] = [
      {
        id: 'health-checks',
        label: 'Health checks',
        value: totalChecks > 0 ? `${healthyChecks}/${totalChecks}` : 'N/A',
        trend: healthyChecks === totalChecks ? 'All systems passing' : 'Attention required',
      },
      {
        id: 'counters',
        label: 'Counters tracked',
        value: String(Object.keys(metrics.counters ?? {}).length),
        trend: 'Recorded by observability pipeline',
      },
      {
        id: 'histograms',
        label: 'Latency histograms',
        value: String(Object.keys(metrics.histograms ?? {}).length),
        trend: 'Distribution metrics available',
      },
    ];

    const recentEvents: RecentEvent[] = Object.entries(health.checks ?? {}).map(
      ([check, status], index) => ({
        id: `${check}-${index}`,
        timestamp: new Date().toISOString(),
        event: `${check} probe`,
        actor: 'Gateway',
        status,
      }),
    );

    return NextResponse.json({
      health,
      metrics,
      metricCards,
      recentEvents,
    });
  } catch (error) {
    console.error('Failed to load platform summary', error);
    return NextResponse.json({ error: 'Failed to load platform summary' }, { status: 502 });
  }
}
