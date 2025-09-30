/**
 * Email Template Manager Component
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Eye, Plus, Edit, Trash2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface EmailTemplate {
  id: string;
  name: string;
  description?: string;
  subject_template: string;
  html_template: string;
  text_template?: string;
  category?: string;
  is_active: boolean;
  variables: {
    all_variables: string[];
  };
  created_at: string;
  updated_at: string;
}

interface TemplateFormData {
  name: string;
  description: string;
  subject_template: string;
  html_template: string;
  text_template: string;
  category: string;
}

export const TemplateManager: React.FC = () => {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<EmailTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<TemplateFormData>({
    name: '',
    description: '',
    subject_template: '',
    html_template: '',
    text_template: '',
    category: '',
  });

  // Fetch templates on component mount
  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/communications/templates');
      if (!response.ok) throw new Error('Failed to fetch templates');
      const data = await response.json();
      setTemplates(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setIsCreating(true);
    setFormData({
      name: '',
      description: '',
      subject_template: '',
      html_template: '',
      text_template: '',
      category: '',
    });
  };

  const handleEdit = (template: EmailTemplate) => {
    setSelectedTemplate(template);
    setIsEditing(true);
    setFormData({
      name: template.name,
      description: template.description || '',
      subject_template: template.subject_template,
      html_template: template.html_template,
      text_template: template.text_template || '',
      category: template.category || '',
    });
  };

  const handlePreview = (template: EmailTemplate) => {
    setPreviewTemplate(template);
    setIsPreviewing(true);
  };

  const handleSave = async () => {
    try {
      const url = isEditing && selectedTemplate
        ? `/api/communications/templates/${selectedTemplate.id}`
        : '/api/communications/templates';

      const method = isEditing ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save template');
      }

      await fetchTemplates();
      setIsCreating(false);
      setIsEditing(false);
      setSelectedTemplate(null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save template');
    }
  };

  const handleDelete = async (template: EmailTemplate) => {
    if (!confirm(`Are you sure you want to delete "${template.name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/communications/templates/${template.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete template');

      await fetchTemplates();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete template');
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setIsEditing(false);
    setSelectedTemplate(null);
    setError(null);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">Loading templates...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Email Templates</h2>
        <Button onClick={handleCreate} disabled={isCreating || isEditing}>
          <Plus className="w-4 h-4 mr-2" />
          New Template
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {(isCreating || isEditing) && (
        <Card>
          <CardHeader>
            <CardTitle>
              {isCreating ? 'Create New Template' : 'Edit Template'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Template name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData({...formData, category: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="onboarding">Onboarding</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="transactional">Transactional</SelectItem>
                    <SelectItem value="notification">Notification</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Template description"
                rows={2}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Subject Template <span className="text-xs text-gray-500">(Supports Jinja2 variables: {{'{{'}}variable{{'}}'}})</span>
              </label>
              <Input
                value={formData.subject_template}
                onChange={(e) => setFormData({...formData, subject_template: e.target.value})}
                placeholder="Subject with {{variable}} placeholders"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">HTML Template</label>
              <Textarea
                value={formData.html_template}
                onChange={(e) => setFormData({...formData, html_template: e.target.value})}
                placeholder="HTML content with {{variable}} placeholders"
                rows={10}
                className="font-mono text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Text Template (Optional)</label>
              <Textarea
                value={formData.text_template}
                onChange={(e) => setFormData({...formData, text_template: e.target.value})}
                placeholder="Plain text version"
                rows={6}
              />
            </div>

            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button onClick={handleSave}>
                {isCreating ? 'Create Template' : 'Save Changes'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {templates.map((template) => (
          <Card key={template.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3 className="font-semibold">{template.name}</h3>
                    {template.category && (
                      <Badge variant="secondary">{template.category}</Badge>
                    )}
                    {!template.is_active && (
                      <Badge variant="destructive">Inactive</Badge>
                    )}
                  </div>

                  {template.description && (
                    <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                  )}

                  <div className="text-sm text-gray-500">
                    <p><strong>Subject:</strong> {template.subject_template}</p>
                    <p><strong>Variables:</strong> {template.variables.all_variables.join(', ') || 'None'}</p>
                    <p><strong>Created:</strong> {new Date(template.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePreview(template)}
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(template)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(template)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {templates.length === 0 && !isCreating && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-gray-500 mb-4">No email templates found</p>
            <Button onClick={handleCreate}>
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Template
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Preview Modal */}
      {isPreviewing && previewTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">Template Preview</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsPreviewing(false);
                    setPreviewTemplate(null);
                  }}
                >
                  ✕
                </Button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
              <div className="space-y-6">
                {/* Template Info */}
                <div>
                  <h3 className="text-lg font-semibold mb-2">{previewTemplate.name}</h3>
                  {previewTemplate.description && (
                    <p className="text-gray-600 mb-4">{previewTemplate.description}</p>
                  )}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {previewTemplate.category && (
                      <Badge variant="outline">{previewTemplate.category}</Badge>
                    )}
                    <Badge variant={previewTemplate.is_active ? "default" : "secondary"}>
                      {previewTemplate.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                </div>

                {/* Subject */}
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Subject</h4>
                  <div className="bg-gray-50 p-3 rounded-md font-mono text-sm">
                    {previewTemplate.subject_template}
                  </div>
                </div>

                {/* Variables */}
                {previewTemplate.variables.all_variables.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Template Variables</h4>
                    <div className="flex flex-wrap gap-2">
                      {previewTemplate.variables.all_variables.map((variable) => (
                        <span key={variable} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm font-mono">
                          {`{{${variable}}}`}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* HTML Template */}
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">HTML Template</h4>
                  <div className="border rounded-md p-4 bg-white">
                    {previewTemplate.html_template ? (
                      <div dangerouslySetInnerHTML={{ __html: previewTemplate.html_template }} />
                    ) : (
                      <p className="text-gray-500 italic">No HTML template defined</p>
                    )}
                  </div>
                </div>

                {/* Text Template */}
                {previewTemplate.text_template && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Text Template</h4>
                    <div className="bg-gray-50 p-3 rounded-md whitespace-pre-wrap font-mono text-sm">
                      {previewTemplate.text_template}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="p-4 border-t bg-gray-50">
              <div className="flex justify-end">
                <Button onClick={() => {
                  setIsPreviewing(false);
                  setPreviewTemplate(null);
                }}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};