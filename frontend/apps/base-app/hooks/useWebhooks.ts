import { useState, useEffect, useCallback } from 'react';

export interface WebhookSubscription {
  id: string;
  user_id: string;
  name: string;
  url: string;
  events: string[];
  description?: string;
  headers: Record<string, string>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_delivery_at?: string;
  total_deliveries: number;
  failed_deliveries: number;
  has_secret: boolean;
}

export interface WebhookSubscriptionCreate {
  url: string;
  events: string[];
  name: string;
  description?: string;
  secret?: string;
  headers?: Record<string, string>;
  is_active?: boolean;
}

export interface WebhookSubscriptionUpdate {
  url?: string;
  events?: string[];
  name?: string;
  description?: string;
  secret?: string;
  headers?: Record<string, string>;
  is_active?: boolean;
}

export interface WebhookDelivery {
  id: string;
  subscription_id: string;
  event_type: string;
  status: string;
  response_status?: number;
  response_body?: string;
  error_message?: string;
  delivered_at: string;
  retry_count: number;
  next_retry_at?: string;
}

export interface WebhookTestResult {
  success: boolean;
  status_code?: number;
  response_body?: string;
  error_message?: string;
  delivery_time_ms: number;
}

export interface AvailableEvents {
  [key: string]: {
    name: string;
    description: string;
  };
}

// Mock data
const mockWebhooks: WebhookSubscription[] = [
  {
    id: '1',
    user_id: 'user1',
    name: 'Customer Events',
    url: 'https://api.example.com/webhooks/customers',
    events: ['customer.created', 'customer.updated'],
    description: 'Receive customer lifecycle events',
    headers: { 'Authorization': 'Bearer token123' },
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    last_delivery_at: new Date(Date.now() - 3600000).toISOString(),
    total_deliveries: 45,
    failed_deliveries: 2,
    has_secret: true,
  },
  {
    id: '2',
    user_id: 'user1',
    name: 'Order Notifications',
    url: 'https://webhook.site/unique-id',
    events: ['order.created', 'order.completed', 'payment.success'],
    description: 'Track order and payment events',
    headers: {},
    is_active: false,
    created_at: new Date(Date.now() - 604800000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    total_deliveries: 12,
    failed_deliveries: 0,
    has_secret: false,
  },
];

const mockDeliveries: WebhookDelivery[] = [
  {
    id: 'delivery1',
    subscription_id: '1',
    event_type: 'customer.created',
    status: 'success',
    response_status: 200,
    response_body: 'OK',
    delivered_at: new Date(Date.now() - 3600000).toISOString(),
    retry_count: 0,
  },
  {
    id: 'delivery2',
    subscription_id: '1',
    event_type: 'customer.updated',
    status: 'failed',
    response_status: 500,
    error_message: 'Internal Server Error',
    delivered_at: new Date(Date.now() - 7200000).toISOString(),
    retry_count: 2,
    next_retry_at: new Date(Date.now() + 1800000).toISOString(),
  },
];

const mockAvailableEvents: AvailableEvents = {
  'customer.created': {
    name: 'Customer Created',
    description: 'Triggered when a new customer is created',
  },
  'customer.updated': {
    name: 'Customer Updated',
    description: 'Triggered when a customer is updated',
  },
  'customer.deleted': {
    name: 'Customer Deleted',
    description: 'Triggered when a customer is deleted',
  },
  'order.created': {
    name: 'Order Created',
    description: 'Triggered when a new order is placed',
  },
  'order.updated': {
    name: 'Order Updated',
    description: 'Triggered when an order is updated',
  },
  'order.completed': {
    name: 'Order Completed',
    description: 'Triggered when an order is completed',
  },
  'payment.success': {
    name: 'Payment Success',
    description: 'Triggered when a payment is successful',
  },
  'payment.failed': {
    name: 'Payment Failed',
    description: 'Triggered when a payment fails',
  },
  'user.created': {
    name: 'User Created',
    description: 'Triggered when a new user is created',
  },
  'user.updated': {
    name: 'User Updated',
    description: 'Triggered when a user is updated',
  },
  'system.alert': {
    name: 'System Alert',
    description: 'Triggered for system alerts and notifications',
  },
};

export function useWebhooks() {
  const [webhooks, setWebhooks] = useState<WebhookSubscription[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWebhooks = useCallback(async (
    page = 1,
    limit = 50,
    eventFilter?: string,
    activeOnly = false
  ) => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      let filteredWebhooks = [...mockWebhooks];

      if (eventFilter) {
        filteredWebhooks = filteredWebhooks.filter(webhook =>
          webhook.events.includes(eventFilter)
        );
      }

      if (activeOnly) {
        filteredWebhooks = filteredWebhooks.filter(webhook => webhook.is_active);
      }

      const startIdx = (page - 1) * limit;
      const endIdx = startIdx + limit;
      const paginatedWebhooks = filteredWebhooks.slice(startIdx, endIdx);

      setWebhooks(paginatedWebhooks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch webhooks');
    } finally {
      setLoading(false);
    }
  }, []);

  const createWebhook = useCallback(async (data: WebhookSubscriptionCreate): Promise<WebhookSubscription> => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newWebhook: WebhookSubscription = {
        id: Date.now().toString(),
        user_id: 'user1',
        name: data.name,
        url: data.url,
        events: data.events,
        description: data.description,
        headers: data.headers || {},
        is_active: data.is_active !== false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        total_deliveries: 0,
        failed_deliveries: 0,
        has_secret: !!data.secret,
      };

      setWebhooks(prev => [newWebhook, ...prev]);
      return newWebhook;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create webhook';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateWebhook = useCallback(async (
    id: string,
    data: WebhookSubscriptionUpdate
  ): Promise<WebhookSubscription> => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      const existingWebhook = webhooks.find(webhook => webhook.id === id);
      if (!existingWebhook) {
        throw new Error('Webhook not found');
      }

      const updatedWebhook: WebhookSubscription = {
        ...existingWebhook,
        ...data,
        updated_at: new Date().toISOString(),
      };

      setWebhooks(prev => prev.map(webhook => webhook.id === id ? updatedWebhook : webhook));
      return updatedWebhook;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update webhook';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [webhooks]);

  const deleteWebhook = useCallback(async (id: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      setWebhooks(prev => prev.filter(webhook => webhook.id !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete webhook';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const testWebhook = useCallback(async (
    id: string,
    eventType: string,
    payload?: Record<string, any>
  ): Promise<WebhookTestResult> => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 500));

      // Simulate random success/failure
      const success = Math.random() > 0.3;

      if (success) {
        return {
          success: true,
          status_code: 200,
          response_body: 'OK',
          delivery_time_ms: Math.floor(Math.random() * 500 + 100),
        };
      } else {
        return {
          success: false,
          status_code: 500,
          error_message: 'Internal Server Error',
          delivery_time_ms: Math.floor(Math.random() * 1000 + 200),
        };
      }
    } catch (err) {
      return {
        success: false,
        error_message: err instanceof Error ? err.message : 'Test failed',
        delivery_time_ms: 0,
      };
    }
  }, []);

  const getAvailableEvents = useCallback(async (): Promise<AvailableEvents> => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 100));
    return mockAvailableEvents;
  }, []);

  useEffect(() => {
    fetchWebhooks();
  }, [fetchWebhooks]);

  return {
    webhooks,
    loading,
    error,
    fetchWebhooks,
    createWebhook,
    updateWebhook,
    deleteWebhook,
    testWebhook,
    getAvailableEvents,
  };
}

