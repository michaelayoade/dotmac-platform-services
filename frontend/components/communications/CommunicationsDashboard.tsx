/**
 * Communications Dashboard - Main component combining templates and campaigns
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Mail, Template, BarChart3 } from 'lucide-react';
import { TemplateManager } from './TemplateManager';
import { BulkEmailManager } from './BulkEmailManager';

interface StatsCardProps {
  title: string;
  value: string | number;
  description: string;
  icon: React.ReactNode;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, description, icon }) => (
  <Card>
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-gray-500">{description}</p>
        </div>
        <div className="text-gray-400">{icon}</div>
      </div>
    </CardContent>
  </Card>
);

export const CommunicationsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Communications</h1>
          <p className="text-gray-600">Manage email templates and bulk campaigns</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <StatsCard
              title="Active Templates"
              value="12"
              description="Ready to use"
              icon={<Template className="w-6 h-6" />}
            />
            <StatsCard
              title="Campaigns This Month"
              value="8"
              description="3 active, 5 completed"
              icon={<Mail className="w-6 h-6" />}
            />
            <StatsCard
              title="Emails Sent"
              value="24.5K"
              description="This month"
              icon={<BarChart3 className="w-6 h-6" />}
            />
            <StatsCard
              title="Success Rate"
              value="98.2%"
              description="Last 30 days"
              icon={<BarChart3 className="w-6 h-6" />}
            />
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Recent Campaigns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Recent campaigns list would go here */}
                  <div className="text-sm text-gray-500 text-center py-8">
                    No recent campaigns
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Template Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Template usage stats would go here */}
                  <div className="text-sm text-gray-500 text-center py-8">
                    Template usage analytics
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="templates">
          <TemplateManager />
        </TabsContent>

        <TabsContent value="campaigns">
          <BulkEmailManager />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Email Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-gray-500 text-center py-8">
                Analytics dashboard coming soon...
                <br />
                <span className="text-xs">Track open rates, click rates, and campaign performance</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};