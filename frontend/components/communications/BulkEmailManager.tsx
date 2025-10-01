/**
 * Bulk Email Campaign Manager Component
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, Upload, Send, Clock, CheckCircle, XCircle, Pause } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface EmailTemplate {
  id: string;
  name: string;
  subject_template: string;
  variables: {
    all_variables: string[];
  };
}

interface BulkEmailJob {
  id: string;
  name: string;
  template_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  error_message?: string;
  scheduled_at?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  progress_percentage: number;
}

interface RecipientData {
  email: string;
  name?: string;
  custom_data?: Record<string, any>;
}

const StatusIcon = ({ status }: { status: BulkEmailJob['status'] }) => {
  switch (status) {
    case 'queued':
      return <Clock className="w-4 h-4 text-yellow-500" />;
    case 'processing':
      return <Send className="w-4 h-4 text-blue-500" />;
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'cancelled':
      return <Pause className="w-4 h-4 text-gray-500" />;
    default:
      return null;
  }
};

const StatusBadge = ({ status }: { status: BulkEmailJob['status'] }) => {
  const variants = {
    queued: 'secondary',
    processing: 'default',
    completed: 'default',
    failed: 'destructive',
    cancelled: 'secondary',
  } as const;

  return (
    <Badge variant={variants[status]} className="capitalize">
      {status}
    </Badge>
  );
};

export const BulkEmailManager: React.FC = () => {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [jobs, setJobs] = useState<BulkEmailJob[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    template_id: '',
    recipients_csv: '',
    template_data: '{}',
  });

  // Fetch data on component mount
  useEffect(() => {
    fetchData();
  }, []);

  // Polling for job updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchJobs();
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      await Promise.all([fetchTemplates(), fetchJobs()]);
    } catch (err) {
      setError('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    const response = await fetch('/api/communications/templates?is_active=true');
    if (!response.ok) throw new Error('Failed to fetch templates');
    const data = await response.json();
    setTemplates(data);
  };

  const fetchJobs = async () => {
    const response = await fetch('/api/communications/bulk-jobs');
    if (!response.ok) throw new Error('Failed to fetch jobs');
    const data = await response.json();
    setJobs(data);
  };

  const handleCreate = () => {
    setIsCreating(true);
    setFormData({
      name: '',
      template_id: '',
      recipients_csv: '',
      template_data: '{}',
    });
  };

  const parseRecipientsCSV = (csvText: string): RecipientData[] => {
    const lines = csvText.trim().split('\n');
    if (lines.length === 0) return [];

    const headers = lines[0].split(',').map(h => h.trim());
    const recipients: RecipientData[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      if (values.length !== headers.length) continue;

      const recipient: RecipientData = {
        email: '',
        custom_data: {},
      };

      headers.forEach((header, index) => {
        const value = values[index];
        if (header.toLowerCase() === 'email') {
          recipient.email = value;
        } else if (header.toLowerCase() === 'name') {
          recipient.name = value;
        } else {
          if (!recipient.custom_data) recipient.custom_data = {};
          recipient.custom_data[header] = value;
        }
      });

      if (recipient.email) {
        recipients.push(recipient);
      }
    }

    return recipients;
  };

  const handleSubmit = async () => {
    try {
      const recipients = parseRecipientsCSV(formData.recipients_csv);
      if (recipients.length === 0) {
        throw new Error('No valid recipients found in CSV data');
      }

      let templateData = {};
      try {
        templateData = JSON.parse(formData.template_data);
      } catch {
        throw new Error('Invalid JSON in template data');
      }

      const response = await fetch('/api/communications/bulk-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          template_id: formData.template_id,
          recipients,
          template_data: templateData,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create bulk job');
      }

      await fetchJobs();
      setIsCreating(false);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create bulk job');
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setError(null);
  };

  const handleCancelJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to cancel this job?')) {
      return;
    }

    try {
      const response = await fetch(`/api/communications/bulk-jobs/${jobId}/cancel`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to cancel job');

      await fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">Loading bulk email campaigns...</div>
        </CardContent>
      </Card>
    );
  }

  const selectedTemplate = templates.find(t => t.id === formData.template_id);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Bulk Email Campaigns</h2>
        <Button onClick={handleCreate} disabled={isCreating}>
          <Send className="w-4 h-4 mr-2" />
          New Campaign
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {isCreating && (
        <Card>
          <CardHeader>
            <CardTitle>Create Bulk Email Campaign</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Campaign Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Campaign name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Email Template</label>
                <Select
                  value={formData.template_id}
                  onValueChange={(value) => setFormData({...formData, template_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select template" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((template) => (
                      <SelectItem key={template.id} value={template.id}>
                        {template.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {selectedTemplate && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Template variables:</strong> {selectedTemplate.variables.all_variables.join(', ') || 'None'}
                  <br />
                  <strong>Subject:</strong> {selectedTemplate.subject_template}
                </AlertDescription>
              </Alert>
            )}

            <div>
              <label className="block text-sm font-medium mb-2">
                Recipients CSV Data
                <span className="text-xs text-gray-500 block">
                  Format: email,name,custom_field1,custom_field2...
                </span>
              </label>
              <Textarea
                value={formData.recipients_csv}
                onChange={(e) => setFormData({...formData, recipients_csv: e.target.value})}
                placeholder={`email,name,department
user1@example.com,John Doe,Engineering
user2@example.com,Jane Smith,Marketing`}
                rows={8}
                className="font-mono text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Global Template Data (JSON)
                <span className="text-xs text-gray-500 block">
                  Variables available to all recipients
                </span>
              </label>
              <Textarea
                value={formData.template_data}
                onChange={(e) => setFormData({...formData, template_data: e.target.value})}
                placeholder='{"company_name": "ACME Corp", "support_email": "support@acme.com"}'
                rows={3}
                className="font-mono text-sm"
              />
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button onClick={handleSubmit}>
                Create Campaign
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {jobs.map((job) => (
          <Card key={job.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <StatusIcon status={job.status} />
                    <h3 className="font-semibold">{job.name}</h3>
                    <StatusBadge status={job.status} />
                  </div>

                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Recipients:</strong> {job.total_recipients.toLocaleString()}</p>
                    <p><strong>Sent:</strong> {job.sent_count.toLocaleString()} | <strong>Failed:</strong> {job.failed_count.toLocaleString()}</p>
                    <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
                    {job.started_at && (
                      <p><strong>Started:</strong> {new Date(job.started_at).toLocaleString()}</p>
                    )}
                    {job.completed_at && (
                      <p><strong>Completed:</strong> {new Date(job.completed_at).toLocaleString()}</p>
                    )}
                  </div>

                  {job.error_message && (
                    <Alert variant="destructive" className="mt-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{job.error_message}</AlertDescription>
                    </Alert>
                  )}
                </div>

                <div className="flex flex-col items-end space-y-2">
                  {job.status === 'processing' && (
                    <div className="w-32">
                      <Progress value={job.progress_percentage} className="mb-1" />
                      <p className="text-xs text-gray-500 text-center">
                        {Math.round(job.progress_percentage)}%
                      </p>
                    </div>
                  )}

                  {(job.status === 'queued' || job.status === 'processing') && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCancelJob(job.id)}
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              </div>

              {job.status === 'completed' && (
                <div className="bg-green-50 p-3 rounded-md">
                  <p className="text-sm text-green-800">
                    Campaign completed successfully!
                    {job.sent_count > 0 && ` ${job.sent_count} emails sent.`}
                    {job.failed_count > 0 && ` ${job.failed_count} failed.`}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {jobs.length === 0 && !isCreating && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-gray-500 mb-4">No bulk email campaigns found</p>
            <Button onClick={handleCreate}>
              <Send className="w-4 h-4 mr-2" />
              Create Your First Campaign
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};