export function useWebhookDeliveries(subscriptionId: string) {
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDeliveries = useCallback(async (
    page = 1,
    limit = 50,
    statusFilter?: string
  ) => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 300));

      let filteredDeliveries = mockDeliveries.filter(
        delivery => delivery.subscription_id === subscriptionId
      );

      if (statusFilter) {
        filteredDeliveries = filteredDeliveries.filter(
          delivery => delivery.status === statusFilter
        );
      }

      const startIdx = (page - 1) * limit;
      const endIdx = startIdx + limit;
      const paginatedDeliveries = filteredDeliveries.slice(startIdx, endIdx);

      setDeliveries(paginatedDeliveries);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch deliveries');
    } finally {
      setLoading(false);
    }
  }, [subscriptionId]);

  const retryDelivery = useCallback(async (deliveryId: string): Promise<void> => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      // Update delivery status optimistically
      setDeliveries(prev => prev.map(delivery =>
        delivery.id === deliveryId
          ? { ...delivery, retry_count: delivery.retry_count + 1 }
          : delivery
      ));
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to retry delivery');
    }
  }, []);

  useEffect(() => {
    if (subscriptionId) {
      fetchDeliveries();
    }
  }, [subscriptionId, fetchDeliveries]);

  return {
    deliveries,
    loading,
    error,
    fetchDeliveries,
    retryDelivery,
  };
}