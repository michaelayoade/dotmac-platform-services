# @dotmac/assets

Comprehensive asset lifecycle management and inventory tracking for ISP operations. This package provides complete asset management capabilities built on DRY patterns and integrated with the DotMac shared services.

## Features

### 🏭 Asset Lifecycle Management

- Complete asset lifecycle tracking from acquisition to disposal
- Depreciation calculations with multiple methods (straight-line, declining balance, units of production)
- Asset transfer and assignment management
- Retirement and disposal workflows
- Comprehensive asset history tracking

### 📊 Inventory Management

- Real-time inventory tracking and stock management
- Barcode and QR code generation/scanning
- Multi-location inventory support
- Parts and supplies management
- Stock level alerts and reorder points

### 🔧 Maintenance Management

- Preventive maintenance scheduling
- Work order management
- Maintenance history tracking
- Cost analysis and reporting
- Maintenance calendar and notifications
- Checklist-based maintenance workflows

### 📍 Asset Tracking

- Location-based asset tracking
- Asset movement history
- Geofencing and alerts
- Assignment tracking (technician/location)
- Real-time asset status monitoring

### 📈 Analytics & Reporting

- Asset utilization metrics
- Maintenance cost analysis
- Depreciation reports
- ROI calculations
- Lifecycle stage analytics

## Installation

```bash
pnpm add @dotmac/assets
```

## Dependencies

This package relies on other DotMac packages:

- `@dotmac/primitives` - Core UI components
- `@dotmac/ui` - Higher-level UI components
- `@dotmac/headless` - Data management and API clients
- `@dotmac/auth` - Authentication and authorization

## Basic Usage

### Asset Management

```tsx
import { AssetList, useAssets } from '@dotmac/assets';

function AssetManagementPage() {
  const { assets, loading, refresh, createAsset } = useAssets();

  const handleCreateAsset = async (data) => {
    await createAsset({
      name: 'New Router',
      category: 'network_equipment',
      type: 'router',
      manufacturer: 'Cisco',
      model: 'ISR4431',
      serial_number: 'ABC123456',
      purchase_price: 2500,
    });
    refresh();
  };

  return (
    <AssetList
      assets={assets}
      loading={loading}
      onRefresh={refresh}
      onAssetSelect={(asset) => console.log('Selected:', asset)}
    />
  );
}
```

### Maintenance Scheduling

```tsx
import { MaintenanceSchedule, useMaintenanceSchedules } from '@dotmac/assets';

function MaintenancePage() {
  const { schedules, createSchedule } = useMaintenanceSchedules();

  const handleScheduleMaintenance = async (assetId: string) => {
    await createSchedule({
      asset_id: assetId,
      maintenance_type: 'preventive',
      frequency: 'monthly',
      frequency_value: 3, // Every 3 months
      next_due_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
      estimated_duration: 120, // 2 hours
      priority: 'medium',
      description: 'Quarterly preventive maintenance',
      checklist_items: [
        { name: 'Check air filters', is_required: true, order: 1 },
        { name: 'Verify connections', is_required: true, order: 2 },
      ],
    });
  };

  return <MaintenanceSchedule schedules={schedules} onCreateRecord={handleScheduleMaintenance} />;
}
```

### Inventory Tracking

```tsx
import { InventoryList, BarcodeScanner, useInventory } from '@dotmac/assets';

function InventoryPage() {
  const { items, updateStock } = useInventory();

  const handleBarcodeScanned = async (barcode: string) => {
    try {
      const asset = await assetsApiClient.scanBarcode(barcode);
      console.log('Asset found:', asset);
    } catch (error) {
      console.error('Asset not found');
    }
  };

  return (
    <div>
      <BarcodeScanner onScan={handleBarcodeScanned} />
      <InventoryList items={items} onItemSelect={(item) => console.log('Selected:', item)} />
    </div>
  );
}
```

### Asset Lifecycle Analytics

