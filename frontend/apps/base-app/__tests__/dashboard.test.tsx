import { render, screen } from '@testing-library/react';
import DashboardPage from '../app/dashboard/page';
import * as httpClient from '@dotmac/http-client';
import * as authModule from '@dotmac/auth';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

const mockQueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

function Wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={mockQueryClient}>{children}</QueryClientProvider>;
}

jest.mock('@dotmac/http-client', () => ({
  ...jest.requireActual('@dotmac/http-client'),
  useApiQuery: jest.fn(),
}));

jest.mock('@dotmac/auth', () => ({
  ...jest.requireActual('@dotmac/auth'),
  useAuth: jest.fn(),
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.spyOn(authModule, 'useAuth').mockReturnValue({
      isAuthenticated: true,
      user: { profile: { name: 'Alice' } },
      logout: jest.fn(),
    } as any);
  });

  it('renders metric cards and events from API data', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: {
        metricCards: [
          { id: 'uptime', label: 'Uptime', value: '99.9%', trend: 'stable' },
        ],
        recentEvents: [
          {
            id: 'evt-1',
            timestamp: '2024-01-31T12:00:00Z',
            event: 'Health probe',
            actor: 'Gateway',
            status: 'healthy',
          },
        ],
      },
      isLoading: false,
      error: null,
    }) as any;

    render(
      <Wrapper>
        <DashboardPage />
      </Wrapper>,
    );

    expect(screen.getByText(/Uptime/)).toBeInTheDocument();
    expect(screen.getByText('99.9%')).toBeInTheDocument();
    expect(screen.getByText('Health probe')).toBeInTheDocument();
  });

  it('shows loading state for metrics', () => {
    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    }) as any;

    render(
      <Wrapper>
        <DashboardPage />
      </Wrapper>,
    );

    expect(screen.getByText('Loading metrics…')).toBeInTheDocument();
  });

  it('logs error when summary fetch fails', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    jest.spyOn(httpClient, 'useApiQuery').mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Gateway timeout'),
    }) as any;

    render(
      <Wrapper>
        <DashboardPage />
      </Wrapper>,
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to fetch platform summary',
      expect.any(Error),
    );

    consoleSpy.mockRestore();
  });
});
