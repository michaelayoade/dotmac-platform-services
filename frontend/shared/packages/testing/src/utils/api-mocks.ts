import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// Mock data generators
export const mockCustomer = (overrides = {}) => ({
  id: `customer_${Math.random().toString(36).substr(2, 9)}`,
  name: 'John Doe',
  email: 'john.doe@example.com',
  phone: '+1-555-0123',
  address: {
    street: '123 Main St',
    city: 'Anytown',
    state: 'NY',
    zip: '12345',
  },
  status: 'active',
  services: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  ...overrides,
});

export const mockInvoice = (overrides = {}) => ({
  id: `invoice_${Math.random().toString(36).substr(2, 9)}`,
  invoiceNumber: `INV-${Math.floor(Math.random() * 10000)}`,
  customerId: 'customer_123',
  status: 'sent',
  issueDate: new Date().toISOString(),
  dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  totalAmount: 99.99,
  amountDue: 99.99,
  lineItems: [
    {
      id: 'line_1',
      description: 'Internet Service - Monthly',
      quantity: 1,
      unitPrice: 99.99,
      amount: 99.99,
    },
  ],
  ...overrides,
});

export const mockPayment = (overrides = {}) => ({
  id: `payment_${Math.random().toString(36).substr(2, 9)}`,
  invoiceId: 'invoice_123',
  customerId: 'customer_123',
  amount: 99.99,
  status: 'completed',
  method: {
    id: 'pm_123',
    type: 'credit_card',
    lastFour: '4242',
    brand: 'visa',
    isDefault: true,
  },
  processedAt: new Date().toISOString(),
  ...overrides,
});

export const mockProvisioningRequest = (overrides = {}) => ({
  id: `req_${Math.random().toString(36).substr(2, 9)}`,
  customerId: 'customer_123',
  serviceTemplateId: 'template_fiber_100',
  status: 'pending',
  priority: 'medium',
  requestedAt: new Date().toISOString(),
  installationAddress: {
    street: '123 Main St',
    city: 'Anytown',
    state: 'NY',
    zip: '12345',
  },
  customerInfo: {
    name: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+1-555-0123',
  },
  tasks: [],
  equipment: [],
  ...overrides,
});

export const mockCommissionData = (overrides = {}) => ({
  id: `comm_${Math.random().toString(36).substr(2, 9)}`,
  resellerId: 'reseller_123',
  customerId: 'customer_123',
  serviceId: 'service_123',
  type: 'recurring',
  amount: 15.0,
  rate: 0.15,
  baseAmount: 100.0,
  status: 'earned',
  period: {
    start: new Date().toISOString(),
    end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  },
  ...overrides,
});

export const mockNotification = (overrides = {}) => ({
  id: `notif_${Math.random().toString(36).substr(2, 9)}`,
  type: 'info',
  priority: 'medium',
  title: 'Test Notification',
  message: 'This is a test notification',
  channel: ['browser'],
  timestamp: new Date(),
  read: false,
  persistent: false,
  ...overrides,
});

