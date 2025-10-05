'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Bell,
  Mail,
  MessageSquare,
  Smartphone,
  Monitor,
  Chrome,
  Volume2,
  BellOff,
  Clock,
  Zap,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  ShieldAlert,
  CreditCard,
  Users,
  FileText,
  Calendar,
  Settings,
  Save,
  RotateCcw,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

// Migrated from sonner to useToast hook
// Note: toast options have changed:
// - sonner: toast.success('msg') -> useToast: toast({ title: 'Success', description: 'msg' })
// - sonner: toast.error('msg') -> useToast: toast({ title: 'Error', description: 'msg', variant: 'destructive' })
// - For complex options, refer to useToast documentation

// Mock notification preferences
const mockPreferences = {
  email: {
    enabled: true,
    digest: 'daily',
    categories: {
      security: true,
      billing: true,
      updates: true,
      marketing: false,
      team: true,
      system: true,
    },
  },
  push: {
    enabled: true,
    sound: true,
    vibrate: true,
    categories: {
      security: true,
      billing: true,
      updates: false,
      marketing: false,
      team: true,
      system: true,
    },
  },
  inApp: {
    enabled: true,
    showBadge: true,
    categories: {
      security: true,
      billing: true,
      updates: true,
      marketing: true,
      team: true,
      system: true,
    },
  },
  sms: {
    enabled: false,
    onlyUrgent: true,
    categories: {
      security: true,
      billing: false,
      updates: false,
      marketing: false,
      team: false,
      system: true,
    },
  },
  slack: {
    enabled: true,
    channel: '#notifications',
    categories: {
      security: true,
      billing: true,
      updates: false,
      marketing: false,
      team: true,
      system: true,
    },
  },
  quietHours: {
    enabled: true,
    start: '22:00',
    end: '08:00',
    timezone: 'America/Los_Angeles',
    allowUrgent: true,
  },
};

// Notification categories with descriptions
const notificationCategories = [
  {
    id: 'security',
    name: 'Security Alerts',
    description: 'Login attempts, password changes, 2FA updates',
    icon: ShieldAlert,
    color: 'text-red-600 dark:text-red-400',
  },
  {
    id: 'billing',
    name: 'Billing & Payments',
    description: 'Invoices, payment confirmations, subscription changes',
    icon: CreditCard,
    color: 'text-green-600 dark:text-green-400',
  },
  {
    id: 'updates',
    name: 'Product Updates',
    description: 'New features, improvements, maintenance notices',
    icon: TrendingUp,
    color: 'text-blue-600 dark:text-blue-400',
  },
  {
    id: 'marketing',
    name: 'Marketing',
    description: 'Promotions, newsletters, tips and tricks',
    icon: Mail,
    color: 'text-purple-600 dark:text-purple-400',
  },
  {
    id: 'team',
    name: 'Team Activity',
    description: 'Member invites, role changes, collaborations',
    icon: Users,
    color: 'text-yellow-600 dark:text-yellow-400',
  },
  {
    id: 'system',
    name: 'System Notifications',
    description: 'Errors, warnings, system status updates',
    icon: AlertCircle,
    color: 'text-muted-foreground',
  },
];

