import { useState, useEffect, useCallback } from 'react';

export interface APIKey {
  id: string;
  name: string;
  scopes: string[];
  created_at: string;
  expires_at?: string;
  description?: string;
  last_used_at?: string;
  is_active: boolean;
  key_preview: string;
}

export interface APIKeyCreateResponse extends APIKey {
  api_key: string;
}

export interface APIKeyCreateRequest {
  name: string;
  scopes: string[];
  expires_at?: string;
  description?: string;
}

export interface APIKeyUpdateRequest {
  name?: string;
  scopes?: string[];
  description?: string;
  is_active?: boolean;
}

export interface APIKeyListResponse {
  api_keys: APIKey[];
  total: number;
  page: number;
  limit: number;
}

export interface AvailableScopes {
  [key: string]: {
    name: string;
    description: string;
  };
}

// Mock API functions - replace with actual API calls
const mockApiKeys: APIKey[] = [
  {
    id: '1',
    name: 'Production API Key',
    scopes: ['read', 'write', 'customers:read'],
    created_at: new Date().toISOString(),
    description: 'Main production API key',
    is_active: true,
    key_preview: 'sk_****ABC123',
    last_used_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: '2',
    name: 'Analytics Integration',
    scopes: ['analytics:read'],
    created_at: new Date(Date.now() - 604800000).toISOString(),
    description: 'For analytics dashboard integration',
    is_active: true,
    key_preview: 'sk_****DEF456',
  },
];

const mockAvailableScopes: AvailableScopes = {
  read: {
    name: 'Read Access',
    description: 'Read-only access to resources',
  },
  write: {
    name: 'Write Access',
    description: 'Create and update resources',
  },
  delete: {
    name: 'Delete Access',
    description: 'Delete resources',
  },
  'customers:read': {
    name: 'Read Customers',
    description: 'View customer information',
  },
  'customers:write': {
    name: 'Manage Customers',
    description: 'Create and update customers',
  },
  'webhooks:manage': {
    name: 'Manage Webhooks',
    description: 'Create and manage webhook subscriptions',
  },
  'analytics:read': {
    name: 'Read Analytics',
    description: 'Access analytics and reporting data',
  },
};

export function useApiKeys() {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchApiKeys = useCallback(async (page = 1, limit = 50) => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      // For now, return mock data
      const startIdx = (page - 1) * limit;
      const endIdx = startIdx + limit;
      const paginatedKeys = mockApiKeys.slice(startIdx, endIdx);

      setApiKeys(paginatedKeys);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch API keys');
    } finally {
      setLoading(false);
    }
  }, []);

  const createApiKey = useCallback(async (data: APIKeyCreateRequest): Promise<APIKeyCreateResponse> => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newApiKey: APIKeyCreateResponse = {
        id: Date.now().toString(),
        name: data.name,
        scopes: data.scopes,
        created_at: new Date().toISOString(),
        expires_at: data.expires_at,
        description: data.description,
        is_active: true,
        key_preview: `sk_****${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
        api_key: `sk_${Math.random().toString(36).substring(2)}${Math.random().toString(36).substring(2)}`,
      };

      // Add to local state
      setApiKeys(prev => [newApiKey, ...prev]);

      return newApiKey;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create API key';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateApiKey = useCallback(async (id: string, data: APIKeyUpdateRequest): Promise<APIKey> => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      const existingKey = apiKeys.find(key => key.id === id);
      if (!existingKey) {
        throw new Error('API key not found');
      }

      const updatedKey: APIKey = {
        ...existingKey,
        ...data,
      };

      // Update local state
      setApiKeys(prev => prev.map(key => key.id === id ? updatedKey : key));

      return updatedKey;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update API key';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [apiKeys]);

  const revokeApiKey = useCallback(async (id: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      // Remove from local state
      setApiKeys(prev => prev.filter(key => key.id !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to revoke API key';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const getAvailableScopes = useCallback(async (): Promise<AvailableScopes> => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 100));
    return mockAvailableScopes;
  }, []);

  useEffect(() => {
    fetchApiKeys();
  }, [fetchApiKeys]);

  return {
    apiKeys,
    loading,
    error,
    fetchApiKeys,
    createApiKey,
    updateApiKey,
    revokeApiKey,
    getAvailableScopes,
  };
}