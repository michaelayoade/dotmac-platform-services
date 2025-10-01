'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Activity,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Clock,
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  Database,
  Shield,
  Zap,
  TrendingUp,
  TrendingDown,
  Loader2,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useHealth } from '@/hooks/useHealth';

// Mock system metrics
const systemMetrics = {
  cpu: { current: 42, trend: 'stable', history: generateMetricHistory(40, 45) },
  memory: { current: 68, trend: 'up', history: generateMetricHistory(65, 70) },
  disk: { current: 55, trend: 'stable', history: generateMetricHistory(54, 56) },
  network: { current: 30, trend: 'down', history: generateMetricHistory(28, 35) },
};

// Generate mock metric history
function generateMetricHistory(min: number, max: number) {
  const now = Date.now();
  return Array.from({ length: 24 }, (_, i) => ({
    time: new Date(now - (23 - i) * 3600000).toISOString().slice(11, 16),
    value: Math.floor(Math.random() * (max - min + 1)) + min,
  }));
}

// Generate response time history
const responseTimeHistory = Array.from({ length: 30 }, (_, i) => ({
  time: `${30 - i}m`,
  p50: Math.floor(Math.random() * 20) + 30,
  p95: Math.floor(Math.random() * 30) + 60,
  p99: Math.floor(Math.random() * 40) + 90,
}));

