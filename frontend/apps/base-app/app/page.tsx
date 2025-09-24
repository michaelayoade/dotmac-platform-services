'use client';

import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-16 gap-10">
      <div className="text-center space-y-4 max-w-2xl">
        <span className="inline-flex items-center rounded-full bg-sky-500/10 px-3 py-1 text-sm font-medium text-sky-400 ring-1 ring-inset ring-sky-500/20">
          DotMac Platform Starter
        </span>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl text-slate-50">
          Production-Ready Platform Services
        </h1>
        <p className="text-slate-300 text-lg">
          A complete boilerplate with authentication, API gateway, file storage, and more.
          Built with FastAPI backend and Next.js frontend.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
          <Link href="/login">
            <button className="px-6 py-3 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors">
              Sign In
            </button>
          </Link>
          <Link href="/dashboard">
            <button className="px-6 py-3 border border-slate-600 text-slate-300 rounded-lg hover:bg-slate-800 transition-colors">
              Go to Dashboard
            </button>
          </Link>
        </div>
      </div>

      <section className="grid w-full max-w-5xl gap-4 md:grid-cols-3">
        <div className="bg-slate-900/40 backdrop-blur border border-slate-700/40 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-2">Backend Services</h3>
          <p className="text-sm text-slate-400 mb-4">FastAPI with modular architecture</p>
          <ul className="space-y-1 text-sm text-slate-300 list-disc list-inside">
            <li>JWT Authentication</li>
            <li>Vault Secrets Management</li>
            <li>File Storage (S3/Local)</li>
            <li>OpenTelemetry Observability</li>
          </ul>
        </div>

        <div className="bg-slate-900/40 backdrop-blur border border-slate-700/40 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-2">Frontend Stack</h3>
          <p className="text-sm text-slate-400 mb-4">Next.js 14 with TypeScript</p>
          <ul className="space-y-1 text-sm text-slate-300 list-disc list-inside">
            <li>App Router Architecture</li>
            <li>Tailwind CSS Styling</li>
            <li>React Query Integration</li>
            <li>Dark Mode Support</li>
          </ul>
        </div>

        <div className="bg-slate-900/40 backdrop-blur border border-slate-700/40 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-100 mb-2">Production Ready</h3>
          <p className="text-sm text-slate-400 mb-4">Deploy anywhere</p>
          <ul className="space-y-1 text-sm text-slate-300 list-disc list-inside">
            <li>Docker Compose Setup</li>
            <li>Environment Configuration</li>
            <li>Health Check Endpoints</li>
            <li>CI/CD Ready</li>
          </ul>
        </div>
      </section>

      <div className="text-center text-sm text-slate-400 mt-8">
        API Status: <span className="text-emerald-400">Ready at localhost:8000</span>
      </div>
    </main>
  );
}