'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import * as z from 'zod';
import { useAuth } from '@dotmac/auth';
import { Button, Card, Input } from '@dotmac/ui';
import { toast } from '@dotmac/notifications';

const loginSchema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: 'builder@dotmac.dev',
      password: 'password',
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = form;

  const onSubmit = async (values: LoginFormValues) => {
    try {
      await login({ username: values.email, password: values.password });
      toast.success('Welcome back!');
      router.push('/dashboard');
    } catch (error: any) {
      toast.error(error?.message ?? 'Unable to sign in');
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-16">
      <Card className="w-full max-w-md bg-slate-900/70 border-slate-700/40">
        <Card.Header className="space-y-2 text-center">
          <Card.Title>Sign in to DotMac</Card.Title>
          <Card.Description>Use the shared auth provider preconfigured for the platform.</Card.Description>
        </Card.Header>
        <Card.Content>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300" htmlFor="email">
                Email
              </label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                {...register('email')}
                placeholder="you@example.com"
                required
              />
              {errors.email && (
                <p className="text-xs text-rose-400">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300" htmlFor="password">
                Password
              </label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register('password')}
                required
              />
              {errors.password && (
                <p className="text-xs text-rose-400">{errors.password.message}</p>
              )}
            </div>

            <Button className="w-full" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </Card.Content>
        <Card.Footer>
          <p className="text-center text-sm text-slate-400">
            Need an account? <Link href="#" className="text-sky-400">Contact DotMac support.</Link>
          </p>
        </Card.Footer>
      </Card>
    </main>
  );
}