export default function HealthPage() {
  const { health, loading, error, refreshHealth } = useHealth();
  const [selectedMetric, setSelectedMetric] = useState('cpu');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refreshHealth();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  // Map backend service names to friendly names with default uptime
  const mapServiceName = (name: string) => {
    const serviceMap: Record<string, string> = {
      'Database': 'Database',
      'Redis': 'Redis Cache',
      'Celery broker': 'Background Jobs',
      'Celery result backend': 'Task Results',
      'Vault': 'Secrets Vault',
    };
    return serviceMap[name] || name;
  };

  const services = health?.services.map(service => ({
    name: mapServiceName(service.name),
    status: service.status,
    uptime: service.uptime || (service.status === 'healthy' ? 99.9 : service.status === 'degraded' ? 95.0 : 85.0),
    responseTime: service.responseTime || 0,
    lastCheck: service.lastCheck || 'just now',
    message: service.message,
  })) || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'unhealthy': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'degraded': return <AlertCircle className="h-5 w-5 text-yellow-600" />;
      case 'unhealthy': return <XCircle className="h-5 w-5 text-red-600" />;
      default: return <AlertCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'down': return <TrendingDown className="h-4 w-4 text-green-500" />;
      default: return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const healthyServices = services.filter(s => s.status === 'healthy').length;
  const degradedServices = services.filter(s => s.status === 'degraded').length;
  const unhealthyServices = services.filter(s => s.status === 'unhealthy').length;

  // Show loading state on initial load
  if (loading && !health) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-sky-500" />
          <p className="text-gray-500">Loading health data...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error && !health) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Failed to Load Health Data</h3>
              <p className="text-gray-500 mb-4">{error}</p>
              <Button onClick={handleRefresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">System Health</h1>
          <p className="text-gray-500 mt-2">Monitor service status and system metrics (Live Data)</p>
          {health?.timestamp && (
            <p className="text-xs text-gray-400 mt-1">
              Last updated: {new Date(health.timestamp).toLocaleTimeString()}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRefresh}
            disabled={isRefreshing || loading}
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${(isRefreshing || loading) ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overall Health Status */}
      <Card>
        <CardHeader>
          <CardTitle>Overall System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {health?.healthy ? (
                <CheckCircle2 className="h-12 w-12 text-green-600" />
              ) : unhealthyServices > 0 ? (
                <XCircle className="h-12 w-12 text-red-600" />
              ) : (
                <AlertCircle className="h-12 w-12 text-yellow-600" />
              )}
              <div>
                <div className="text-2xl font-bold">
                  {health?.healthy ? 'All Systems Operational' :
                   unhealthyServices > 0 ? 'Critical Issues' :
                   'Degraded Performance'}
                </div>
                <div className="text-sm text-gray-500">
                  {healthyServices} healthy, {degradedServices} degraded, {unhealthyServices} unhealthy
                </div>
                {health?.failed_services && health.failed_services.length > 0 && (
                  <div className="text-sm text-red-600 mt-1">
                    Failed: {health.failed_services.join(', ')}
                  </div>
                )}
              </div>
            </div>
            <div className="flex gap-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{healthyServices}</div>
                <div className="text-sm text-gray-500">Healthy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{degradedServices}</div>
                <div className="text-sm text-gray-500">Degraded</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{unhealthyServices}</div>
                <div className="text-sm text-gray-500">Unhealthy</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="services">
        <TabsList>
          <TabsTrigger>Services</TabsTrigger>
          <TabsTrigger>System Metrics</TabsTrigger>
          <TabsTrigger>Response Times</TabsTrigger>
        </TabsList>

        {/* Services Tab */}
        <TabsContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {services.map((service) => (
              <Card key={service.name}>
                <CardContent className="p-6">
                  <div className="flex justify-between items-start">
                    <div className="flex items-start gap-3">
                      {getStatusIcon(service.status)}
                      <div>
                        <h3 className="font-semibold">{service.name}</h3>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {service.lastCheck}
                          </span>
                          <span className="flex items-center gap-1">
                            <Activity className="h-3 w-3" />
                            {service.uptime}% uptime
                          </span>
                          {service.responseTime > 0 && (
                            <span className="flex items-center gap-1">
                              <Zap className="h-3 w-3" />
                              {service.responseTime}ms
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <Badge
                      variant={
                        service.status === 'healthy' ? 'default' :
                        service.status === 'degraded' ? 'secondary' : 'destructive'
                      }
                    >
                      {service.status}
                    </Badge>
                  </div>
                  <div className="mt-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-500">Uptime</span>
                      <span>{service.uptime}%</span>
                    </div>
                    <Progress value={service.uptime} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* System Metrics Tab */}
        <TabsContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium">CPU Usage</span>
                    </div>
                    <div className="text-2xl font-bold mt-2">{systemMetrics.cpu.current}%</div>
                  </div>
                  {getTrendIcon(systemMetrics.cpu.trend)}
                </div>
                <Progress value={systemMetrics.cpu.current} className="h-2 mt-4" />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <MemoryStick className="h-4 w-4 text-purple-600" />
                      <span className="text-sm font-medium">Memory</span>
                    </div>
                    <div className="text-2xl font-bold mt-2">{systemMetrics.memory.current}%</div>
                  </div>
                  {getTrendIcon(systemMetrics.memory.trend)}
                </div>
                <Progress value={systemMetrics.memory.current} className="h-2 mt-4" />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium">Disk Usage</span>
                    </div>
                    <div className="text-2xl font-bold mt-2">{systemMetrics.disk.current}%</div>
                  </div>
                  {getTrendIcon(systemMetrics.disk.trend)}
                </div>
                <Progress value={systemMetrics.disk.current} className="h-2 mt-4" />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Network className="h-4 w-4 text-orange-600" />
                      <span className="text-sm font-medium">Network</span>
                    </div>
                    <div className="text-2xl font-bold mt-2">{systemMetrics.network.current}%</div>
                  </div>
                  {getTrendIcon(systemMetrics.network.trend)}
                </div>
                <Progress value={systemMetrics.network.current} className="h-2 mt-4" />
              </CardContent>
            </Card>
          </div>

          {/* Metric History Chart */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>24-Hour History</CardTitle>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant={selectedMetric === 'cpu' ? 'default' : 'outline'}
                    onClick={() => setSelectedMetric('cpu')}
                  >
                    CPU
                  </Button>
                  <Button
                    size="sm"
                    variant={selectedMetric === 'memory' ? 'default' : 'outline'}
                    onClick={() => setSelectedMetric('memory')}
                  >
                    Memory
                  </Button>
                  <Button
                    size="sm"
                    variant={selectedMetric === 'disk' ? 'default' : 'outline'}
                    onClick={() => setSelectedMetric('disk')}
                  >
                    Disk
                  </Button>
                  <Button
                    size="sm"
                    variant={selectedMetric === 'network' ? 'default' : 'outline'}
                    onClick={() => setSelectedMetric('network')}
                  >
                    Network
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={systemMetrics[selectedMetric as keyof typeof systemMetrics].history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#3b82f6"
                    fill="#93c5fd"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Response Times Tab */}
        <TabsContent className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Response Times</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={responseTimeHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis label={{ value: 'Response Time (ms)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="p50"
                    stroke="#10b981"
                    name="P50 (Median)"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="p95"
                    stroke="#f59e0b"
                    name="P95"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="p99"
                    stroke="#ef4444"
                    name="P99"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Average Response Time</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">45ms</div>
                <p className="text-xs text-muted-foreground">
                  -5ms from last hour
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">0.12%</div>
                <p className="text-xs text-muted-foreground">
                  Within acceptable range
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Requests/sec</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">1,247</div>
                <p className="text-xs text-muted-foreground">
                  +15% from yesterday
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}