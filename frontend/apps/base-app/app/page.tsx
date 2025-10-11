'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';

export default function HomePage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated via API call (HttpOnly cookies can't be read by JS)
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/v1/auth/me', {
          credentials: 'include',
        });
        setIsLoggedIn(response.ok);
      } catch (error) {
        setIsLoggedIn(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-16 gap-12">
      <div className="text-center space-y-6 max-w-3xl">
        <div className="flex items-center justify-center mb-6">
          <span className="inline-flex items-center rounded-full bg-sky-500/10 px-4 py-2 text-sm font-medium text-sky-400 ring-1 ring-inset ring-sky-500/20">
            🚀 DotMac Platform Services
          </span>
        </div>

        <h1 className="text-5xl font-bold tracking-tight text-foreground mb-4">
          Enterprise Platform
          <span className="text-sky-400 block">Ready to Deploy</span>
        </h1>

        <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Complete business platform with authentication, customer management, billing,
          analytics, and more. Built for scale with FastAPI and React.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 mt-8">
          {isLoggedIn ? (
            <Link href="/dashboard">
              <button className="px-8 py-4 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors text-lg font-medium">
                Go to Dashboard
              </button>
            </Link>
          ) : (
            <>
              <Link href="/login">
                <button className="px-8 py-4 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors text-lg font-medium">
                  Sign In
                </button>
              </Link>
              <Link href="/register">
                <button className="px-8 py-4 border border-border text-muted-foreground rounded-lg hover:bg-accent transition-colors text-lg font-medium">
                  Create Account
                </button>
              </Link>
            </>
          )}
        </div>

        <div className="bg-card/30 backdrop-blur border border-border/50 rounded-lg p-4 mt-8">
          <p className="text-sm text-muted-foreground mb-2">Quick Start - Test Credentials:</p>
          <p className="text-sky-400 font-mono text-sm">admin / admin123</p>
        </div>
      </div>

      <section className="grid w-full max-w-6xl gap-6 md:grid-cols-3">
        <div className="bg-card/40 backdrop-blur border border-border/40 rounded-xl p-8 hover:bg-card/60 transition-all">
          <div className="text-sky-400 mb-4 text-2xl">🔐</div>
          <h3 className="text-xl font-semibold text-foreground mb-3">Authentication & Security</h3>
          <ul className="space-y-2 text-muted-foreground text-sm">
            <li>• JWT-based authentication</li>
            <li>• Role-based access control</li>
            <li>• Secure secrets management</li>
            <li>• API key management</li>
          </ul>
        </div>

        <div className="bg-card/40 backdrop-blur border border-border/40 rounded-xl p-8 hover:bg-card/60 transition-all">
          <div className="text-green-400 mb-4 text-2xl">📊</div>
          <h3 className="text-xl font-semibold text-foreground mb-3">Business Operations</h3>
          <ul className="space-y-2 text-muted-foreground text-sm">
            <li>• Customer relationship management</li>
            <li>• Billing & payment processing</li>
            <li>• Analytics & reporting</li>
            <li>• Communication tools</li>
          </ul>
        </div>

        <div className="bg-card/40 backdrop-blur border border-border/40 rounded-xl p-8 hover:bg-card/60 transition-all">
          <div className="text-purple-400 mb-4 text-2xl">🚀</div>
          <h3 className="text-xl font-semibold text-foreground mb-3">Developer Experience</h3>
          <ul className="space-y-2 text-muted-foreground text-sm">
            <li>• Modern React/Next.js frontend</li>
            <li>• FastAPI backend with OpenAPI</li>
            <li>• Docker containerization</li>
            <li>• Production-ready monitoring</li>
          </ul>
        </div>
      </section>

      <div className="flex items-center gap-4 text-sm text-muted-foreground mt-8">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
          <span>API: <span className="text-emerald-400">localhost:8000</span></span>
        </div>
        <div className="w-px h-4 bg-muted"></div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
          <span>Frontend: <span className="text-blue-400">localhost:3001</span></span>
        </div>
      </div>
    </main>
  );
}
