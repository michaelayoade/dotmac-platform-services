export interface Asset {
  id: string;
  asset_number: string;
  name: string;
  description?: string;
  category: AssetCategory;
  type: AssetType;
  status: AssetStatus;
  condition: AssetCondition;
  location?: Location;
  assigned_to?: string; // User/Technician ID
  manufacturer: string;
  model: string;
  serial_number?: string;
  mac_address?: string;
  ip_address?: string;
  purchase_date?: Date;
  purchase_price?: number;
  warranty_expiry?: Date;
  depreciation_schedule?: DepreciationSchedule;
  specifications?: Record<string, any>;
  attachments?: AssetAttachment[];
  tags?: string[];
  custom_fields?: Record<string, any>;
  created_at: Date;
  updated_at: Date;
  created_by: string;
  updated_by: string;
}

export interface AssetHistory {
  id: string;
  asset_id: string;
  event_type: AssetEventType;
  event_date: Date;
  description: string;
  performed_by: string;
  location?: Location;
  cost?: number;
  notes?: string;
  attachments?: AssetAttachment[];
  metadata?: Record<string, any>;
}

export interface MaintenanceSchedule {
  id: string;
  asset_id: string;
  maintenance_type: MaintenanceType;
  frequency: MaintenanceFrequency;
  frequency_value: number; // e.g., 30 for "every 30 days"
  next_due_date: Date;
  estimated_duration: number; // minutes
  estimated_cost?: number;
  assigned_to?: string;
  priority: MaintenancePriority;
  description: string;
  checklist_items: MaintenanceChecklistItem[];
  parts_required?: AssetPart[];
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface MaintenanceRecord {
  id: string;
  asset_id: string;
  schedule_id?: string;
  maintenance_type: MaintenanceType;
  performed_date: Date;
  performed_by: string;
  duration_minutes: number;
  actual_cost?: number;
  status: MaintenanceStatus;
  description: string;
  work_performed: string;
  parts_used?: AssetPart[];
  checklist_completed?: MaintenanceChecklistCompletion[];
  next_maintenance_date?: Date;
  issues_found?: string;
  attachments?: AssetAttachment[];
  created_at: Date;
  updated_at: Date;
}

export interface AssetPart {
  id: string;
  part_number: string;
  name: string;
  description?: string;
  manufacturer: string;
  category: string;
  unit_cost: number;
  quantity_in_stock: number;
  minimum_stock_level: number;
  supplier?: string;
  lead_time_days?: number;
  specifications?: Record<string, any>;
  compatible_assets?: string[]; // Asset IDs
  created_at: Date;
  updated_at: Date;
}

export interface InventoryItem {
  id: string;
  asset_id?: string; // If item is assigned to an asset
  part_id?: string; // If item is a part
  barcode?: string;
  qr_code?: string;
  location: Location;
  quantity: number;
  unit_of_measure: string;
  value_per_unit: number;
  total_value: number;
  expiry_date?: Date;
  batch_number?: string;
  supplier: string;
  purchase_order_number?: string;
  received_date?: Date;
  condition: InventoryCondition;
  notes?: string;
  created_at: Date;
  updated_at: Date;
}

export interface Location {
  id: string;
  name: string;
  type: LocationType;
  address?: string;
  coordinates?: GeoCoordinates;
  parent_location_id?: string;
  level: number; // Hierarchy level
  path: string; // Full path like "Building A > Floor 2 > Room 201"
  capacity?: number;
  is_active: boolean;
  metadata?: Record<string, any>;
}

export interface GeoCoordinates {
  latitude: number;
  longitude: number;
}

export interface AssetAttachment {
  id: string;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  url: string;
  thumbnail_url?: string;
  uploaded_by: string;
  uploaded_at: Date;
  description?: string;
}

export interface DepreciationSchedule {
  method: DepreciationMethod;
  useful_life_years: number;
  salvage_value: number;
  current_value: number;
  annual_depreciation: number;
}

export interface MaintenanceChecklistItem {
  id: string;
  name: string;
  description?: string;
  is_required: boolean;
  order: number;
}

export interface MaintenanceChecklistCompletion {
  item_id: string;
  completed: boolean;
  notes?: string;
  completed_by: string;
  completed_at: Date;
}

export interface AssetMetrics {
  total_assets: number;
  assets_by_status: Record<AssetStatus, number>;
  assets_by_category: Record<AssetCategory, number>;
  total_value: number;
  depreciated_value: number;
  maintenance_costs_ytd: number;
  upcoming_maintenance: number;
  overdue_maintenance: number;
  warranty_expiring_soon: number;
  assets_by_condition: Record<AssetCondition, number>;
}

export interface MaintenanceMetrics {
  total_scheduled: number;
  completed_this_month: number;
  overdue: number;
  upcoming_7_days: number;
  upcoming_30_days: number;
  average_completion_time: number;
  total_cost_ytd: number;
  preventive_vs_corrective: {
    preventive: number;
    corrective: number;
  };
}

// Enums
export enum AssetCategory {
  NETWORK_EQUIPMENT = 'network_equipment',
  CUSTOMER_PREMISES = 'customer_premises',
  INFRASTRUCTURE = 'infrastructure',
  VEHICLES = 'vehicles',
  TOOLS = 'tools',
  OFFICE_EQUIPMENT = 'office_equipment',
  SOFTWARE = 'software',
  OTHER = 'other',
}

export enum AssetType {
  ROUTER = 'router',
  SWITCH = 'switch',
  FIREWALL = 'firewall',
  ACCESS_POINT = 'access_point',
  MODEM = 'modem',
  ONT = 'ont',
  OLT = 'olt',
  FIBER_CABLE = 'fiber_cable',
  COPPER_CABLE = 'copper_cable',
  ANTENNA = 'antenna',
  TOWER = 'tower',
  GENERATOR = 'generator',
  UPS = 'ups',
  PDU = 'pdu',
  RACK = 'rack',
  SERVER = 'server',
  LAPTOP = 'laptop',
  TABLET = 'tablet',
  PHONE = 'phone',
  VEHICLE = 'vehicle',
  TOOL = 'tool',
  OTHER = 'other',
}

export enum AssetStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  IN_MAINTENANCE = 'in_maintenance',
  RETIRED = 'retired',
  DISPOSED = 'disposed',
  LOST = 'lost',
  STOLEN = 'stolen',
  RESERVED = 'reserved',
}

