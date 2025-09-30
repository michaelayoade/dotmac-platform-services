'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { register as registerUser } from '@/lib/auth';
import { registerSchema, type RegisterFormData } from '@/lib/validations/auth';

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    setError('');
    setLoading(true);

    try {
      // Register the user; backend issues HttpOnly auth cookies
      await registerUser({
        email: data.email,
        password: data.password,
        name: data.full_name,
      });

      // Server sets HttpOnly cookies; navigate once ready
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-12 bg-slate-950">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-50 mb-2">Create an account</h1>
          <p className="text-slate-400">Join the DotMac Platform</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-lg p-8 space-y-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-slate-300 mb-2">
              Full Name (optional)
            </label>
            <input
              id="full_name"
              type="text"
              {...register('full_name')}
              className={`w-full px-3 py-2 bg-slate-800 border ${
                errors.full_name ? 'border-red-500' : 'border-slate-700'
              } rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent`}
              placeholder="John Doe"
            />
            {errors.full_name && (
              <p className="mt-1 text-sm text-red-400">{errors.full_name.message}</p>
            )}
          </div>

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
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
            )}
            <p className="text-xs text-slate-500 mt-1">
              Must contain uppercase, lowercase, and number
            </p>
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300 mb-2">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              {...register('confirmPassword')}
              className={`w-full px-3 py-2 bg-slate-800 border ${
                errors.confirmPassword ? 'border-red-500' : 'border-slate-700'
              } rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent`}
              placeholder="••••••••"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-400">{errors.confirmPassword.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
          >
            {loading ? 'Creating account...' : 'Sign up'}
          </button>

          <p className="text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link href="/login" className="text-sky-400 hover:text-sky-300">
              Sign in
            </Link>
          </p>
        </form>

        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-slate-400 hover:text-slate-300">
            ← Back to home
          </Link>
        </div>
      </div>
    </main>
  );
}