// API Mock Handlers
export const handlers = [
  // Analytics API
  http.get('/api/analytics/metrics', () => {
    return HttpResponse.json({
      metrics: {
        totalCustomers: 1250,
        activeServices: 2100,
        monthlyRevenue: 125000,
        conversionRate: 0.23,
        customerSatisfaction: 4.6,
        churnRate: 0.05,
      },
      trends: {
        customers: [1200, 1220, 1235, 1250],
        revenue: [120000, 122000, 123500, 125000],
      },
    });
  }),

  // Billing API
  http.get('/api/billing/invoices', () => {
    const invoices = Array.from({ length: 10 }, () => mockInvoice());
    return HttpResponse.json({ invoices });
  }),

  http.post('/api/billing/invoices', () => {
    return HttpResponse.json({ invoice: mockInvoice() });
  }),

  http.get('/api/billing/payments', () => {
    const payments = Array.from({ length: 5 }, () => mockPayment());
    return HttpResponse.json({ payments });
  }),

  http.post('/api/billing/payments', () => {
    return HttpResponse.json({ payment: mockPayment({ status: 'completed' }) });
  }),

  // Provisioning API
  http.get('/api/provisioning/requests', () => {
    const requests = Array.from({ length: 8 }, () => mockProvisioningRequest());
    return HttpResponse.json({ requests });
  }),

  http.post('/api/provisioning/requests', () => {
    return HttpResponse.json({ request: mockProvisioningRequest() });
  }),

  // Commission API
  http.get('/api/commissions', () => {
    const commissions = Array.from({ length: 15 }, () => mockCommissionData());
    const stats = {
      totalEarned: 2350.5,
      monthlyEarned: 450.75,
      totalCustomers: 125,
      avgCommissionPerCustomer: 18.8,
      projectedAnnual: 5400.0,
    };
    return HttpResponse.json({ commissions, stats });
  }),

  // Communication API
  http.get('/api/communication/messages', () => {
    const messages = Array.from({ length: 10 }, (_, i) => ({
      id: `msg_${i}`,
      recipient: `customer${i}@example.com`,
      subject: `Message ${i + 1}`,
      status: ['sent', 'delivered', 'failed'][i % 3],
      sentAt: new Date(Date.now() - i * 60 * 60 * 1000).toISOString(),
    }));
    return HttpResponse.json({ messages });
  }),

  http.post('/api/communication/messages', () => {
    return HttpResponse.json({
      message: {
        id: 'msg_new',
        status: 'sent',
        sentAt: new Date().toISOString(),
      },
    });
  }),

  // Territory API
  http.get('/api/territory/data', () => {
    return HttpResponse.json({
      territories: [
        {
          id: 'territory_1',
          name: 'Downtown Area',
          coordinates: [
            [-74.0059, 40.7128],
            [-74.0059, 40.7228],
            [-73.9959, 40.7228],
            [-73.9959, 40.7128],
          ],
        },
      ],
      customers: Array.from({ length: 20 }, (_, i) => ({
        id: `customer_${i}`,
        name: `Customer ${i + 1}`,
        location: {
          lat: 40.7128 + (Math.random() - 0.5) * 0.1,
          lng: -74.0059 + (Math.random() - 0.5) * 0.1,
        },
        status: ['active', 'inactive', 'prospect'][i % 3],
      })),
    });
  }),

  // Error simulation handlers
  http.get('/api/error/500', () => {
    return HttpResponse.json({ message: 'Internal Server Error' }, { status: 500 });
  }),

  http.get('/api/error/404', () => {
    return HttpResponse.json({ message: 'Not Found' }, { status: 404 });
  }),

  http.get('/api/error/timeout', () => {
    return new Promise(() => {}); // Never resolves
  }),
];

// Test server setup
export const server = setupServer(...handlers);

// Helper functions for testing
export const createMockWebSocket = () => {
  const mockWS = {
    readyState: 0, // WebSocket.CONNECTING
    onopen: null as ((event: Event) => void) | null,
    onmessage: null as ((event: MessageEvent) => void) | null,
    onclose: null as ((event: CloseEvent) => void) | null,
    onerror: null as ((event: Event) => void) | null,
    send: jest.fn(),
    close: jest.fn(),
  };

  const simulateOpen = () => {
    if (mockWS.onopen) {
      mockWS.onopen(new Event('open'));
    }
  };

  const simulateMessage = (data: any) => {
    if (mockWS.onmessage) {
      mockWS.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  };

  const simulateClose = () => {
    mockWS.readyState = 3; // WebSocket.CLOSED
    if (mockWS.onclose) {
      mockWS.onclose(new CloseEvent('close'));
    }
  };

  const simulateError = () => {
    mockWS.readyState = 3; // WebSocket.CLOSED
    if (mockWS.onerror) {
      mockWS.onerror(new Event('error'));
    }
  };

  return { mockWS, simulateOpen, simulateMessage, simulateClose, simulateError };
};

// Test server lifecycle helpers
export const resetMocks = () => {
  server.resetHandlers();
};

export const startTestServer = () => {
  server.listen();
};

export const stopTestServer = () => {
  server.close();
};
