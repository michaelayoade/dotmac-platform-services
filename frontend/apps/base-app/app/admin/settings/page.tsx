"use client";

import { useState } from "react";
import { Save, ShieldAlert, Clock, Bell } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

export default function AdminSettingsPage() {
  const [enforceMfa, setEnforceMfa] = useState(true);
  const [sessionTimeout, setSessionTimeout] = useState(30);
  const [notifyOnChanges, setNotifyOnChanges] = useState(true);
  const [webhookUrl, setWebhookUrl] = useState("https://hooks.example.com/admin-events");
  const [policyText, setPolicyText] = useState(
    "Administrators must rotate passwords every 90 days and ensure MFA is active before accessing production environments."
  );

  return (
    <div className="space-y-6" data-testid="settings">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Platform controls</p>
        <h1 className="text-3xl font-semibold text-foreground">Security & compliance settings</h1>
        <p className="max-w-2xl text-sm text-muted-foreground">
          Update organisation-wide rules for privileged accounts, session policies, notifications and audit requirements.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-primary/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg font-semibold">
              <ShieldAlert className="h-5 w-5 text-primary" />
              Authentication requirements
            </CardTitle>
            <CardDescription>Define how administrators prove their identity when signing in.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-start justify-between gap-4 rounded-lg border border-border bg-card px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-foreground">Enforce MFA for admin users</p>
                <p className="text-xs text-muted-foreground">
                  Require a second factor during sign-in. Users without MFA configured will be redirected to the MFA setup flow.
                </p>
              </div>
              <Switch checked={enforceMfa} onCheckedChange={setEnforceMfa} aria-label="Toggle MFA enforcement" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="policyText" className="text-sm font-semibold text-foreground">
                Administrator security policy
              </Label>
              <Textarea
                id="policyText"
                rows={5}
                value={policyText}
                onChange={(event) => setPolicyText(event.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                This policy is shown to all administrators during onboarding and when their privileges change.
              </p>
            </div>

            <Button className="gap-2">
              <Save className="h-4 w-4" />
              Save authentication settings
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg font-semibold">
              <Clock className="h-5 w-5 text-muted-foreground" />
              Session controls
            </CardTitle>
            <CardDescription>Limit how long administrator sessions remain active.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="sessionTimeout" className="text-sm font-semibold text-foreground">
                Session timeout (minutes)
              </Label>
              <Input
                id="sessionTimeout"
                type="number"
                min={5}
                max={240}
                value={sessionTimeout}
                onChange={(event) => setSessionTimeout(Number(event.target.value))}
              />
              <p className="text-xs text-muted-foreground">
                After this window of inactivity users will be signed out and must reauthenticate.
              </p>
            </div>

            <div className="flex items-start justify-between gap-4 rounded-lg border border-border bg-card px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-foreground">Notify when privileged sessions extend</p>
                <p className="text-xs text-muted-foreground">
                  Sends a webhook and email to the compliance team when an administrator session exceeds the standard length.
                </p>
              </div>
              <Switch
                checked={notifyOnChanges}
                onCheckedChange={setNotifyOnChanges}
                aria-label="Toggle notifications on extended sessions"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="webhook" className="text-sm font-semibold text-foreground">
                Security webhook endpoint
              </Label>
              <Input
                id="webhook"
                type="url"
                value={webhookUrl}
                onChange={(event) => setWebhookUrl(event.target.value)}
                placeholder="https://hooks.example.com/admin-events"
              />
              <p className="text-xs text-muted-foreground">
                DotMac will deliver signed JSON payloads to this URL when critical admin actions occur.
              </p>
            </div>

            <Button className="gap-2" variant="outline">
              <Bell className="h-4 w-4" />
              Send test notification
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