export default function NotificationSettingsPage() {
  const { toast } = useToast();

  const [preferences, setPreferences] = useState(mockPreferences);
  const [hasChanges, setHasChanges] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChannelToggle = (channel: string, enabled: boolean) => {
    setPreferences({
      ...preferences,
      [channel]: {
        ...preferences[channel as keyof typeof preferences],
        enabled,
      },
    });
    setHasChanges(true);
  };

  const handleCategoryToggle = (channel: string, category: string, enabled: boolean) => {
    const channelPrefs = preferences[channel as keyof typeof preferences];

    // Type guard to check if channel has categories
    if (channelPrefs && typeof channelPrefs === 'object' && 'categories' in channelPrefs) {
      setPreferences({
        ...preferences,
        [channel]: {
          ...channelPrefs,
          categories: {
            ...(channelPrefs.categories as Record<string, boolean>),
            [category]: enabled,
          },
        },
      });
      setHasChanges(true);
    }
  };

  const handleQuietHoursToggle = (enabled: boolean) => {
    setPreferences({
      ...preferences,
      quietHours: {
        ...preferences.quietHours,
        enabled,
      },
    });
    setHasChanges(true);
  };

  const handleSavePreferences = async () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setHasChanges(false);
      toast({ title: 'Success', description: 'Notification preferences saved' });
    }, 1000);
  };

  const handleResetDefaults = () => {
    setPreferences(mockPreferences);
    setHasChanges(false);
    toast({ title: 'Success', description: 'Reset to default preferences' });
  };

  const handleTestNotification = (channel: string) => {
    toast({ title: 'Success', description: `Test ${channel} notification sent` });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Notification Settings</h1>
          <p className="text-muted-foreground mt-2">Manage how and when you receive notifications</p>
        </div>
        {hasChanges && (
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleResetDefaults}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
            <Button onClick={handleSavePreferences} disabled={isLoading}>
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </Button>
          </div>
        )}
      </div>

      {/* Quick Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Settings</CardTitle>
          <CardDescription>Quickly manage your notification preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base">Pause All Notifications</Label>
              <p className="text-sm text-muted-foreground">Temporarily disable all notifications</p>
            </div>
            <Switch />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base">Quiet Hours</Label>
              <p className="text-sm text-muted-foreground">
                No notifications from {preferences.quietHours.start} to {preferences.quietHours.end}
              </p>
            </div>
            <Switch
              checked={preferences.quietHours.enabled}
              onCheckedChange={handleQuietHoursToggle}
            />
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="channels" className="space-y-4">
        <TabsList>
          <TabsTrigger value="channels">Channels</TabsTrigger>
          <TabsTrigger value="categories">Categories</TabsTrigger>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
        </TabsList>

        {/* Channels Tab */}
        <TabsContent value="channels" className="space-y-4">
          {/* Email Notifications */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  <div>
                    <CardTitle className="text-base">Email Notifications</CardTitle>
                    <CardDescription>Receive notifications via email</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTestNotification('email')}
                  >
                    Test
                  </Button>
                  <Switch
                    checked={preferences.email.enabled}
                    onCheckedChange={(checked) => handleChannelToggle('email', checked)}
                  />
                </div>
              </div>
            </CardHeader>
            {preferences.email.enabled && (
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Email Digest</Label>
                  <RadioGroup>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem
                        value="instant"
                        id="instant"
                        name="email-digest"
                        checked={preferences.email.digest === 'instant'}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setPreferences({
                              ...preferences,
                              email: { ...preferences.email, digest: 'instant' },
                            });
                            setHasChanges(true);
                          }
                        }}
                      />
                      <Label htmlFor="instant">Instant</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem
                        value="daily"
                        id="daily"
                        name="email-digest"
                        checked={preferences.email.digest === 'daily'}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setPreferences({
                              ...preferences,
                              email: { ...preferences.email, digest: 'daily' },
                            });
                            setHasChanges(true);
                          }
                        }}
                      />
                      <Label htmlFor="daily">Daily Digest</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem
                        value="weekly"
                        id="weekly"
                        name="email-digest"
                        checked={preferences.email.digest === 'weekly'}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setPreferences({
                              ...preferences,
                              email: { ...preferences.email, digest: 'weekly' },
                            });
                            setHasChanges(true);
                          }
                        }}
                      />
                      <Label htmlFor="weekly">Weekly Summary</Label>
                    </div>
                  </RadioGroup>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Push Notifications */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <Smartphone className="h-5 w-5 text-green-600 dark:text-green-400" />
                  <div>
                    <CardTitle className="text-base">Push Notifications</CardTitle>
                    <CardDescription>Receive notifications on your devices</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTestNotification('push')}
                  >
                    Test
                  </Button>
                  <Switch
                    checked={preferences.push.enabled}
                    onCheckedChange={(checked) => handleChannelToggle('push', checked)}
                  />
                </div>
              </div>
            </CardHeader>
            {preferences.push.enabled && (
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Sound</Label>
                  <Switch
                    checked={preferences.push.sound}
                    onCheckedChange={(checked) => {
                      setPreferences({
                        ...preferences,
                        push: { ...preferences.push, sound: checked },
                      });
                      setHasChanges(true);
                    }}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>Vibration</Label>
                  <Switch
                    checked={preferences.push.vibrate}
                    onCheckedChange={(checked) => {
                      setPreferences({
                        ...preferences,
                        push: { ...preferences.push, vibrate: checked },
                      });
                      setHasChanges(true);
                    }}
                  />
                </div>
              </CardContent>
            )}
          </Card>

          {/* In-App Notifications */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <Monitor className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  <div>
                    <CardTitle className="text-base">In-App Notifications</CardTitle>
                    <CardDescription>Show notifications within the application</CardDescription>
                  </div>
                </div>
                <Switch
                  checked={preferences.inApp.enabled}
                  onCheckedChange={(checked) => handleChannelToggle('inApp', checked)}
                />
              </div>
            </CardHeader>
            {preferences.inApp.enabled && (
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Show Badge Count</Label>
                  <Switch
                    checked={preferences.inApp.showBadge}
                    onCheckedChange={(checked) => {
                      setPreferences({
                        ...preferences,
                        inApp: { ...preferences.inApp, showBadge: checked },
                      });
                      setHasChanges(true);
                    }}
                  />
                </div>
              </CardContent>
            )}
          </Card>

          {/* SMS Notifications */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                  <div>
                    <CardTitle className="text-base">SMS Notifications</CardTitle>
                    <CardDescription>Receive text messages for urgent alerts</CardDescription>
                  </div>
                </div>
                <Switch
                  checked={preferences.sms.enabled}
                  onCheckedChange={(checked) => handleChannelToggle('sms', checked)}
                />
              </div>
            </CardHeader>
            {preferences.sms.enabled && (
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Only Urgent Notifications</Label>
                  <Switch
                    checked={preferences.sms.onlyUrgent}
                    onCheckedChange={(checked) => {
                      setPreferences({
                        ...preferences,
                        sms: { ...preferences.sms, onlyUrgent: checked },
                      });
                      setHasChanges(true);
                    }}
                  />
                </div>
              </CardContent>
            )}
          </Card>

          {/* Slack Integration */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-5 w-5 text-pink-600 dark:text-pink-400" />
                  <div>
                    <CardTitle className="text-base">Slack Integration</CardTitle>
                    <CardDescription>Send notifications to your Slack workspace</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {preferences.slack.enabled && (
                    <Badge variant="outline">{preferences.slack.channel}</Badge>
                  )}
                  <Switch
                    checked={preferences.slack.enabled}
                    onCheckedChange={(checked) => handleChannelToggle('slack', checked)}
                  />
                </div>
              </div>
            </CardHeader>
          </Card>
        </TabsContent>

        {/* Categories Tab */}
        <TabsContent value="categories" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Notification Categories</CardTitle>
              <CardDescription>
                Choose which types of notifications you want to receive on each channel
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {notificationCategories.map((category) => {
                  const Icon = category.icon;
                  return (
                    <div key={category.id}>
                      <div className="flex items-start gap-3 mb-3">
                        <Icon className={`h-5 w-5 mt-0.5 ${category.color}`} />
                        <div className="flex-1">
                          <p className="font-medium">{category.name}</p>
                          <p className="text-sm text-muted-foreground">{category.description}</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 ml-8">
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={preferences.email.categories[category.id as keyof typeof preferences.email.categories]}
                            onCheckedChange={(checked) =>
                              handleCategoryToggle('email', category.id, checked)
                            }
                            disabled={!preferences.email.enabled}
                          />
                          <Label className="text-sm">Email</Label>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={preferences.push.categories[category.id as keyof typeof preferences.push.categories]}
                            onCheckedChange={(checked) =>
                              handleCategoryToggle('push', category.id, checked)
                            }
                            disabled={!preferences.push.enabled}
                          />
                          <Label className="text-sm">Push</Label>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={preferences.inApp.categories[category.id as keyof typeof preferences.inApp.categories]}
                            onCheckedChange={(checked) =>
                              handleCategoryToggle('inApp', category.id, checked)
                            }
                            disabled={!preferences.inApp.enabled}
                          />
                          <Label className="text-sm">In-App</Label>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={preferences.sms.categories[category.id as keyof typeof preferences.sms.categories]}
                            onCheckedChange={(checked) =>
                              handleCategoryToggle('sms', category.id, checked)
                            }
                            disabled={!preferences.sms.enabled}
                          />
                          <Label className="text-sm">SMS</Label>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={preferences.slack.categories[category.id as keyof typeof preferences.slack.categories]}
                            onCheckedChange={(checked) =>
                              handleCategoryToggle('slack', category.id, checked)
                            }
                            disabled={!preferences.slack.enabled}
                          />
                          <Label className="text-sm">Slack</Label>
                        </div>
                      </div>
                      {category.id !== 'system' && <Separator className="mt-6" />}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Schedule Tab */}
        <TabsContent value="schedule" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quiet Hours</CardTitle>
              <CardDescription>
                Set times when you don&apos;t want to receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Quiet Hours</Label>
                  <p className="text-sm text-muted-foreground">Pause non-urgent notifications during set hours</p>
                </div>
                <Switch
                  checked={preferences.quietHours.enabled}
                  onCheckedChange={handleQuietHoursToggle}
                />
              </div>

              {preferences.quietHours.enabled && (
                <>
                  <Separator />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="quiet-start">Start Time</Label>
                      <select
                        id="quiet-start"
                        value={preferences.quietHours.start}
                        onChange={(e) => {
                          setPreferences({
                            ...preferences,
                            quietHours: { ...preferences.quietHours, start: e.target.value },
                          });
                          setHasChanges(true);
                        }}
                        className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground"
                      >
                        <option value="20:00">8:00 PM</option>
                        <option value="21:00">9:00 PM</option>
                        <option value="22:00">10:00 PM</option>
                        <option value="23:00">11:00 PM</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="quiet-end">End Time</Label>
                      <select
                        id="quiet-end"
                        value={preferences.quietHours.end}
                        onChange={(e) => {
                          setPreferences({
                            ...preferences,
                            quietHours: { ...preferences.quietHours, end: e.target.value },
                          });
                          setHasChanges(true);
                        }}
                        className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground"
                      >
                        <option value="06:00">6:00 AM</option>
                        <option value="07:00">7:00 AM</option>
                        <option value="08:00">8:00 AM</option>
                        <option value="09:00">9:00 AM</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Allow Urgent Notifications</Label>
                      <p className="text-sm text-muted-foreground">
                        Receive critical security and system alerts during quiet hours
                      </p>
                    </div>
                    <Switch
                      checked={preferences.quietHours.allowUrgent}
                      onCheckedChange={(checked) => {
                        setPreferences({
                          ...preferences,
                          quietHours: { ...preferences.quietHours, allowUrgent: checked },
                        });
                        setHasChanges(true);
                      }}
                    />
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Weekly Schedule</CardTitle>
              <CardDescription>
                Customize notification preferences for specific days
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-muted-foreground py-8">
                <Calendar className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-sm">Weekly scheduling coming soon</p>
                <p className="text-xs mt-2">Set different notification rules for weekdays and weekends</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}