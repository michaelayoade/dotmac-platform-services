'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Plug,
  Plus,
  Settings,
  MoreHorizontal,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Trash2,
  ExternalLink,
  Key,
  Link,
  Unlink,
  Play,
  Pause,
  Info,
  Code,
  Database,
  MessageSquare,
  Mail,
  Calendar,
  FileText,
  CreditCard,
  Shield,
  Cloud,
  Github,
  Chrome,
  Zap,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

// Migrated from sonner to useToast hook
// Note: toast options have changed:
// - sonner: toast.success('msg') -> useToast: toast({ title: 'Success', description: 'msg' })
// - sonner: toast.error('msg') -> useToast: toast({ title: 'Error', description: 'msg', variant: 'destructive' })
// - For complex options, refer to useToast documentation

interface Integration {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: React.ForwardRefExoticComponent<Omit<import('lucide-react').LucideProps, "ref"> & React.RefAttributes<SVGSVGElement>>;
  status?: string;
  connectedAt?: string;
  lastSync?: string;
  error?: string;
  config?: Record<string, unknown>;
  popularity?: string;
}

// Mock integrations data
const mockIntegrations = {
  connected: [
    {
      id: '1',
      name: 'GitHub',
      description: 'Source code management and collaboration',
      category: 'Development',
      icon: Github,
      status: 'active',
      connectedAt: '2024-01-15T10:00:00Z',
      lastSync: '2024-01-20T15:30:00Z',
      config: {
        organization: 'acme-corp',
        repositories: 12,
        webhooks: ['push', 'pull_request', 'issues'],
      },
    },
    {
      id: '2',
      name: 'Slack',
      description: 'Team communication and collaboration',
      category: 'Communication',
      icon: MessageSquare,
      status: 'active',
      connectedAt: '2024-01-10T10:00:00Z',
      lastSync: '2024-01-20T14:00:00Z',
      config: {
        workspace: 'acme-team',
        channels: ['#general', '#dev', '#alerts'],
      },
    },
    {
      id: '3',
      name: 'Stripe',
      description: 'Payment processing and billing',
      category: 'Finance',
      icon: CreditCard,
      status: 'error',
      connectedAt: '2023-12-01T10:00:00Z',
      lastSync: '2024-01-19T10:00:00Z',
      error: 'Invalid API key',
      config: {
        mode: 'live',
        webhookEndpoint: 'https://api.example.com/stripe/webhook',
      },
    },
  ],
  available: [
    {
      id: '4',
      name: 'Google Calendar',
      description: 'Calendar and scheduling integration',
      category: 'Productivity',
      icon: Calendar,
      popularity: 'popular',
    },
    {
      id: '5',
      name: 'SendGrid',
      description: 'Email delivery service',
      category: 'Communication',
      icon: Mail,
      popularity: 'popular',
    },
    {
      id: '6',
      name: 'AWS S3',
      description: 'Cloud storage service',
      category: 'Infrastructure',
      icon: Cloud,
      popularity: 'popular',
    },
    {
      id: '7',
      name: 'Jira',
      description: 'Issue tracking and project management',
      category: 'Development',
      icon: FileText,
    },
    {
      id: '8',
      name: 'PostgreSQL',
      description: 'Relational database',
      category: 'Database',
      icon: Database,
    },
    {
      id: '9',
      name: 'Auth0',
      description: 'Authentication and authorization',
      category: 'Security',
      icon: Shield,
    },
  ],
};

// Mock webhooks data
const mockWebhooks = [
  {
    id: '1',
    url: 'https://api.example.com/webhooks/user-events',
    events: ['user.created', 'user.updated', 'user.deleted'],
    status: 'active',
    createdAt: '2024-01-15T10:00:00Z',
    lastTriggered: '2024-01-20T14:30:00Z',
    successRate: 98.5,
  },
  {
    id: '2',
    url: 'https://api.example.com/webhooks/billing',
    events: ['payment.succeeded', 'payment.failed', 'subscription.updated'],
    status: 'active',
    createdAt: '2024-01-10T10:00:00Z',
    lastTriggered: '2024-01-20T10:00:00Z',
    successRate: 100,
  },
  {
    id: '3',
    url: 'https://api.example.com/webhooks/system',
    events: ['system.error', 'system.warning'],
    status: 'paused',
    createdAt: '2024-01-05T10:00:00Z',
    lastTriggered: '2024-01-18T10:00:00Z',
    successRate: 85.2,
  },
];

