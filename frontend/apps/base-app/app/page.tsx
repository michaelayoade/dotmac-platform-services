'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { useApiQuery } from '@dotmac/http-client';
import { apiClient } from '@/lib/http-client';
import { Button, Card } from '@dotmac/ui';

interface HealthCheckResponse {
  status: string;
  service: string;
  checks: Record<string, string>;
}

const healthQuery = () => apiClient.get<HealthCheckResponse>('/health');

export default function HomePage() {
  const {
    data: healthResponse,
    isLoading,
    error,
  } = useApiQuery(['health'], { execute: healthQuery });
  const health = healthResponse?.data;
  const errorMessage = (error as any)?.message ?? (error as any)?.error?.message ?? null;

  useEffect(() => {
    if (error) {
      console.error('Health check failed', error);
    }
  }, [error]);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-16 gap-10">
      <div className="text-center space-y-4 max-w-2xl">
        <span className="inline-flex items-center rounded-full bg-sky-500/10 px-3 py-1 text-sm font-medium text-sky-400 ring-1 ring-inset ring-sky-500/20">
          DotMac Platform Starter
        </span>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl text-slate-50">
          Kick-start your next product with production-ready platform services
        </h1>
        <p className="text-slate-300 text-lg">
          This base application ships with authentication, API clients, real-time hooks and UI primitives already wired up. Update the theme, connect your endpoints, and build from day one.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
          <Button asChild variant="primary">
            <Link href="/dashboard">Explore dashboard</Link>
          </Button>
          <Button asChild variant="ghost">
            <Link href="/auth/login">Sign in</Link>
          </Button>
        </div>
      </div>

      <section className="grid w-full max-w-5xl gap-4 md:grid-cols-3">
        <Card className="bg-slate-900/40 backdrop-blur border-slate-700/40">
          <Card.Header>
            <Card.Title>API health</Card.Title>
            <Card.Description>Gateway connectivity check</Card.Description>
          </Card.Header>
          <Card.Content>
            {isLoading ? (
              <p className="text-slate-400">Checking platform status…</p>
            ) : error ? (
              <p className="text-rose-400">{errorMessage ?? 'Service unavailable'}</p>
            ) : health ? (
              <div className="space-y-2">
                <p className="text-emerald-400 text-sm flex items-center gap-2">
                  <span className="inline-block h-2 w-2 rounded-full bg-emerald-400" />
                  {health.status} – {health.service}
                </p>
                <ul className="text-xs text-slate-200 space-y-1">
                  {Object.entries(health.checks ?? {}).map(([name, status]) => (
                    <li key={name} className="flex items-center justify-between bg-slate-900/40 rounded px-3 py-2">
                      <span className="uppercase tracking-wide text-slate-400">{name}</span>
                      <span className={status === 'healthy' ? 'text-emerald-400' : 'text-amber-400'}>{status}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </Card.Content>
        </Card>

        <Card className="bg-slate-900/40 backdrop-blur border-slate-700/40">
          <Card.Header>
            <Card.Title>Pre-integrated services</Card.Title>
            <Card.Description>React hooks & providers</Card.Description>
          </Card.Header>
          <Card.Content className="space-y-2 text-slate-300 text-sm">
            <ul className="space-y-1 list-disc list-inside">
              <li>Universal auth provider with session hydration</li>
              <li>React Query configured for platform APIs</li>
              <li>Notification center & toast pipeline</li>
            </ul>
          </Card.Content>
        </Card>

        <Card className="bg-slate-900/40 backdrop-blur border-slate-700/40">
          <Card.Header>
            <Card.Title>Next steps</Card.Title>
            <Card.Description>Customize for your product</Card.Description>
          </Card.Header>
          <Card.Content className="space-y-2 text-slate-300 text-sm">
            <ol className="space-y-1 list-decimal list-inside">
              <li>Set environment variables in <code>.env</code></li>
              <li>Adjust the brand theme tokens</li>
              <li>Extend the dashboard with real data</li>
            </ol>
          </Card.Content>
        </Card>
      </section>
    </main>
  );
}