export enum AssetCondition {
  EXCELLENT = 'excellent',
  GOOD = 'good',
  FAIR = 'fair',
  POOR = 'poor',
  NEEDS_REPAIR = 'needs_repair',
  BEYOND_REPAIR = 'beyond_repair',
}

export enum AssetEventType {
  CREATED = 'created',
  UPDATED = 'updated',
  TRANSFERRED = 'transferred',
  ASSIGNED = 'assigned',
  UNASSIGNED = 'unassigned',
  MAINTENANCE_SCHEDULED = 'maintenance_scheduled',
  MAINTENANCE_COMPLETED = 'maintenance_completed',
  CONDITION_CHANGED = 'condition_changed',
  STATUS_CHANGED = 'status_changed',
  DISPOSED = 'disposed',
  WARRANTY_EXPIRED = 'warranty_expired',
}

export enum MaintenanceType {
  PREVENTIVE = 'preventive',
  CORRECTIVE = 'corrective',
  PREDICTIVE = 'predictive',
  CONDITION_BASED = 'condition_based',
  CALIBRATION = 'calibration',
  INSPECTION = 'inspection',
  UPGRADE = 'upgrade',
  REPLACEMENT = 'replacement',
}

export enum MaintenanceFrequency {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  SEMI_ANNUAL = 'semi_annual',
  ANNUAL = 'annual',
  CUSTOM = 'custom',
}

export enum MaintenancePriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export enum MaintenanceStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  DEFERRED = 'deferred',
}

export enum DepreciationMethod {
  STRAIGHT_LINE = 'straight_line',
  DECLINING_BALANCE = 'declining_balance',
  UNITS_OF_PRODUCTION = 'units_of_production',
}

export enum LocationType {
  BUILDING = 'building',
  FLOOR = 'floor',
  ROOM = 'room',
  RACK = 'rack',
  SHELF = 'shelf',
  WAREHOUSE = 'warehouse',
  SITE = 'site',
  VEHICLE = 'vehicle',
  OUTDOOR = 'outdoor',
}

export enum InventoryCondition {
  NEW = 'new',
  USED = 'used',
  REFURBISHED = 'refurbished',
  DAMAGED = 'damaged',
  EXPIRED = 'expired',
}