```tsx
import { LifecycleDashboard, useAssetMetrics } from '@dotmac/assets';

function AnalyticsPage() {
  const { metrics, loading } = useAssetMetrics();

  return (
    <LifecycleDashboard
      metrics={metrics}
      loading={loading}
      timeRange={{
        start: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000), // 1 year ago
        end: new Date(),
      }}
    />
  );
}
```

## Components

### Asset Management

- `AssetList` - Comprehensive asset listing with filters
- `AssetDetail` - Detailed asset information view
- `AssetForm` - Asset creation and editing forms
- `AssetCard` - Asset summary cards
- `AssetSearch` - Advanced asset search interface
- `AssetHistory` - Asset lifecycle history view

### Lifecycle Management

- `LifecycleDashboard` - Asset lifecycle analytics
- `DepreciationSchedule` - Depreciation tracking and calculations
- `AssetTransfer` - Asset transfer workflows
- `AssetRetirement` - Asset retirement management
- `LifecycleTimeline` - Visual lifecycle timeline

### Maintenance Management

- `MaintenanceSchedule` - Maintenance scheduling interface
- `MaintenanceRecord` - Maintenance record management
- `MaintenanceCalendar` - Calendar view of maintenance activities
- `MaintenanceDashboard` - Maintenance analytics and metrics
- `WorkOrder` - Work order management
- `MaintenanceChecklist` - Checklist-based maintenance workflows

### Inventory Management

- `InventoryList` - Inventory item listing
- `InventoryItem` - Individual inventory item details
- `StockLevels` - Stock level monitoring
- `InventorySearch` - Inventory search and filtering
- `BarcodeScanner` - Barcode scanning component
- `QRCodeGenerator` - QR code generation for assets

### Asset Tracking

- `AssetTracker` - Real-time asset tracking
- `LocationMap` - Visual asset location mapping
- `AssetMovement` - Asset movement tracking
- `GeofenceAlerts` - Location-based alerts
- `TrackingHistory` - Asset location history

## Hooks

### Data Management

- `useAssets` - Asset CRUD operations
- `useAssetHistory` - Asset lifecycle history
- `useMaintenanceSchedules` - Maintenance scheduling
- `useMaintenanceRecords` - Maintenance record management
- `useInventory` - Inventory management
- `useAssetMetrics` - Asset analytics and metrics
- `useAssetTracking` - Real-time asset tracking
- `useDepreciation` - Depreciation calculations

## API Integration

The package includes a comprehensive API client for asset management:

```tsx
import { assetsApiClient } from '@dotmac/assets';

// Asset operations
const assets = await assetsApiClient.getAssets({
  filters: { category: 'network_equipment', status: 'active' },
});

const asset = await assetsApiClient.createAsset({
  name: 'New Switch',
  category: 'network_equipment',
  type: 'switch',
  manufacturer: 'Cisco',
  model: 'Catalyst 9300',
});

// Maintenance operations
const schedules = await assetsApiClient.getMaintenanceSchedules({
  asset_id: asset.id,
});

await assetsApiClient.createMaintenanceRecord({
  asset_id: asset.id,
  maintenance_type: 'preventive',
  performed_date: new Date(),
  performed_by: 'technician-123',
  duration_minutes: 90,
  description: 'Quarterly maintenance completed',
});

// Inventory operations
const inventory = await assetsApiClient.getInventoryItems({
  location_id: 'warehouse-1',
});

// Analytics
const metrics = await assetsApiClient.getAssetMetrics({
  category: 'network_equipment',
  date_from: new Date('2024-01-01'),
  date_to: new Date(),
});
```

## Utility Functions

### Asset Status Helpers

```tsx
import { assetStatusHelpers } from '@dotmac/assets';

const statusColor = assetStatusHelpers.getStatusColor(asset.status);
const needsAttention = assetStatusHelpers.needsAttention(asset);
const assetAge = assetStatusHelpers.getAssetAge(asset);
const warrantyStatus = assetStatusHelpers.getWarrantyStatus(asset);
```

