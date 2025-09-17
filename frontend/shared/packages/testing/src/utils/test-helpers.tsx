import { render, screen, waitFor, act, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock NotificationProvider for testing
const MockNotificationProvider = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>;
};

// Enhanced render function with all providers
export const renderWithProviders = (
  ui: React.ReactElement,
  options: {
    queryClient?: QueryClient;
    initialNotifications?: any[];
    websocketUrl?: string;
    [key: string]: any;
  } = {}
): ReturnType<typeof render> & {
  user: ReturnType<typeof userEvent.setup>;
  queryClient: QueryClient;
} => {
  const {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false },
      },
    }),
    initialNotifications = [],
    websocketUrl = 'ws://localhost:8080',
    ...renderOptions
  } = options;

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MockNotificationProvider>{children}</MockNotificationProvider>
    </QueryClientProvider>
  );

  const result = render(ui, { wrapper: Wrapper, ...renderOptions });

  return {
    ...result,
    user: userEvent.setup(),
    queryClient,
  };
};

// Hook testing utilities
export const createHookWrapper = (providers: React.ComponentType<any>[] = []) => {
  return ({ children }: { children: React.ReactNode }) => {
    return providers.reduceRight(
      (acc, Provider) => <Provider>{acc}</Provider>,
      children
    ) as React.ReactElement;
  };
};

// Async testing helpers
export const waitForLoadingToFinish = async (timeout = 5000) => {
  await waitFor(
    () => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    },
    { timeout }
  );
};

export const waitForErrorToAppear = async (expectedError: string | RegExp, timeout = 3000) => {
  await waitFor(
    () => {
      expect(screen.getByText(expectedError)).toBeInTheDocument();
    },
    { timeout }
  );
};

// Form testing utilities
export const fillForm = async (formData: Record<string, string>) => {
  const user = userEvent.setup();

  for (const [fieldName, value] of Object.entries(formData)) {
    const field = screen.getByLabelText(new RegExp(fieldName, 'i'));
    await user.clear(field);
    await user.type(field, value);
  }
};

export const submitForm = async (submitButtonText = /submit|save|create/i) => {
  const user = userEvent.setup();
  const submitButton = screen.getByRole('button', { name: submitButtonText });
  await user.click(submitButton);
};

// Table testing utilities
export const getTableRows = (tableRole = 'table') => {
  const table = screen.getByRole(tableRole);
  return within(table).getAllByRole('row');
};

export const getTableCells = (row: HTMLElement) => {
  return within(row).getAllByRole('cell');
};

export const expectTableToHaveRows = (expectedRowCount: number, tableRole = 'table') => {
  const rows = getTableRows(tableRole);
  // Subtract 1 for header row
  expect(rows).toHaveLength(expectedRowCount + 1);
};

// Modal testing utilities
export const expectModalToBeOpen = (modalTitleText: string | RegExp) => {
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  expect(screen.getByText(modalTitleText)).toBeInTheDocument();
};

export const expectModalToBeClosed = () => {
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
};

export const closeModal = async () => {
  const user = userEvent.setup();
  const closeButton = screen.getByRole('button', { name: /close|cancel/i });
  await user.click(closeButton);
};

// Navigation testing utilities
export const expectCurrentPage = (expectedPath: string) => {
  expect(window.location.pathname).toBe(expectedPath);
};

export const navigateToPage = async (linkText: string | RegExp) => {
  const user = userEvent.setup();
  const link = screen.getByRole('link', { name: linkText });
  await user.click(link);
};

// WebSocket testing utilities
export const mockWebSocketMessage = (mockWS: any, message: any) => {
  act(() => {
    if (mockWS.onmessage) {
      mockWS.onmessage(
        new MessageEvent('message', {
          data: JSON.stringify(message),
        })
      );
    }
  });
};

export const mockWebSocketConnection = (mockWS: any) => {
  act(() => {
    mockWS.readyState = WebSocket.OPEN;
    if (mockWS.onopen) {
      mockWS.onopen(new Event('open'));
    }
  });
};

export const mockWebSocketDisconnection = (mockWS: any) => {
  act(() => {
    mockWS.readyState = WebSocket.CLOSED;
    if (mockWS.onclose) {
      mockWS.onclose(new CloseEvent('close'));
    }
  });
};

// Notification testing utilities
export const expectNotificationToShow = async (message: string | RegExp) => {
  await waitFor(() => {
    expect(screen.getByText(message)).toBeInTheDocument();
  });
};

