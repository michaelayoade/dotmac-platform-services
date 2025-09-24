import { useState, useCallback, useEffect } from 'react';

// Customer types based on our backend schemas
export interface Customer {
  id: string;
  customer_number: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  display_name?: string;
  company_name?: string;
  email: string;
  phone?: string;
  mobile?: string;
  customer_type: 'individual' | 'business' | 'enterprise' | 'partner' | 'vendor';
  tier: 'free' | 'basic' | 'standard' | 'premium' | 'enterprise';
  status: 'prospect' | 'active' | 'inactive' | 'suspended' | 'churned' | 'archived';
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state_province?: string;
  postal_code?: string;
  country?: string;
  lifetime_value: number;
  total_purchases: number;
  last_purchase_date?: string;
  first_purchase_date?: string;
  average_order_value: number;
  created_at: string;
  updated_at: string;
  tags: string[];
  metadata: Record<string, any>;
  custom_fields: Record<string, any>;
}

export interface CustomerSearchParams {
  query?: string;
  email?: string;
  status?: string;
  customer_type?: string;
  tier?: string;
  country?: string;
  city?: string;
  tags?: string[];
  page?: number;
  page_size?: number;
}

export interface CustomerMetrics {
  total_customers: number;
  active_customers: number;
  new_customers_this_month: number;
  churn_rate: number;
  average_lifetime_value: number;
  total_revenue: number;
  customers_by_status: Record<string, number>;
  customers_by_tier: Record<string, number>;
  customers_by_type: Record<string, number>;
  top_segments: Array<{ name: string; count: number }>;
}

export interface CustomerActivity {
  id: string;
  customer_id: string;
  activity_type: string;
  title: string;
  description?: string;
  metadata: Record<string, any>;
  performed_by?: string;
  created_at: string;
}

export interface CustomerNote {
  id: string;
  customer_id: string;
  subject: string;
  content: string;
  is_internal: boolean;
  created_by_id: string;
  created_at: string;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Helper function to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

// Helper function to handle API responses
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    if (response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      return;
    }
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
};

export const useCustomers = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<CustomerMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    page_size: 50,
    has_next: false,
    has_prev: false,
  });

  // Fetch customer metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/customers/metrics/overview`, {
        headers: getAuthHeaders(),
      });
      const data = await handleResponse(response);
      setMetrics(data);
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      setError('Failed to fetch customer metrics');
    }
  }, []);

  // Search customers
  const searchCustomers = useCallback(async (params: CustomerSearchParams = {}) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/customers/search`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          ...params,
          page: params.page || 1,
          page_size: params.page_size || 50,
        }),
      });

      const data = await handleResponse(response);
      setCustomers(data.customers || []);
      setPagination({
        total: data.total || 0,
        page: data.page || 1,
        page_size: data.page_size || 50,
        has_next: data.has_next || false,
        has_prev: data.has_prev || false,
      });
    } catch (err) {
      console.error('Failed to search customers:', err);
      setError('Failed to search customers');
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create customer
  const createCustomer = useCallback(async (customerData: Partial<Customer>) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/customers/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(customerData),
      });

      const newCustomer = await handleResponse(response);
      return newCustomer;
    } catch (err) {
      console.error('Failed to create customer:', err);
      setError('Failed to create customer');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update customer
  const updateCustomer = useCallback(async (customerId: string, customerData: Partial<Customer>) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/customers/${customerId}`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(customerData),
      });

      const updatedCustomer = await handleResponse(response);

      // Update the customer in the local state
      setCustomers(prev =>
        prev.map(customer =>
          customer.id === customerId ? updatedCustomer : customer
        )
      );

      return updatedCustomer;
    } catch (err) {
      console.error('Failed to update customer:', err);
      setError('Failed to update customer');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete customer
  const deleteCustomer = useCallback(async (customerId: string, hardDelete = false) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/customers/${customerId}?hard_delete=${hardDelete}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (response.status === 204) {
        // Remove from local state
        setCustomers(prev => prev.filter(customer => customer.id !== customerId));
        return true;
      }
    } catch (err) {
      console.error('Failed to delete customer:', err);
      setError('Failed to delete customer');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get customer by ID
  const getCustomer = useCallback(async (customerId: string, includeActivities = false, includeNotes = false) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (includeActivities) params.append('include_activities', 'true');
      if (includeNotes) params.append('include_notes', 'true');

      const response = await fetch(`${API_BASE_URL}/customers/${customerId}?${params}`, {
        headers: getAuthHeaders(),
      });

      return await handleResponse(response);
    } catch (err) {
      console.error('Failed to get customer:', err);
      setError('Failed to get customer');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Refresh current data
  const refreshCustomers = useCallback(() => {
    searchCustomers();
    fetchMetrics();
  }, [searchCustomers, fetchMetrics]);

  // Load initial data
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return {
    customers,
    loading,
    error,
    metrics,
    pagination,
    searchCustomers,
    createCustomer,
    updateCustomer,
    deleteCustomer,
    getCustomer,
    refreshCustomers,
  };
};

export const useCustomerActivities = (customerId: string) => {
  const [activities, setActivities] = useState<CustomerActivity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchActivities = useCallback(async (limit = 50, offset = 0) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/customers/${customerId}/activities?limit=${limit}&offset=${offset}`, {
        headers: getAuthHeaders(),
      });

      const data = await handleResponse(response);
      setActivities(data || []);
    } catch (err) {
      console.error('Failed to fetch activities:', err);
      setError('Failed to fetch activities');
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  const addActivity = useCallback(async (activityData: Omit<CustomerActivity, 'id' | 'customer_id' | 'created_at'>) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/customers/${customerId}/activities`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(activityData),
      });

      const newActivity = await handleResponse(response);
      setActivities(prev => [newActivity, ...prev]);
      return newActivity;
    } catch (err) {
      console.error('Failed to add activity:', err);
      setError('Failed to add activity');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    if (customerId) {
      fetchActivities();
    }
  }, [customerId, fetchActivities]);

  return {
    activities,
    loading,
    error,
    fetchActivities,
    addActivity,
  };
};

export const useCustomerNotes = (customerId: string) => {
  const [notes, setNotes] = useState<CustomerNote[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNotes = useCallback(async (includeInternal = true, limit = 50, offset = 0) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('include_internal', includeInternal.toString());
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());

      const response = await fetch(`${API_BASE_URL}/customers/${customerId}/notes?${params}`, {
        headers: getAuthHeaders(),
      });

      const data = await handleResponse(response);
      setNotes(data || []);
    } catch (err) {
      console.error('Failed to fetch notes:', err);
      setError('Failed to fetch notes');
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  const addNote = useCallback(async (noteData: Omit<CustomerNote, 'id' | 'customer_id' | 'created_by_id' | 'created_at'>) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/customers/${customerId}/notes`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(noteData),
      });

      const newNote = await handleResponse(response);
      setNotes(prev => [newNote, ...prev]);
      return newNote;
    } catch (err) {
      console.error('Failed to add note:', err);
      setError('Failed to add note');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    if (customerId) {
      fetchNotes();
    }
  }, [customerId, fetchNotes]);

  return {
    notes,
    loading,
    error,
    fetchNotes,
    addNote,
  };
};