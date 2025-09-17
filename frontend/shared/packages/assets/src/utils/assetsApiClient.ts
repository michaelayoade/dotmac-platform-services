import type {
  Asset,
  AssetHistory,
  MaintenanceSchedule,
  MaintenanceRecord,
  InventoryItem,
  AssetPart,
  Location,
  AssetMetrics,
  MaintenanceMetrics,
  CreateAssetRequest,
  UpdateAssetRequest,
  CreateMaintenanceScheduleRequest,
  CreateMaintenanceRecordRequest,
  AssetListResponse,
  AssetHistoryResponse,
  LocationListResponse,
  AssetSearchFilters,
  MaintenanceSearchFilters,
} from '../types';

/**
 * Assets API client for asset lifecycle management functionality
 * Follows DRY patterns and integrates with existing shared services
 */
export class AssetsApiClient {
  private baseURL: string;
  private tenantId?: string | undefined;

  constructor(baseURL: string, tenantId?: string) {
    this.baseURL = baseURL;
    this.tenantId = tenantId;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(this.tenantId && { 'X-Tenant-ID': this.tenantId }),
      ...((options.headers as Record<string, string>) || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`Assets API error: ${response.statusText}`);
    }

    return response.json();
  }

  // Asset Management APIs
  async getAssets(params?: {
    page?: number;
    per_page?: number;
    filters?: AssetSearchFilters;
  }): Promise<AssetListResponse> {
    const searchParams = params
      ? new URLSearchParams(
          Object.entries({
            ...params,
            ...params.filters,
          })
            .filter(([, value]) => value !== undefined)
            .map(([key, value]) => [key, String(value)])
        ).toString()
      : '';

    return this.request(`/assets${searchParams ? `?${searchParams}` : ''}`);
  }

  async getAsset(assetId: string): Promise<Asset> {
    return this.request(`/assets/${assetId}`);
  }

  async createAsset(data: CreateAssetRequest): Promise<Asset> {
    return this.request('/assets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAsset(assetId: string, data: UpdateAssetRequest): Promise<Asset> {
    return this.request(`/assets/${assetId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteAsset(assetId: string): Promise<void> {
    return this.request(`/assets/${assetId}`, {
      method: 'DELETE',
    });
  }

  async transferAsset(
    assetId: string,
    data: {
      location_id?: string;
      assigned_to?: string;
      notes?: string;
    }
  ): Promise<Asset> {
    return this.request(`/assets/${assetId}/transfer`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async retireAsset(
    assetId: string,
    data: {
      retirement_date: Date;
      reason: string;
      disposal_method?: string;
    }
  ): Promise<Asset> {
    return this.request(`/assets/${assetId}/retire`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Asset History APIs
  async getAssetHistory(
    assetId: string,
    params?: {
      page?: number;
      per_page?: number;
    }
  ): Promise<AssetHistoryResponse> {
    const searchParams = params
      ? new URLSearchParams(
          Object.entries(params)
            .filter(([, value]) => value !== undefined)
            .map(([key, value]) => [key, String(value)])
        ).toString()
      : '';

    return this.request(`/assets/${assetId}/history${searchParams ? `?${searchParams}` : ''}`);
  }

  // Maintenance Management APIs
  async getMaintenanceSchedules(params?: {
    asset_id?: string;
    filters?: MaintenanceSearchFilters;
  }): Promise<MaintenanceSchedule[]> {
    const searchParams = params
      ? new URLSearchParams(
          Object.entries({
            ...params,
            ...params.filters,
          })
            .filter(([, value]) => value !== undefined)
            .map(([key, value]) => [key, String(value)])
        ).toString()
      : '';

    return this.request(`/maintenance/schedules${searchParams ? `?${searchParams}` : ''}`);
  }

  async createMaintenanceSchedule(
    data: CreateMaintenanceScheduleRequest
  ): Promise<MaintenanceSchedule> {
    return this.request('/maintenance/schedules', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateMaintenanceSchedule(
    scheduleId: string,
    data: Partial<CreateMaintenanceScheduleRequest>
  ): Promise<MaintenanceSchedule> {
    return this.request(`/maintenance/schedules/${scheduleId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteMaintenanceSchedule(scheduleId: string): Promise<void> {
    return this.request(`/maintenance/schedules/${scheduleId}`, {
      method: 'DELETE',
    });
  }

  async getMaintenanceRecords(params?: {
    asset_id?: string;
    schedule_id?: string;
    filters?: MaintenanceSearchFilters;
  }): Promise<MaintenanceRecord[]> {
    const searchParams = params
      ? new URLSearchParams(
          Object.entries({
            ...params,
            ...params.filters,
          })
            .filter(([, value]) => value !== undefined)
            .map(([key, value]) => [key, String(value)])
        ).toString()
      : '';

    return this.request(`/maintenance/records${searchParams ? `?${searchParams}` : ''}`);
  }

  async createMaintenanceRecord(data: CreateMaintenanceRecordRequest): Promise<MaintenanceRecord> {
    return this.request('/maintenance/records', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Inventory Management APIs
  async getInventoryItems(params?: {
    location_id?: string;
    asset_id?: string;
    part_id?: string;
  }): Promise<InventoryItem[]> {
    const searchParams = params
      ? new URLSearchParams(
          Object.entries(params)
            .filter(([, value]) => value !== undefined)
            .map(([key, value]) => [key, String(value)])
        ).toString()
      : '';

    return this.request(`/inventory${searchParams ? `?${searchParams}` : ''}`);
  }

  async updateInventoryItem(
    itemId: string,
    data: {
      quantity?: number;
      location_id?: string;
      condition?: string;
      notes?: string;
    }
  ): Promise<InventoryItem> {
    return this.request(`/inventory/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async moveInventoryItem(
    itemId: string,
    data: {
      from_location_id: string;
      to_location_id: string;
      quantity: number;
      notes?: string;
    }
  ): Promise<InventoryItem> {
    return this.request(`/inventory/${itemId}/move`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Parts Management APIs
  async getParts(): Promise<AssetPart[]> {
    return this.request('/parts');
  }

  async createPart(data: Omit<AssetPart, 'id' | 'created_at' | 'updated_at'>): Promise<AssetPart> {
    return this.request('/parts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePartStock(
    partId: string,
    data: {
      quantity_adjustment: number;
      reason: string;
    }
  ): Promise<AssetPart> {
    return this.request(`/parts/${partId}/stock`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Location Management APIs
  async getLocations(): Promise<LocationListResponse> {
    return this.request('/locations');
  }

  async createLocation(data: Omit<Location, 'id'>): Promise<Location> {
    return this.request('/locations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Metrics and Analytics APIs
  async getAssetMetrics(params?: {
    category?: string;
    location_id?: string;
    date_from?: Date;
    date_to?: Date;
  }): Promise<AssetMetrics> {
    const searchParams = params
      ? new URLSearchParams(
          Object.entries(params)
            .filter(([, value]) => value !== undefined)
            .map(([key, value]) => [
              key,
              value instanceof Date ? value.toISOString() : String(value),
            ])
        ).toString()
      : '';

    return this.request(`/assets/metrics${searchParams ? `?${searchParams}` : ''}`);
  }

  async getMaintenanceMetrics(params?: {
    asset_id?: string;
    date_from?: Date;
    date_to?: Date;
  }): Promise<MaintenanceMetrics> {
    const searchParams = params
      ? new URLSearchParams(
          Object.entries(params)
            .filter(([, value]) => value !== undefined)
            .map(([key, value]) => [
              key,
              value instanceof Date ? value.toISOString() : String(value),
            ])
        ).toString()
      : '';

    return this.request(`/maintenance/metrics${searchParams ? `?${searchParams}` : ''}`);
  }

  // Depreciation APIs
  async calculateDepreciation(assetId: string): Promise<{
    current_value: number;
    annual_depreciation: number;
    accumulated_depreciation: number;
    remaining_value: number;
  }> {
    return this.request(`/assets/${assetId}/depreciation`);
  }

  // Barcode/QR Code APIs
  async generateBarcode(assetId: string): Promise<{ barcode: string; image_url: string }> {
    return this.request(`/assets/${assetId}/barcode`, {
      method: 'POST',
    });
  }

  async generateQRCode(assetId: string): Promise<{ qr_code: string; image_url: string }> {
    return this.request(`/assets/${assetId}/qr-code`, {
      method: 'POST',
    });
  }

  async scanBarcode(barcode: string): Promise<Asset> {
    return this.request(`/assets/scan/${encodeURIComponent(barcode)}`);
  }
}

// Factory function following DRY patterns
export const createAssetsApiClient = (baseURL: string, tenantId?: string): AssetsApiClient => {
  return new AssetsApiClient(baseURL, tenantId);
};

// Default instance for common use
export const assetsApiClient = new AssetsApiClient(
  process.env.NEXT_PUBLIC_API_URL || '/api',
  process.env.NEXT_PUBLIC_TENANT_ID
);