export const expectSuccessNotification = async (message?: string | RegExp) => {
  const successIndicator = message
    ? screen.getByText(message)
    : screen.getByText(/success|completed|saved/i);

  await waitFor(() => {
    expect(successIndicator).toBeInTheDocument();
  });
};

export const expectErrorNotification = async (message?: string | RegExp) => {
  const errorIndicator = message
    ? screen.getByText(message)
    : screen.getByText(/error|failed|invalid/i);

  await waitFor(() => {
    expect(errorIndicator).toBeInTheDocument();
  });
};

// Data loading testing utilities
export const expectLoadingState = () => {
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
};

export const expectEmptyState = (emptyMessage: string | RegExp) => {
  expect(screen.getByText(emptyMessage)).toBeInTheDocument();
};

export const expectDataToLoad = async (dataTestId: string) => {
  await waitFor(() => {
    expect(screen.getByTestId(dataTestId)).toBeInTheDocument();
  });
};

// Accessibility testing utilities
export const expectProperAriaLabels = (elements: HTMLElement[]) => {
  elements.forEach((element) => {
    const hasAriaLabel = element.hasAttribute('aria-label');
    const hasAriaLabelledBy = element.hasAttribute('aria-labelledby');
    const hasAriaDescribedBy = element.hasAttribute('aria-describedby');

    expect(hasAriaLabel || hasAriaLabelledBy || hasAriaDescribedBy).toBe(true);
  });
};

export const expectKeyboardNavigation = async (elements: HTMLElement[]) => {
  const user = userEvent.setup();

  for (const element of elements) {
    await user.tab();
    expect(element).toHaveFocus();
  }
};

// Performance testing utilities
export const measureRenderTime = async (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  await waitForLoadingToFinish();
  const end = performance.now();
  return end - start;
};

export const expectFastRender = async (renderFn: () => void, threshold = 100) => {
  const renderTime = await measureRenderTime(renderFn);
  expect(renderTime).toBeLessThan(threshold);
};

// Integration testing utilities
export const simulateAPIError = (status = 500, message = 'Server Error') => {
  return Promise.reject(new Error(`HTTP ${status}: ${message}`));
};

export const simulateNetworkDelay = (delay = 1000) => {
  return new Promise((resolve) => setTimeout(resolve, delay));
};

export const simulateOfflineMode = () => {
  Object.defineProperty(navigator, 'onLine', {
    writable: true,
    value: false,
  });

  window.dispatchEvent(new Event('offline'));
};

export const simulateOnlineMode = () => {
  Object.defineProperty(navigator, 'onLine', {
    writable: true,
    value: true,
  });

  window.dispatchEvent(new Event('online'));
};

// Test data generators
export const generateTestData = <T,>(generator: (index: number) => T, count: number): T[] => {
  return Array.from({ length: count }, (_, index) => generator(index));
};

export const randomString = (length = 8) => {
  return Math.random()
    .toString(36)
    .substring(2, 2 + length);
};

export const randomEmail = () => {
  return `test${randomString()}@example.com`;
};

export const randomPhoneNumber = () => {
  const area = Math.floor(Math.random() * 900) + 100;
  const exchange = Math.floor(Math.random() * 900) + 100;
  const number = Math.floor(Math.random() * 9000) + 1000;
  return `+1-${area}-${exchange}-${number}`;
};

export const randomDate = (start = new Date(2023, 0, 1), end = new Date()) => {
  return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
};

export const randomCurrency = (min = 10, max = 1000) => {
  return Number((Math.random() * (max - min) + min).toFixed(2));
};

// Screenshot testing utilities (for visual regression)
export const expectVisualMatch = async (elementTestId: string, snapshotName: string) => {
  const element = screen.getByTestId(elementTestId);
  expect(element).toMatchSnapshot(snapshotName);
};

// Component state testing
export const expectComponentState = (component: any, expectedState: Record<string, any>) => {
  Object.entries(expectedState).forEach(([key, value]) => {
    expect(component).toHaveProperty(key, value);
  });
};

// Custom matchers
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeWithinRange(floor: number, ceiling: number): R;
      toHaveValidEmailFormat(): R;
      toHaveValidPhoneFormat(): R;
    }
  }
}

expect.extend({
  toBeWithinRange(received: number, floor: number, ceiling: number) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },

  toHaveValidEmailFormat(received: string) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const pass = emailRegex.test(received);
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid email format`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid email format`,
        pass: false,
      };
    }
  },

  toHaveValidPhoneFormat(received: string) {
    const phoneRegex = /^\+1-\d{3}-\d{3}-\d{4}$/;
    const pass = phoneRegex.test(received);
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid phone format`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid phone format`,
        pass: false,
      };
    }
  },
});
