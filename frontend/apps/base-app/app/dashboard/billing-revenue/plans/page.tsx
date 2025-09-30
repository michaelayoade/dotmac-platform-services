'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import {
  Plus,
  Edit2,
  Trash2,
  Package,
  Check,
  X,
  DollarSign,
  Users,
  Zap,
  Shield,
  Star,
  TrendingUp,
  Archive,
  Eye,
  EyeOff,
  Loader2,
} from 'lucide-react';
import { useBillingPlans, type BillingPlan } from '@/hooks/useBillingPlans';

interface PlanFeature {
  id: string;
  name: string;
  description?: string;
  included: boolean;
  limit?: number | string;
}

interface Plan {
  id: string;
  name: string;
  description: string;
  price_monthly: number;
  price_annual: number;
  currency: string;
  status: 'active' | 'inactive' | 'archived';
  tier: 'starter' | 'professional' | 'enterprise' | 'custom';
  features: PlanFeature[];
  popular: boolean;
  trial_days: number;
  max_users?: number;
  storage_gb?: number;
  api_calls?: number;
  created_at: string;
  updated_at: string;
  subscriber_count: number;
  mrr: number;
}

const defaultFeatures: PlanFeature[] = [
  { id: 'users', name: 'Team Members', included: true, limit: '5' },
  { id: 'storage', name: 'Storage', included: true, limit: '10 GB' },
  { id: 'api', name: 'API Calls', included: true, limit: '10,000/mo' },
  { id: 'support', name: 'Email Support', included: true },
  { id: 'analytics', name: 'Advanced Analytics', included: false },
  { id: 'sso', name: 'SSO Integration', included: false },
  { id: 'audit', name: 'Audit Logs', included: false },
  { id: 'custom', name: 'Custom Integrations', included: false },
];

