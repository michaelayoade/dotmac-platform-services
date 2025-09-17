import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HomePage from '../app/page';
import * as httpClient from '@dotmac/http-client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useRouter } from 'next/navigation';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

const mockQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

// Mock console.error to avoid noise in tests
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

function Wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={mockQueryClient}>{children}</QueryClientProvider>;
}

jest.mock('@dotmac/http-client', () => ({
  ...jest.requireActual('@dotmac/http-client'),
  useApiQuery: jest.fn(),
}));

describe('HomePage', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      refresh: jest.fn(),
    });
    mockPush.mockClear();
  });

  it('renders health cards when data is loaded', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: {
        data: {
          status: 'healthy',
          service: 'api-gateway',
          checks: {
            cache: 'healthy',
            auth: 'healthy',
          },
        },
      },
      isLoading: false,
      error: null,
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    expect(screen.getByText('API health')).toBeInTheDocument();
    expect(screen.getByText(/api-gateway/)).toBeInTheDocument();
    expect(screen.getByText('cache')).toBeInTheDocument();
    expect(screen.getByText('auth')).toBeInTheDocument();
  });

  it('displays loading state when health is fetching', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    expect(screen.getByText('Checking platform status…')).toBeInTheDocument();
  });

  it('displays error state when health check fails', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: false,
      error: { message: 'Connection timeout' },
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
  });

  it('displays fallback error message when error has no message', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: false,
      error: {},
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    expect(screen.getByText('Service unavailable')).toBeInTheDocument();
  });

  it('renders main navigation elements', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    expect(screen.getByText('DotMac Platform Starter')).toBeInTheDocument();
    expect(screen.getByText('Kick-start your next product with production-ready platform services')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Explore dashboard' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign in' })).toBeInTheDocument();
  });

  it('renders feature cards', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    expect(screen.getByText('Pre-integrated services')).toBeInTheDocument();
    expect(screen.getByText('Next steps')).toBeInTheDocument();
    expect(screen.getByText('Universal auth provider with session hydration')).toBeInTheDocument();
    expect(screen.getByText('Set environment variables in')).toBeInTheDocument();
  });

  it('logs errors to console when health check fails', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const mockError = new Error('Network failure');

    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: false,
      error: mockError,
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    expect(consoleSpy).toHaveBeenCalledWith('Health check failed', mockError);
    consoleSpy.mockRestore();
  });

  it('handles navigation interactions', async () => {
    const user = userEvent.setup();
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    const dashboardLink = screen.getByRole('link', { name: 'Explore dashboard' });
    const signInLink = screen.getByRole('link', { name: 'Sign in' });

    expect(dashboardLink).toHaveAttribute('href', '/dashboard');
    expect(signInLink).toHaveAttribute('href', '/auth/login');
  });

  it('renders health check details correctly', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: {
        data: {
          status: 'healthy',
          service: 'api-gateway',
          checks: {
            database: 'healthy',
            cache: 'degraded',
            auth: 'healthy',
          },
        },
      },
      isLoading: false,
      error: null,
    }) as any;

    render(
      <Wrapper>
        <HomePage />
      </Wrapper>,
    );

    expect(screen.getByText('healthy – api-gateway')).toBeInTheDocument();
    expect(screen.getByText('DATABASE')).toBeInTheDocument();
    expect(screen.getByText('CACHE')).toBeInTheDocument();
    expect(screen.getByText('AUTH')).toBeInTheDocument();

    // Check status indicators
    const healthyStatuses = screen.getAllByText('healthy');
    expect(healthyStatuses.length).toBeGreaterThan(1);
    expect(screen.getByText('degraded')).toBeInTheDocument();
  });
});