// Mock API keys
const mockApiKeys = [
  {
    id: '1',
    name: 'Production API Key',
    key: 'sk_live_...abc123',
    createdAt: '2024-01-15T10:00:00Z',
    lastUsed: '2024-01-20T15:30:00Z',
    permissions: ['read', 'write'],
  },
  {
    id: '2',
    name: 'Development API Key',
    key: 'sk_test_...def456',
    createdAt: '2024-01-10T10:00:00Z',
    lastUsed: '2024-01-20T10:00:00Z',
    permissions: ['read'],
  },
];

export default function IntegrationsPage() {
  const { toast } = useToast();

  const [connectedIntegrations, setConnectedIntegrations] = useState<Integration[]>(mockIntegrations.connected);
  const [availableIntegrations] = useState<Integration[]>(mockIntegrations.available);
  const [webhooks, setWebhooks] = useState(mockWebhooks);
  const [apiKeys, setApiKeys] = useState(mockApiKeys);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [isConfigureOpen, setIsConfigureOpen] = useState(false);
  const [isConnectOpen, setIsConnectOpen] = useState(false);
  const [isWebhookOpen, setIsWebhookOpen] = useState(false);
  const [isApiKeyOpen, setIsApiKeyOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // New webhook form state
  const [newWebhook, setNewWebhook] = useState({
    url: '',
    events: [] as string[],
  });

  // New API key form state
  const [newApiKey, setNewApiKey] = useState({
    name: '',
    permissions: ['read'],
  });

  const handleConnect = (integration: Integration) => {
    setSelectedIntegration(integration);
    setIsConnectOpen(true);
  };

  const handleCompleteConnection = () => {
    if (!selectedIntegration) return;

    const newConnection: Integration = {
      ...selectedIntegration,
      status: 'active',
      connectedAt: new Date().toISOString(),
      lastSync: new Date().toISOString(),
      config: {},
      error: undefined,
    };

    setConnectedIntegrations([...connectedIntegrations, newConnection]);
    setIsConnectOpen(false);
    toast({ title: 'Success', description: `Connected to ${selectedIntegration.name}` });
  };

  const handleDisconnect = (integrationId: string) => {
    const integration = connectedIntegrations.find(i => i.id === integrationId);
    setConnectedIntegrations(connectedIntegrations.filter(i => i.id !== integrationId));
    toast({ title: 'Success', description: `Disconnected from ${integration?.name}` });
  };

  const handleRefreshConnection = (integrationId: string) => {
    const integration = connectedIntegrations.find(i => i.id === integrationId);
    setConnectedIntegrations(connectedIntegrations.map(i =>
      i.id === integrationId
        ? { ...i, lastSync: new Date().toISOString(), status: 'active', error: undefined }
        : i
    ));
    toast({ title: 'Success', description: `Refreshed connection to ${integration?.name}` });
  };

  const handleCreateWebhook = () => {
    const webhook = {
      id: Date.now().toString(),
      url: newWebhook.url,
      events: newWebhook.events,
      status: 'active',
      createdAt: new Date().toISOString(),
      lastTriggered: null,
      successRate: 100,
    };

    setWebhooks([...webhooks, webhook]);
    setIsWebhookOpen(false);
    setNewWebhook({ url: '', events: [] });
    toast({ title: 'Success', description: 'Webhook created successfully' });
  };

  const handleToggleWebhook = (webhookId: string) => {
    setWebhooks(webhooks.map(w =>
      w.id === webhookId
        ? { ...w, status: w.status === 'active' ? 'paused' : 'active' }
        : w
    ));
    const webhook = webhooks.find(w => w.id === webhookId);
    toast({ title: 'Success', description: `Webhook ${webhook?.status === 'active' ? 'paused' : 'activated'}` });
  };

  const handleDeleteWebhook = (webhookId: string) => {
    setWebhooks(webhooks.filter(w => w.id !== webhookId));
    toast({ title: 'Success', description: 'Webhook deleted' });
  };

  const handleCreateApiKey = () => {
    const apiKey = {
      id: Date.now().toString(),
      name: newApiKey.name,
      key: `sk_${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date().toISOString(),
      lastUsed: null,
      permissions: newApiKey.permissions,
    };

    setApiKeys([...apiKeys, apiKey]);
    setIsApiKeyOpen(false);
    setNewApiKey({ name: '', permissions: ['read'] });
    toast({ title: 'Success', description: 'API key created successfully' });
  };

  const handleDeleteApiKey = (keyId: string) => {
    setApiKeys(apiKeys.filter(k => k.id !== keyId));
    toast({ title: 'Success', description: 'API key deleted' });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-green-500">Active</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      case 'paused':
        return <Badge variant="secondary">Paused</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Development': return <Code className="h-4 w-4" />;
      case 'Communication': return <MessageSquare className="h-4 w-4" />;
      case 'Finance': return <CreditCard className="h-4 w-4" />;
      case 'Database': return <Database className="h-4 w-4" />;
      case 'Security': return <Shield className="h-4 w-4" />;
      case 'Infrastructure': return <Cloud className="h-4 w-4" />;
      default: return <Plug className="h-4 w-4" />;
    }
  };

  // Filter available integrations
  const filteredIntegrations = availableIntegrations.filter(integration =>
    integration.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    integration.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Integrations</h1>
        <p className="text-gray-500 mt-2">Connect your favorite tools and services</p>
      </div>

      <Tabs defaultValue="connected" className="space-y-4">
        <TabsList>
          <TabsTrigger value="connected">Connected</TabsTrigger>
          <TabsTrigger value="available">Available</TabsTrigger>
          <TabsTrigger value="webhooks">Webhooks</TabsTrigger>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
        </TabsList>

        {/* Connected Tab */}
        <TabsContent value="connected" className="space-y-4">
          {connectedIntegrations.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <Plug className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">No integrations connected yet</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => (document.querySelector('[value="available"]') as HTMLElement)?.click()}
                >
                  Browse Integrations
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {connectedIntegrations.map((integration) => {
                const Icon = integration.icon;
                return (
                  <Card key={integration.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-gray-100 rounded-lg">
                            <Icon className="h-5 w-5" />
                          </div>
                          <div>
                            <CardTitle className="text-base">{integration.name}</CardTitle>
                            <CardDescription className="text-xs mt-1">
                              {integration.description}
                            </CardDescription>
                          </div>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem
                              onClick={() => {
                                setSelectedIntegration(integration);
                                setIsConfigureOpen(true);
                              }}
                            >
                              <Settings className="h-4 w-4 mr-2" />
                              Configure
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleRefreshConnection(integration.id)}
                            >
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Refresh
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDisconnect(integration.id)}
                              className="text-red-600"
                            >
                              <Unlink className="h-4 w-4 mr-2" />
                              Disconnect
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">Status</span>
                        {getStatusBadge(integration.status)}
                      </div>
                      {integration.error && (
                        <div className="flex items-start gap-2 p-2 bg-red-50 rounded-md">
                          <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                          <p className="text-xs text-red-800">{integration.error}</p>
                        </div>
                      )}
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">Connected</span>
                        <span className="text-sm">
                          {new Date(integration.connectedAt).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">Last Sync</span>
                        <span className="text-sm">
                          {new Date(integration.lastSync).toLocaleString()}
                        </span>
                      </div>
                      {integration.config && Object.keys(integration.config).length > 0 && (
                        <div className="pt-2 border-t">
                          {Object.entries(integration.config).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between text-xs">
                              <span className="text-gray-500 capitalize">{key}:</span>
                              <span className="font-mono">
                                {Array.isArray(value) ? value.length : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Available Tab */}
        <TabsContent value="available" className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="relative flex-1 max-w-sm">
              <Input
                placeholder="Search integrations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
              <Plug className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {filteredIntegrations.map((integration) => {
              const Icon = integration.icon;
              const isConnected = connectedIntegrations.some(c => c.name === integration.name);

              return (
                <Card key={integration.id} className={isConnected ? 'opacity-50' : ''}>
                  <CardHeader>
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-gray-100 rounded-lg">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base">{integration.name}</CardTitle>
                          {integration.popularity === 'popular' && (
                            <Badge variant="outline" className="text-xs">Popular</Badge>
                          )}
                        </div>
                        <CardDescription className="text-xs mt-1">
                          {integration.description}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(integration.category)}
                        <span className="text-xs text-gray-500">{integration.category}</span>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleConnect(integration)}
                        disabled={isConnected}
                      >
                        {isConnected ? (
                          <>
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Connected
                          </>
                        ) : (
                          <>
                            <Link className="h-3 w-3 mr-1" />
                            Connect
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Webhooks Tab */}
        <TabsContent value="webhooks" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Webhooks</CardTitle>
                  <CardDescription>Manage webhook endpoints for real-time events</CardDescription>
                </div>
                <Button onClick={() => setIsWebhookOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Webhook
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {webhooks.length === 0 ? (
                <div className="text-center py-8">
                  <Zap className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-500">No webhooks configured</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Endpoint URL</TableHead>
                      <TableHead>Events</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Success Rate</TableHead>
                      <TableHead>Last Triggered</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {webhooks.map((webhook) => (
                      <TableRow key={webhook.id}>
                        <TableCell className="font-mono text-sm">
                          {webhook.url}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1 flex-wrap">
                            {webhook.events.slice(0, 2).map((event, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {event}
                              </Badge>
                            ))}
                            {webhook.events.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{webhook.events.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {webhook.status === 'active' ? (
                            <Badge variant="default" className="bg-green-500">Active</Badge>
                          ) : (
                            <Badge variant="secondary">Paused</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="text-sm">{webhook.successRate}%</span>
                            {webhook.successRate < 90 && (
                              <AlertCircle className="h-4 w-4 text-yellow-500" />
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {webhook.lastTriggered
                            ? new Date(webhook.lastTriggered).toLocaleString()
                            : 'Never'}
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent>
                              <DropdownMenuItem onClick={() => handleToggleWebhook(webhook.id)}>
                                {webhook.status === 'active' ? (
                                  <>
                                    <Pause className="h-4 w-4 mr-2" />
                                    Pause
                                  </>
                                ) : (
                                  <>
                                    <Play className="h-4 w-4 mr-2" />
                                    Activate
                                  </>
                                )}
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <RefreshCw className="h-4 w-4 mr-2" />
                                Test Webhook
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleDeleteWebhook(webhook.id)}
                                className="text-red-600"
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
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>API Keys</CardTitle>
                  <CardDescription>Manage API keys for programmatic access</CardDescription>
                </div>
                <Button onClick={() => setIsApiKeyOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create API Key
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {apiKeys.length === 0 ? (
                <div className="text-center py-8">
                  <Key className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-gray-500">No API keys created</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Key</TableHead>
                      <TableHead>Permissions</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Last Used</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {apiKeys.map((apiKey) => (
                      <TableRow key={apiKey.id}>
                        <TableCell className="font-medium">{apiKey.name}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                              {apiKey.key}
                            </code>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                navigator.clipboard.writeText(apiKey.key);
                                toast({ title: 'Success', description: 'API key copied to clipboard' });
                              }}
                            >
                              Copy
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            {apiKey.permissions.map((perm, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {perm}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>{new Date(apiKey.createdAt).toLocaleDateString()}</TableCell>
                        <TableCell>
                          {apiKey.lastUsed
                            ? new Date(apiKey.lastUsed).toLocaleString()
                            : 'Never'}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteApiKey(apiKey.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Configure Integration Dialog */}
      <Dialog open={isConfigureOpen} onOpenChange={setIsConfigureOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Configure {selectedIntegration?.name}</DialogTitle>
            <DialogDescription>
              Update integration settings and configuration
            </DialogDescription>
          </DialogHeader>
          {selectedIntegration && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Integration Status</Label>
                <div className="flex items-center gap-2">
                  {getStatusBadge(selectedIntegration.status)}
                  {selectedIntegration.error && (
                    <span className="text-sm text-red-600">{selectedIntegration.error}</span>
                  )}
                </div>
              </div>
              <Separator />
              <div className="space-y-2">
                <Label>Configuration</Label>
                <div className="text-sm text-gray-500">
                  Integration-specific configuration would appear here
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsConfigureOpen(false)}>
              Close
            </Button>
            <Button onClick={() => {
              handleRefreshConnection(selectedIntegration?.id);
              setIsConfigureOpen(false);
            }}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Connect Integration Dialog */}
      <Dialog open={isConnectOpen} onOpenChange={setIsConnectOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Connect to {selectedIntegration?.name}</DialogTitle>
            <DialogDescription>
              Authorize and configure the integration
            </DialogDescription>
          </DialogHeader>
          {selectedIntegration && (
            <div className="space-y-4 py-4">
              <div className="text-center py-8 border-2 border-dashed rounded-lg">
                <selectedIntegration.icon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-sm text-gray-500">
                  Click the button below to authorize with {selectedIntegration.name}
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsConnectOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCompleteConnection}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Authorize & Connect
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Webhook Dialog */}
      <Dialog open={isWebhookOpen} onOpenChange={setIsWebhookOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Webhook</DialogTitle>
            <DialogDescription>
              Configure a new webhook endpoint
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="webhook-url">Endpoint URL</Label>
              <Input
                id="webhook-url"
                value={newWebhook.url}
                onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                placeholder="https://api.example.com/webhooks"
              />
            </div>
            <div className="space-y-2">
              <Label>Events</Label>
              <div className="space-y-2">
                {['user.created', 'user.updated', 'payment.succeeded', 'system.error'].map(event => (
                  <div key={event} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={event}
                      checked={newWebhook.events.includes(event)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewWebhook({
                            ...newWebhook,
                            events: [...newWebhook.events, event],
                          });
                        } else {
                          setNewWebhook({
                            ...newWebhook,
                            events: newWebhook.events.filter(e => e !== event),
                          });
                        }
                      }}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={event} className="text-sm font-normal">
                      {event}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsWebhookOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateWebhook}
              disabled={!newWebhook.url || newWebhook.events.length === 0}
            >
              Create Webhook
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create API Key Dialog */}
      <Dialog open={isApiKeyOpen} onOpenChange={setIsApiKeyOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create API Key</DialogTitle>
            <DialogDescription>
              Generate a new API key for programmatic access
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="key-name">Key Name</Label>
              <Input
                id="key-name"
                value={newApiKey.name}
                onChange={(e) => setNewApiKey({ ...newApiKey, name: e.target.value })}
                placeholder="e.g., Production API Key"
              />
            </div>
            <div className="space-y-2">
              <Label>Permissions</Label>
              <div className="space-y-2">
                {['read', 'write', 'delete'].map(permission => (
                  <div key={permission} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={permission}
                      checked={newApiKey.permissions.includes(permission)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewApiKey({
                            ...newApiKey,
                            permissions: [...newApiKey.permissions, permission],
                          });
                        } else {
                          setNewApiKey({
                            ...newApiKey,
                            permissions: newApiKey.permissions.filter(p => p !== permission),
                          });
                        }
                      }}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={permission} className="text-sm font-normal capitalize">
                      {permission}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsApiKeyOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateApiKey}
              disabled={!newApiKey.name || newApiKey.permissions.length === 0}
            >
              Create API Key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}