// API Request/Response Types
export interface CreateAssetRequest {
  asset_number?: string;
  name: string;
  description?: string;
  category: AssetCategory;
  type: AssetType;
  location_id?: string;
  manufacturer: string;
  model: string;
  serial_number?: string;
  mac_address?: string;
  ip_address?: string;
  purchase_date?: Date;
  purchase_price?: number;
  warranty_expiry?: Date;
  specifications?: Record<string, any>;
  tags?: string[];
  custom_fields?: Record<string, any>;
}

export interface UpdateAssetRequest {
  name?: string;
  description?: string;
  category?: AssetCategory;
  type?: AssetType;
  status?: AssetStatus;
  condition?: AssetCondition;
  location_id?: string;
  assigned_to?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  mac_address?: string;
  ip_address?: string;
  purchase_date?: Date;
  purchase_price?: number;
  warranty_expiry?: Date;
  specifications?: Record<string, any>;
  tags?: string[];
  custom_fields?: Record<string, any>;
}

export interface AssetListResponse {
  assets: Asset[];
  total: number;
  page: number;
  per_page: number;
}

export interface CreateMaintenanceScheduleRequest {
  asset_id: string;
  maintenance_type: MaintenanceType;
  frequency: MaintenanceFrequency;
  frequency_value: number;
  next_due_date: Date;
  estimated_duration: number;
  estimated_cost?: number;
  assigned_to?: string;
  priority: MaintenancePriority;
  description: string;
  checklist_items: Omit<MaintenanceChecklistItem, 'id'>[];
  parts_required?: string[]; // Part IDs
}

export interface CreateMaintenanceRecordRequest {
  asset_id: string;
  schedule_id?: string;
  maintenance_type: MaintenanceType;
  performed_date: Date;
  performed_by: string;
  duration_minutes: number;
  actual_cost?: number;
  description: string;
  work_performed: string;
  parts_used?: { part_id: string; quantity: number }[];
  checklist_completed?: Omit<MaintenanceChecklistCompletion, 'completed_by' | 'completed_at'>[];
  next_maintenance_date?: Date;
  issues_found?: string;
}

export interface LocationListResponse {
  locations: Location[];
  total: number;
}

export interface AssetHistoryResponse {
  history: AssetHistory[];
  total: number;
  page: number;
  per_page: number;
}

// Component Props Types
export interface AssetListProps {
  assets?: Asset[];
  loading?: boolean;
  onAssetSelect?: (asset: Asset) => void;
  onAssetEdit?: (asset: Asset) => void;
  onAssetDelete?: (assetId: string) => void;
  onRefresh?: () => void;
}

export interface AssetDetailProps {
  asset: Asset;
  onEdit?: () => void;
  onDelete?: () => void;
}

export interface MaintenanceScheduleListProps {
  schedules?: MaintenanceSchedule[];
  loading?: boolean;
  onScheduleEdit?: (schedule: MaintenanceSchedule) => void;
  onScheduleDelete?: (scheduleId: string) => void;
  onCreateRecord?: (schedule: MaintenanceSchedule) => void;
}

export interface InventoryListProps {
  items?: InventoryItem[];
  loading?: boolean;
  onItemSelect?: (item: InventoryItem) => void;
  onItemEdit?: (item: InventoryItem) => void;
}

export interface AssetMetricsProps {
  timeRange?: TimeRange;
  category?: AssetCategory;
  location?: string;
}

export interface TimeRange {
  start: Date;
  end: Date;
}

// Search and Filter Types
export interface AssetSearchFilters {
  category?: AssetCategory;
  type?: AssetType;
  status?: AssetStatus;
  condition?: AssetCondition;
  location_id?: string;
  assigned_to?: string;
  manufacturer?: string;
  tags?: string[];
  purchase_date_from?: Date;
  purchase_date_to?: Date;
  warranty_expiry_from?: Date;
  warranty_expiry_to?: Date;
}

export interface MaintenanceSearchFilters {
  asset_id?: string;
  maintenance_type?: MaintenanceType;
  status?: MaintenanceStatus;
  priority?: MaintenancePriority;
  assigned_to?: string;
  due_date_from?: Date;
  due_date_to?: Date;
}

// Configuration Types
export interface AssetsConfig {
  api_endpoint: string;
  enable_barcode_scanning: boolean;
  enable_qr_codes: boolean;
  auto_generate_asset_numbers: boolean;
  asset_number_format: string;
  default_depreciation_method: DepreciationMethod;
  maintenance_reminder_days: number;
  warranty_reminder_days: number;
  enable_location_tracking: boolean;
  enable_photo_attachments: boolean;
  max_attachment_size_mb: number;
  supported_file_types: string[];
}
