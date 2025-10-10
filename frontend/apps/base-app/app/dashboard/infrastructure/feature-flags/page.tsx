'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

interface FeatureFlag {
  id: string;
  name: string;
  displayName: string;
  description: string;
  enabled: boolean;
  type: string;
  environment: string;
  targeting: string;
  segment?: string;
  rolloutPercentage: number;
  createdAt: string;
  updatedAt: string;
  lastModifiedBy: string;
  tags: string[];
}
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ToggleLeft,
  ToggleRight,
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2,
  Copy,
  History,
  Users,
  Percent,
  Calendar,
  AlertCircle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Code,
  Globe,
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { useFeatureFlags } from '@/hooks/useFeatureFlags';

// Mock feature flags data
const mockFeatureFlags = [
  {
    id: '1',
    name: 'new-dashboard-ui',
    displayName: 'New Dashboard UI',
    description: 'Enable the redesigned dashboard interface',
    enabled: true,
    type: 'boolean',
    environment: 'production',
    targeting: 'all',
    rolloutPercentage: 100,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-20T15:30:00Z',
    lastModifiedBy: 'admin@example.com',
    tags: ['frontend', 'ui'],
  },
  {
    id: '2',
    name: 'advanced-analytics',
    displayName: 'Advanced Analytics',
    description: 'Enable advanced analytics features for premium users',
    enabled: true,
    type: 'boolean',
    environment: 'production',
    targeting: 'segment',
    segment: 'premium_users',
    rolloutPercentage: 100,
    createdAt: '2024-01-10T10:00:00Z',
    updatedAt: '2024-01-18T10:00:00Z',
    lastModifiedBy: 'product@example.com',
    tags: ['analytics', 'premium'],
  },
  {
    id: '3',
    name: 'api-rate-limit',
    displayName: 'API Rate Limiting',
    description: 'Configure API rate limits per user tier',
    enabled: true,
    type: 'number',
    value: 1000,
    environment: 'production',
    targeting: 'all',
    createdAt: '2024-01-05T10:00:00Z',
    updatedAt: '2024-01-05T10:00:00Z',
    lastModifiedBy: 'engineering@example.com',
    tags: ['api', 'performance'],
  },
  {
    id: '4',
    name: 'beta-features',
    displayName: 'Beta Features',
    description: 'Enable beta features for testing',
    enabled: false,
    type: 'boolean',
    environment: 'staging',
    targeting: 'percentage',
    rolloutPercentage: 25,
    createdAt: '2024-01-20T10:00:00Z',
    updatedAt: '2024-01-22T10:00:00Z',
    lastModifiedBy: 'qa@example.com',
    tags: ['beta', 'experimental'],
  },
  {
    id: '5',
    name: 'maintenance-mode',
    displayName: 'Maintenance Mode',
    description: 'Enable maintenance mode for the application',
    enabled: false,
    type: 'boolean',
    environment: 'production',
    targeting: 'all',
    createdAt: '2024-01-01T10:00:00Z',
    updatedAt: '2024-01-01T10:00:00Z',
    lastModifiedBy: 'ops@example.com',
    tags: ['system', 'maintenance'],
  },
];

// Mock audit history
const mockAuditHistory = [
  {
    id: '1',
    flagName: 'new-dashboard-ui',
    action: 'enabled',
    user: 'admin@example.com',
    timestamp: '2024-01-20T15:30:00Z',
    oldValue: false,
    newValue: true,
  },
  {
    id: '2',
    flagName: 'beta-features',
    action: 'rollout_changed',
    user: 'qa@example.com',
    timestamp: '2024-01-22T10:00:00Z',
    oldValue: 10,
    newValue: 25,
  },
  {
    id: '3',
    flagName: 'api-rate-limit',
    action: 'value_changed',
    user: 'engineering@example.com',
    timestamp: '2024-01-05T10:00:00Z',
    oldValue: 500,
    newValue: 1000,
  },
];