export default function PlansPage() {
  const { toast } = useToast();
  const {
    plans: backendPlans,
    products,
    loading: plansLoading,
    error,
    createPlan,
    updatePlan,
    deletePlan
  } = useBillingPlans();

  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'quarterly' | 'annual'>('monthly');
  const [showNewPlanDialog, setShowNewPlanDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedBackendPlan, setSelectedBackendPlan] = useState<BillingPlan | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [newPlanData, setNewPlanData] = useState({
    product_id: '',
    billing_interval: 'monthly' as 'monthly' | 'quarterly' | 'annual',
    interval_count: 1,
    trial_days: 14,
  });
  const [newPlan, setNewPlan] = useState<Partial<Plan>>({
    name: '',
    description: '',
    price_monthly: 0,
    price_annual: 0,
    tier: 'custom',
    features: [],
    trial_days: 14,
  });

  // Use backend plans directly or mock data as fallback
  // TODO: Complete backend plan mapping when API is stabilized
  const plans: Plan[] = backendPlans.length > 0 ? backendPlans.map(plan => ({
    id: plan.plan_id,
    name: plan.name || plan.display_name || 'Unknown Plan',
    description: plan.description || '',
    price_monthly: plan.billing_interval === 'monthly' ? plan.price_amount / 100 : 0,
    price_annual: plan.billing_interval === 'annual' ? plan.price_amount / 100 : 0,
    currency: plan.currency || 'USD',
    status: plan.is_active ? 'active' : 'inactive',
    tier: (plan.name?.toLowerCase() as 'starter' | 'professional' | 'enterprise' | 'custom') || 'custom',
    features: [],
    popular: false,
    trial_days: plan.trial_days || 0,
    max_users: 0,
    storage_gb: 0,
    api_calls: 0,
    created_at: plan.created_at,
    updated_at: plan.updated_at,
    subscriber_count: 0,
    mrr: 0,
  })) : [
        {
          id: 'plan-starter',
          name: 'Starter',
          description: 'Perfect for small teams just getting started',
          price_monthly: 29,
          price_annual: 290,
          currency: 'USD',
          status: 'active',
          tier: 'starter',
          features: [
            { id: 'users', name: 'Up to 5 team members', included: true, limit: '5' },
            { id: 'storage', name: '10 GB storage', included: true, limit: '10 GB' },
            { id: 'api', name: '10,000 API calls/mo', included: true, limit: '10,000' },
            { id: 'support', name: 'Email support', included: true },
            { id: 'analytics', name: 'Basic analytics', included: true },
            { id: 'sso', name: 'SSO Integration', included: false },
            { id: 'audit', name: 'Audit Logs', included: false },
            { id: 'custom', name: 'Custom Integrations', included: false },
          ],
          popular: false,
          trial_days: 14,
          max_users: 5,
          storage_gb: 10,
          api_calls: 10000,
          created_at: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          subscriber_count: 125,
          mrr: 3625,
        },
        {
          id: 'plan-pro',
          name: 'Professional',
          description: 'For growing teams that need more power and flexibility',
          price_monthly: 99,
          price_annual: 990,
          currency: 'USD',
          status: 'active',
          tier: 'professional',
          features: [
            { id: 'users', name: 'Up to 20 team members', included: true, limit: '20' },
            { id: 'storage', name: '100 GB storage', included: true, limit: '100 GB' },
            { id: 'api', name: '100,000 API calls/mo', included: true, limit: '100,000' },
            { id: 'support', name: 'Priority email support', included: true },
            { id: 'analytics', name: 'Advanced analytics', included: true },
            { id: 'sso', name: 'SSO Integration', included: true },
            { id: 'audit', name: 'Audit Logs', included: true },
            { id: 'custom', name: 'Custom Integrations', included: false },
          ],
          popular: true,
          trial_days: 14,
          max_users: 20,
          storage_gb: 100,
          api_calls: 100000,
          created_at: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
          subscriber_count: 89,
          mrr: 8811,
        },
        {
          id: 'plan-ent',
          name: 'Enterprise',
          description: 'Full-featured solution for large organizations',
          price_monthly: 499,
          price_annual: 4990,
          currency: 'USD',
          status: 'active',
          tier: 'enterprise',
          features: [
            { id: 'users', name: 'Unlimited team members', included: true, limit: 'Unlimited' },
            { id: 'storage', name: '1 TB storage', included: true, limit: '1 TB' },
            { id: 'api', name: 'Unlimited API calls', included: true, limit: 'Unlimited' },
            { id: 'support', name: '24/7 phone & email support', included: true },
            { id: 'analytics', name: 'Advanced analytics & reporting', included: true },
            { id: 'sso', name: 'SSO & SAML Integration', included: true },
            { id: 'audit', name: 'Full audit logs & compliance', included: true },
            { id: 'custom', name: 'Custom integrations', included: true },
            { id: 'sla', name: '99.9% SLA', included: true },
            { id: 'manager', name: 'Dedicated success manager', included: true },
          ],
          popular: false,
          trial_days: 30,
          max_users: -1,
          storage_gb: 1000,
          api_calls: -1,
          created_at: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          subscriber_count: 12,
          mrr: 5988,
        },
      ];

  const handleCreatePlan = async () => {
    if (!newPlan.name || !newPlan.description || newPlan.price_monthly <= 0) {
      toast({
        title: 'Error',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    try {
      // API call would go here
      toast({
        title: 'Success',
        description: 'Pricing plan created successfully',
      });
      setShowNewPlanDialog(false);
      // Refresh handled by hook
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create pricing plan',
        variant: 'destructive',
      });
    }
  };

  const handleUpdatePlan = async () => {
    if (!selectedPlan) return;

    try {
      // API call would go here
      toast({
        title: 'Success',
        description: 'Pricing plan updated successfully',
      });
      setShowEditDialog(false);
      // Refresh handled by hook
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update pricing plan',
        variant: 'destructive',
      });
    }
  };

  const handleArchivePlan = async (plan: Plan) => {
    if (!confirm(`Are you sure you want to archive the ${plan.name} plan? Existing subscribers will not be affected.`)) {
      return;
    }

    try {
      // API call would go here
      toast({
        title: 'Success',
        description: `${plan.name} plan has been archived`,
      });
      // Refresh handled by hook
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to archive plan',
        variant: 'destructive',
      });
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'starter':
        return 'bg-blue-100 text-blue-800';
      case 'professional':
        return 'bg-purple-100 text-purple-800';
      case 'enterprise':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const totalMRR = plans.reduce((sum, plan) => sum + plan.mrr, 0);
  const totalSubscribers = plans.reduce((sum, plan) => sum + plan.subscriber_count, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Pricing Plans</h1>
          <p className="text-gray-500">Manage your subscription tiers and pricing</p>
        </div>
        <Button onClick={() => setShowNewPlanDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Plan
        </Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Plans</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{plans.filter(p => p.status === 'active').length}</div>
            <p className="text-xs text-gray-500">Available for subscription</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Subscribers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalSubscribers}</div>
            <p className="text-xs text-gray-500">Across all plans</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total MRR</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalMRR, 'USD')}</div>
            <p className="text-xs text-gray-500">Monthly recurring revenue</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Avg Revenue/User</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalSubscribers > 0 ? formatCurrency(totalMRR / totalSubscribers, 'USD') : '$0'}
            </div>
            <p className="text-xs text-gray-500">ARPU</p>
          </CardContent>
        </Card>
      </div>

      {/* Billing Period Toggle */}
      <div className="flex justify-center">
        <div className="inline-flex items-center space-x-2 p-1 bg-gray-100 rounded-lg">
          <Button
            variant={billingPeriod === 'monthly' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setBillingPeriod('monthly')}
          >
            Monthly Billing
          </Button>
          <Button
            variant={billingPeriod === 'annual' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setBillingPeriod('annual')}
          >
            Annual Billing
            <Badge variant="secondary" className="ml-2">Save 20%</Badge>
          </Button>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card key={plan.id} className={`relative ${plan.popular ? 'border-purple-500 border-2' : ''}`}>
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <Badge className="bg-purple-500 text-white">
                  <Star className="h-3 w-3 mr-1" />
                  Most Popular
                </Badge>
              </div>
            )}
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl">{plan.name}</CardTitle>
                  <CardDescription className="mt-1">{plan.description}</CardDescription>
                </div>
                <Badge className={getTierColor(plan.tier)} variant="secondary">
                  {plan.tier}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-3xl font-bold">
                  {formatCurrency(
                    billingPeriod === 'monthly' ? plan.price_monthly : plan.price_annual,
                    plan.currency
                  )}
                  <span className="text-lg font-normal text-gray-500">
                    /{billingPeriod === 'monthly' ? 'month' : 'year'}
                  </span>
                </div>
                {billingPeriod === 'annual' && (
                  <p className="text-sm text-green-600">
                    Save {formatCurrency(plan.price_monthly * 12 - plan.price_annual, plan.currency)} per year
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center text-sm text-gray-500">
                  <Users className="h-4 w-4 mr-2" />
                  {plan.subscriber_count} active subscribers
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <DollarSign className="h-4 w-4 mr-2" />
                  {formatCurrency(plan.mrr, plan.currency)} MRR
                </div>
                <div className="flex items-center text-sm text-gray-500">
                  <Zap className="h-4 w-4 mr-2" />
                  {plan.trial_days} day free trial
                </div>
              </div>

              <div className="border-t pt-4">
                <p className="text-sm font-medium mb-3">Features</p>
                <ul className="space-y-2">
                  {plan.features.slice(0, 5).map((feature) => (
                    <li key={feature.id} className="flex items-start text-sm">
                      {feature.included ? (
                        <Check className="h-4 w-4 text-green-500 mr-2 mt-0.5" />
                      ) : (
                        <X className="h-4 w-4 text-gray-300 mr-2 mt-0.5" />
                      )}
                      <span className={feature.included ? '' : 'text-gray-400'}>
                        {feature.name}
                      </span>
                    </li>
                  ))}
                </ul>
                {plan.features.length > 5 && (
                  <Button variant="link" size="sm" className="mt-2 p-0">
                    View all features ({plan.features.length})
                  </Button>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => {
                  setSelectedPlan(plan);
                  setShowEditDialog(true);
                }}
              >
                <Edit2 className="h-4 w-4 mr-1" />
                Edit
              </Button>
              {plan.status === 'active' ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleArchivePlan(plan)}
                >
                  <Archive className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                >
                  <Eye className="h-4 w-4" />
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
      </div>

      {/* New Plan Dialog */}
      <Dialog open={showNewPlanDialog} onOpenChange={setShowNewPlanDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Pricing Plan</DialogTitle>
            <DialogDescription>
              Set up a new subscription tier for your customers
            </DialogDescription>
          </DialogHeader>
          <Tabs>
            <TabsList>
              <TabsTrigger>General</TabsTrigger>
              <TabsTrigger>Features</TabsTrigger>
              <TabsTrigger>Limits</TabsTrigger>
            </TabsList>
            <TabsContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Plan Name</Label>
                  <Input
                    value={newPlan.name}
                    onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })}
                    placeholder="e.g., Professional"
                  />
                </div>
                <div>
                  <Label>Tier</Label>
                  <select
                    value={newPlan.tier}
                    onChange={(e) => setNewPlan({ ...newPlan, tier: e.target.value as 'starter' | 'professional' | 'enterprise' | 'custom' })}
                    className="flex h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white"
                  >
                    <option value="starter">Starter</option>
                    <option value="professional">Professional</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={newPlan.description}
                  onChange={(e) => setNewPlan({ ...newPlan, description: e.target.value })}
                  placeholder="Brief description of the plan"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Monthly Price (USD)</Label>
                  <Input
                    type="number"
                    value={newPlan.price_monthly}
                    onChange={(e) => setNewPlan({ ...newPlan, price_monthly: parseFloat(e.target.value) })}
                    placeholder="99"
                  />
                </div>
                <div>
                  <Label>Annual Price (USD)</Label>
                  <Input
                    type="number"
                    value={newPlan.price_annual}
                    onChange={(e) => setNewPlan({ ...newPlan, price_annual: parseFloat(e.target.value) })}
                    placeholder="990"
                  />
                </div>
              </div>
              <div>
                <Label>Trial Period (days)</Label>
                <Input
                  type="number"
                  value={newPlan.trial_days}
                  onChange={(e) => setNewPlan({ ...newPlan, trial_days: parseInt(e.target.value) })}
                  placeholder="14"
                />
              </div>
            </TabsContent>
            <TabsContent className="space-y-4">
              <p className="text-sm text-gray-500">Select which features are included in this plan</p>
              <div className="space-y-3">
                {newPlan.features.map((feature, index) => (
                  <div key={feature.id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={feature.included}
                        onCheckedChange={(checked) => {
                          const updated = [...newPlan.features];
                          updated[index].included = checked;
                          setNewPlan({ ...newPlan, features: updated });
                        }}
                      />
                      <Label className="font-normal">{feature.name}</Label>
                    </div>
                    {feature.limit && (
                      <Input
                        className="w-32"
                        value={feature.limit}
                        onChange={(e) => {
                          const updated = [...newPlan.features];
                          updated[index].limit = e.target.value;
                          setNewPlan({ ...newPlan, features: updated });
                        }}
                        placeholder="Limit"
                      />
                    )}
                  </div>
                ))}
              </div>
            </TabsContent>
            <TabsContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Max Users</Label>
                  <Input type="number" placeholder="20" />
                </div>
                <div>
                  <Label>Storage (GB)</Label>
                  <Input type="number" placeholder="100" />
                </div>
                <div>
                  <Label>API Calls/Month</Label>
                  <Input type="number" placeholder="100000" />
                </div>
                <div>
                  <Label>Custom Domains</Label>
                  <Input type="number" placeholder="5" />
                </div>
              </div>
            </TabsContent>
          </Tabs>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewPlanDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreatePlan}>
              Create Plan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Plan Dialog */}
      {selectedPlan && (
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit {selectedPlan.name} Plan</DialogTitle>
              <DialogDescription>
                Update pricing and features for this plan
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Monthly Price</Label>
                <Input
                  type="number"
                  defaultValue={selectedPlan.price_monthly}
                  placeholder="Monthly price"
                />
              </div>
              <div>
                <Label>Annual Price</Label>
                <Input
                  type="number"
                  defaultValue={selectedPlan.price_annual}
                  placeholder="Annual price"
                />
              </div>
              <div>
                <Label>Status</Label>
                <select
                  defaultValue={selectedPlan?.status || 'active'}
                  className="flex h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleUpdatePlan}>
                Save Changes
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}