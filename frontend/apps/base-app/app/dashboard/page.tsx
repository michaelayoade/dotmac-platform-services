'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@dotmac/auth';
import { Card, Button, Table } from '@dotmac/ui';
import { useApiQuery } from '@dotmac/http-client';

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

type PlatformSummary = {
  health: {
    status: string;
    service: string;
    checks: Record<string, string>;
  };
  metrics: {
    counters?: Record<string, number>;
    histograms?: Record<string, unknown>;
  };
  metricCards: MetricCard[];
  recentEvents: RecentEvent[];
};

const fetchPlatformSummary = () =>
  fetch('/api/platform/summary', { cache: 'no-store' }).then((res) => {
    if (!res.ok) {
      throw new Error('Failed to load platform summary');
    }
    return res.json() as Promise<PlatformSummary>;
  });

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, user, logout } = useAuth();
  const {
    data,
    isLoading,
    error,
  } = useApiQuery(['platform-summary'], { execute: fetchPlatformSummary });

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/auth/login');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (error) {
      console.error('Failed to fetch platform summary', error);
    }
  }, [error]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-4 backdrop-blur">
        <div>
          <h1 className="text-2xl font-semibold">Welcome back, {user?.profile?.name ?? 'DotMac Builder'}</h1>
          <p className="text-sm text-slate-400">
            This workspace is wired to the shared analytics and notification systems out of the box.
          </p>
        </div>
        <Button variant="ghost" onClick={logout}>
          Sign out
        </Button>
      </header>

      <main className="px-6 py-10 space-y-8">
        <section className="grid gap-4 md:grid-cols-3">
          {(data?.metricCards ?? []).map((metric) => (
            <Card key={metric.id} className="bg-slate-900/60 border-slate-700/40">
              <Card.Header>
                <Card.Title>{metric.label}</Card.Title>
              </Card.Header>
              <Card.Content>
                <p className="text-3xl font-semibold">{metric.value}</p>
                {metric.trend ? (
                  <p className="text-sm text-emerald-400">{metric.trend}</p>
                ) : null}
              </Card.Content>
            </Card>
          ))}
          {!isLoading && !error && (data?.metricCards?.length ?? 0) === 0 && (
            <Card className="bg-slate-900/60 border-slate-700/40">
              <Card.Content>
                <p className="text-slate-400">No metrics available yet.</p>
              </Card.Content>
            </Card>
          )}
          {isLoading && (
            <Card className="bg-slate-900/60 border-slate-700/40">
              <Card.Content>
                <p className="text-slate-400">Loading metrics…</p>
              </Card.Content>
            </Card>
          )}
          {error && (
            <Card className="bg-slate-900/60 border-slate-700/40">
              <Card.Content>
                <p className="text-rose-400 text-sm">{error.message}</p>
              </Card.Content>
            </Card>
          )}
        </section>

        <section>
          <Card className="bg-slate-900/60 border-slate-700/40">
            <Card.Header>
              <Card.Title>Recent platform events</Card.Title>
              <Card.Description>Rendered via the shared data-table primitives.</Card.Description>
            </Card.Header>
            <Card.Content>
              {data?.recentEvents?.length ? (
                <Table>
                  <Table.Header>
                    <Table.Row>
                      <Table.Head>Time</Table.Head>
                      <Table.Head>Event</Table.Head>
                      <Table.Head>Actor</Table.Head>
                      <Table.Head>Status</Table.Head>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {data.recentEvents.map((event) => (
                      <Table.Row key={event.id}>
                        <Table.Cell>{new Date(event.timestamp).toLocaleString()}</Table.Cell>
                        <Table.Cell>{event.event}</Table.Cell>
                        <Table.Cell>{event.actor}</Table.Cell>
                        <Table.Cell>
                          <span
                            className={`rounded px-2 py-0.5 text-xs font-medium ${
                              event.status === 'healthy'
                                ? 'bg-emerald-500/10 text-emerald-400'
                                : 'bg-amber-500/10 text-amber-400'
                            }`}
                          >
                            {event.status}
                          </span>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table>
              ) : (
                <p className="text-slate-400 text-sm">No recent events available.</p>
              )}
            </Card.Content>
          </Card>
        </section>
      </main>
    </div>
  );
}