export default function FeatureFlagsPage() {
  const { flags: backendFlags, status, loading, error, toggleFlag, deleteFlag: deleteBackendFlag, refreshFlags } = useFeatureFlags();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterEnvironment, setFilterEnvironment] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedFlag, setSelectedFlag] = useState<FeatureFlag | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Map backend flags to display format
  const flags: FeatureFlag[] = backendFlags.map(flag => ({
    id: flag.name,
    name: flag.name,
    displayName: flag.name.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    description: flag.description || 'No description provided',
    enabled: flag.enabled,
    type: 'boolean',
    environment: 'production',
    targeting: 'all',
    segment: undefined,
    rolloutPercentage: flag.enabled ? 100 : 0,
    createdAt: flag.created_at ? new Date(flag.created_at * 1000).toISOString() : new Date().toISOString(),
    updatedAt: new Date(flag.updated_at * 1000).toISOString(),
    lastModifiedBy: 'system',
    tags: Object.keys(flag.context || {}),
  }));

  // New flag form state
  const [newFlag, setNewFlag] = useState({
    name: '',
    displayName: '',
    description: '',
    type: 'boolean',
    enabled: false,
    environment: 'staging',
    targeting: 'all',
    rolloutPercentage: 100,
    tags: '',
  });

  // Filter flags
  const filteredFlags = flags.filter(flag => {
    const matchesSearch = flag.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         flag.displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         flag.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesEnvironment = filterEnvironment === 'all' || flag.environment === filterEnvironment;
    const matchesStatus = filterStatus === 'all' ||
                         (filterStatus === 'enabled' && flag.enabled) ||
                         (filterStatus === 'disabled' && !flag.enabled);
    return matchesSearch && matchesEnvironment && matchesStatus;
  });

  const handleToggleFlag = async (flagId: string) => {
    const flag = flags.find(f => f.id === flagId);
    if (!flag) return;

    try {
      await toggleFlag(flagId, !flag.enabled);
      toast.success(`Feature flag "${flag.displayName}" ${flag.enabled ? 'disabled' : 'enabled'}`);
    } catch (err) {
      toast.error(`Failed to toggle feature flag`);
    }
  };

  const handleCreateFlag = () => {
    const flag = {
      id: Date.now().toString(),
      name: newFlag.name,
      displayName: newFlag.displayName,
      description: newFlag.description,
      type: newFlag.type,
      enabled: newFlag.enabled,
      environment: newFlag.environment,
      targeting: newFlag.targeting,
      rolloutPercentage: newFlag.rolloutPercentage,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastModifiedBy: 'current@user.com',
      tags: newFlag.tags.split(',').map(t => t.trim()).filter(Boolean),
    };

    // Flag creation would happen via API call here
    // Refresh flags to get updated list
    refreshFlags();
    setIsCreateOpen(false);
    setNewFlag({
      name: '',
      displayName: '',
      description: '',
      type: 'boolean',
      enabled: false,
      environment: 'staging',
      targeting: 'all',
      rolloutPercentage: 100,
      tags: '',
    });
    toast.success('Feature flag created successfully');
  };

  const handleUpdateFlag = () => {
    if (!selectedFlag) return;

    // Flag update would happen via API call here
    // Refresh flags to get updated list
    refreshFlags();
    setIsEditOpen(false);
    toast.success('Feature flag updated successfully');
  };

  const handleDeleteFlag = async () => {
    if (!selectedFlag) return;

    try {
      await deleteBackendFlag(selectedFlag.id);
      setIsDeleteOpen(false);
      setSelectedFlag(null);
      toast.success('Feature flag deleted successfully');
    } catch (err) {
      toast.error('Failed to delete feature flag');
    }
  };

  const handleDuplicateFlag = (flag: FeatureFlag) => {
    const duplicated = {
      ...flag,
      id: Date.now().toString(),
      name: `${flag.name}-copy`,
      displayName: `${flag.displayName} (Copy)`,
      enabled: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // Flag duplication would happen via API call here
    // Refresh flags to get updated list
    refreshFlags();
    toast.success('Feature flag duplicated successfully');
  };

  const getEnvironmentBadge = (env: string) => {
    switch (env) {
      case 'production':
        return <Badge variant="destructive">{env}</Badge>;
      case 'staging':
        return <Badge variant="secondary">{env}</Badge>;
      case 'development':
        return <Badge variant="outline">{env}</Badge>;
      default:
        return <Badge variant="outline">{env}</Badge>;
    }
  };

  const getTargetingIcon = (targeting: string) => {
    switch (targeting) {
      case 'all':
        return <Globe className="h-4 w-4" />;
      case 'segment':
        return <Users className="h-4 w-4" />;
      case 'percentage':
        return <Percent className="h-4 w-4" />;
      default:
        return <Globe className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Feature Flags</h1>
          <p className="text-muted-foreground mt-2">Manage feature toggles and rollouts</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Flag
        </Button>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Feature Flag</DialogTitle>
              <DialogDescription>
                Define a new feature flag for controlled rollouts
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="flag-name">Flag Name</Label>
                  <Input
                    id="flag-name"
                    value={newFlag.name}
                    onChange={(e) => setNewFlag({ ...newFlag, name: e.target.value })}
                    placeholder="e.g., new-feature"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="flag-display-name">Display Name</Label>
                  <Input
                    id="flag-display-name"
                    value={newFlag.displayName}
                    onChange={(e) => setNewFlag({ ...newFlag, displayName: e.target.value })}
                    placeholder="e.g., New Feature"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="flag-description">Description</Label>
                <Textarea
                  id="flag-description"
                  value={newFlag.description}
                  onChange={(e) => setNewFlag({ ...newFlag, description: e.target.value })}
                  placeholder="Describe the purpose of this feature flag"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="flag-type">Type</Label>
                  <select
                    id="flag-type"
                    value={newFlag.type}
                    onChange={(e) => setNewFlag({ ...newFlag, type: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground"
                  >
                    <option value="boolean">Boolean</option>
                    <option value="number">Number</option>
                    <option value="string">String</option>
                    <option value="json">JSON</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="flag-environment">Environment</Label>
                  <select
                    id="flag-environment"
                    value={newFlag.environment}
                    onChange={(e) => setNewFlag({ ...newFlag, environment: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground"
                  >
                    <option value="development">Development</option>
                    <option value="staging">Staging</option>
                    <option value="production">Production</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="flag-targeting">Targeting</Label>
                  <select
                    id="flag-targeting"
                    value={newFlag.targeting}
                    onChange={(e) => setNewFlag({ ...newFlag, targeting: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-foreground"
                  >
                    <option value="all">All Users</option>
                    <option value="segment">User Segment</option>
                    <option value="percentage">Percentage Rollout</option>
                  </select>
                </div>
                {newFlag.targeting === 'percentage' && (
                  <div className="space-y-2">
                    <Label htmlFor="flag-percentage">Rollout Percentage</Label>
                    <Input
                      id="flag-percentage"
                      type="number"
                      min="0"
                      max="100"
                      value={newFlag.rolloutPercentage}
                      onChange={(e) => setNewFlag({ ...newFlag, rolloutPercentage: parseInt(e.target.value) })}
                    />
                  </div>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="flag-tags">Tags (comma-separated)</Label>
                <Input
                  id="flag-tags"
                  value={newFlag.tags}
                  onChange={(e) => setNewFlag({ ...newFlag, tags: e.target.value })}
                  placeholder="e.g., frontend, experimental"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="flag-enabled"
                  checked={newFlag.enabled}
                  onCheckedChange={(checked) => setNewFlag({ ...newFlag, enabled: checked })}
                />
                <Label htmlFor="flag-enabled">Enable immediately</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateFlag} disabled={!newFlag.name || !newFlag.displayName}>
                Create Flag
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Flags</CardTitle>
            <ToggleLeft className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{flags.length}</div>
            <p className="text-xs text-muted-foreground">
              Across all environments
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enabled</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {flags.filter(f => f.enabled).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Currently active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Production</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {flags.filter(f => f.environment === 'production').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Live in production
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rollouts</CardTitle>
            <Percent className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {flags.filter(f => f.targeting === 'percentage' && f.rolloutPercentage < 100).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Gradual deployments
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="flags">
        <TabsList>
          <TabsTrigger value="flags">Feature Flags</TabsTrigger>
          <TabsTrigger value="history">Audit History</TabsTrigger>
          <TabsTrigger value="examples">Code Examples</TabsTrigger>
        </TabsList>

        {/* Flags Tab */}
        <TabsContent value="flags" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>All Flags</CardTitle>
                <div className="flex gap-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search flags..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 w-[250px]"
                    />
                  </div>
                  <select
                    value={filterEnvironment}
                    onChange={(e) => setFilterEnvironment(e.target.value)}
                    className="h-10 w-[150px] rounded-md border border-border bg-card px-3 text-sm text-foreground"
                  >
                    <option value="all">All Environments</option>
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development</option>
                  </select>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="h-10 w-[120px] rounded-md border border-border bg-card px-3 text-sm text-foreground"
                  >
                    <option value="all">All Status</option>
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Flag</TableHead>
                    <TableHead>Environment</TableHead>
                    <TableHead>Targeting</TableHead>
                    <TableHead>Tags</TableHead>
                    <TableHead>Last Updated</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredFlags.map((flag) => (
                    <TableRow key={flag.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{flag.displayName}</div>
                          <div className="text-sm text-muted-foreground">{flag.name}</div>
                          <div className="text-xs text-muted-foreground mt-1">{flag.description}</div>
                        </div>
                      </TableCell>
                      <TableCell>{getEnvironmentBadge(flag.environment)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getTargetingIcon(flag.targeting)}
                          <span className="text-sm">
                            {flag.targeting === 'all' && 'All Users'}
                            {flag.targeting === 'segment' && flag.segment}
                            {flag.targeting === 'percentage' && `${flag.rolloutPercentage}%`}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 flex-wrap">
                          {flag.tags?.map((tag, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {new Date(flag.updatedAt).toLocaleDateString()}
                          <div className="text-xs text-muted-foreground">{flag.lastModifiedBy}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={flag.enabled}
                          onCheckedChange={() => handleToggleFlag(flag.id)}
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger>
                            <Button
                              variant="ghost"
                              className="h-8 w-8 p-0"
                              aria-label={`Open actions for ${flag.name ?? 'feature flag'}`}
                              title={`Open actions for ${flag.name ?? 'feature flag'}`}
                            >
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedFlag(flag);
                                setIsEditOpen(true);
                              }}
                            >
                              <Edit className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDuplicateFlag(flag)}
                            >
                              <Copy className="h-4 w-4 mr-2" />
                              Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedFlag(flag);
                                setIsHistoryOpen(true);
                              }}
                            >
                              <History className="h-4 w-4 mr-2" />
                              View History
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedFlag(flag);
                                setIsDeleteOpen(true);
                              }}
                              className="text-red-600 dark:text-red-400"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Audit History</CardTitle>
              <CardDescription>Recent changes to feature flags</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Flag</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Changes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockAuditHistory.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>
                        {new Date(entry.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell className="font-medium">{entry.flagName}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{entry.action}</Badge>
                      </TableCell>
                      <TableCell>{entry.user}</TableCell>
                      <TableCell>
                        <span className="text-red-600 dark:text-red-400 line-through">{String(entry.oldValue)}</span>
                        {' → '}
                        <span className="text-green-600 dark:text-green-400">{String(entry.newValue)}</span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Code Examples Tab */}
        <TabsContent value="examples" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Implementation Examples</CardTitle>
              <CardDescription>How to use feature flags in your code</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  JavaScript/TypeScript
                </h4>
                <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
{`import { getFeatureFlag } from '@dotmac/feature-flags';

// Check if a feature is enabled
if (await getFeatureFlag('new-dashboard-ui')) {
  // Show new UI
  renderNewDashboard();
} else {
  // Show old UI
  renderLegacyDashboard();
}

// Get flag with default value
const rateLimit = await getFeatureFlag('api-rate-limit', 1000);
console.log(\`Rate limit: \${rateLimit}\`);`}
                </pre>
              </div>

              <div>
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Python
                </h4>
                <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
{`from dotmac.feature_flags import get_flag

# Check boolean flag
if get_flag('new-dashboard-ui'):
    return render_new_dashboard()
else:
    return render_legacy_dashboard()

# Get numeric flag with default
rate_limit = get_flag('api-rate-limit', default=1000)
print(f"Rate limit: {rate_limit}")`}
                </pre>
              </div>

              <div>
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  React Hook
                </h4>
                <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
{`import { useFeatureFlag } from '@dotmac/react-feature-flags';

function MyComponent() {
  const { isEnabled, loading } = useFeatureFlag('new-dashboard-ui');

  if (loading) return <Spinner />;

  return isEnabled ? <NewDashboard /> : <LegacyDashboard />;
}`}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteOpen} onOpenChange={setIsDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Feature Flag</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this feature flag? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {selectedFlag && (
            <div className="py-4">
              <div className="bg-red-100 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-md p-4">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 mr-3" />
                  <div>
                    <p className="text-sm text-red-800 dark:text-red-300">
                      <strong>{selectedFlag.displayName}</strong> will be permanently deleted.
                    </p>
                    <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                      Flag name: {selectedFlag.name}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteFlag}>
              Delete Flag
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
