'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { apiClient } from '@/lib/api/client';
import { logger } from '@/lib/utils/logger';
import { loginSchema, type LoginFormData } from '@/lib/validations/auth';

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setError('');
    setLoading(true);

    try {
      logger.info('Starting login process', { email: data.email });

      const response = await apiClient.login(data.email, data.password);
      logger.debug('Login response received', { success: response.success });

      if (response.success) {
        logger.info('Login successful, cookies should be set by server');
        await new Promise(resolve => setTimeout(resolve, 500));
        logger.info('Redirecting to dashboard');
        router.push('/dashboard');
      } else {
        logger.error('Login failed', new Error(response.error?.message || 'Login failed'), { response: response.error });
        setError(response.error?.message || 'Login failed');
      }
    } catch (err) {
      logger.error('Login error', err instanceof Error ? err : new Error(String(err)));
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-12 bg-slate-950">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-50 mb-2">Welcome back</h1>
          <p className="text-slate-400">Sign in to your DotMac Platform account</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-lg p-8 space-y-6" data-testid="login-form">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-sm" data-testid="error-message">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
              Email address
            </label>
            <input
              id="email"
              type="email"
              {...register('email')}
              className={`w-full px-3 py-2 bg-slate-800 border ${
                errors.email ? 'border-red-500' : 'border-slate-700'
              } rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent`}
              placeholder="you@example.com"
              data-testid="email-input"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              {...register('password')}
              className={`w-full px-3 py-2 bg-slate-800 border ${
                errors.password ? 'border-red-500' : 'border-slate-700'
              } rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent`}
              placeholder="••••••••"
              data-testid="password-input"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-sky-500 focus:ring-sky-500 focus:ring-offset-slate-900"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-slate-300">
                Remember me
              </label>
            </div>

            <Link href="/forgot-password" className="text-sm text-sky-400 hover:text-sky-300">
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-sky-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-sky-600 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="submit-button"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-400">
          Don't have an account?{' '}
          <Link href="/register" className="text-sky-400 hover:text-sky-300 font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </main>
  );
}