### Lifecycle Helpers

```tsx
import { lifecycleHelpers } from '@dotmac/assets';

const depreciation = lifecycleHelpers.calculateDepreciation(
  25000, // purchase price
  'straight_line',
  5, // useful life years
  2500, // salvage value
  2 // current age in years
);

const stage = lifecycleHelpers.getAssetLifecycleStage(asset);
const shouldReplace = lifecycleHelpers.shouldConsiderReplacement(asset);
```

### Maintenance Helpers

```tsx
import { maintenanceHelpers } from '@dotmac/assets';

const nextDueDate = maintenanceHelpers.calculateNextDueDate(
  'monthly',
  3, // every 3 months
  lastMaintenanceDate
);

const isOverdue = maintenanceHelpers.isMaintenanceOverdue(schedule);
const urgency = maintenanceHelpers.getMaintenanceUrgency(schedule);
const costAnalysis = maintenanceHelpers.calculateMaintenanceCost(records);
```

## Configuration

### Assets Configuration

```tsx
import { AssetsConfig } from '@dotmac/assets';

const config: AssetsConfig = {
  api_endpoint: '/api/assets',
  enable_barcode_scanning: true,
  enable_qr_codes: true,
  auto_generate_asset_numbers: true,
  asset_number_format: 'ASSET-{YYYY}-{0000}',
  default_depreciation_method: 'straight_line',
  maintenance_reminder_days: 7,
  warranty_reminder_days: 30,
  enable_location_tracking: true,
  enable_photo_attachments: true,
  max_attachment_size_mb: 10,
  supported_file_types: ['pdf', 'jpg', 'png', 'doc', 'docx'],
};
```

## Types and Interfaces

Comprehensive TypeScript definitions for all asset management operations:

```tsx
import type {
  Asset,
  AssetCategory,
  AssetStatus,
  AssetCondition,
  MaintenanceSchedule,
  MaintenanceRecord,
  InventoryItem,
  AssetMetrics,
  CreateAssetRequest,
  UpdateAssetRequest,
} from '@dotmac/assets';
```

## Key Features

### Asset Categories

- Network Equipment (routers, switches, firewalls, etc.)
- Customer Premises Equipment
- Infrastructure Assets
- Vehicles and Mobile Assets
- Tools and Equipment
- Office Equipment
- Software Assets

### Maintenance Types

- **Preventive**: Scheduled routine maintenance
- **Corrective**: Repair-based maintenance
- **Predictive**: Data-driven maintenance
- **Condition-based**: Condition-triggered maintenance
- **Calibration**: Precision instrument calibration
- **Inspection**: Regular safety/compliance inspections

### Depreciation Methods

- **Straight Line**: Equal annual depreciation
- **Declining Balance**: Accelerated depreciation
- **Units of Production**: Usage-based depreciation

### Location Tracking

- Hierarchical location structure
- GPS coordinate support
- Asset movement history
- Geofencing capabilities

## Integration with ISP Operations

This package integrates seamlessly with ISP-specific workflows:

- **Network Equipment Tracking**: Specialized support for routers, switches, ONTs, OLTs
- **Field Operations**: Mobile-friendly interfaces for technicians
- **Customer Premise Equipment**: CPE lifecycle management
- **Infrastructure Assets**: Tower, cable, and facility management
- **Compliance Reporting**: Regulatory compliance tracking

## Real-time Features

- Live asset status updates
- Maintenance notifications
- Inventory alerts
- Location tracking
- Mobile barcode scanning

## Analytics and Reporting

- Asset utilization reports
- Maintenance cost analysis
- Depreciation schedules
- ROI calculations
- Compliance reports
- Predictive maintenance insights

## License

MIT - See LICENSE file for details.

## Contributing

Please refer to the main DotMac Framework contributing guidelines.
