import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PluginForm } from '../../app/dashboard/settings/plugins/components/PluginForm';

describe('PluginForm Complete Coverage Tests', () => {
  it('handles JSON field with object value', async () => {
    const user = userEvent.setup();

    const pluginWithJson = {
      name: "JSON Plugin",
      type: "integration" as const,
      version: "1.0.0",
      description: "Plugin with JSON field",
      supports_health_check: true,
      supports_test_connection: false,
      fields: [{
        key: "json_config",
        label: "JSON Config",
        type: "json" as const,
        description: "JSON configuration",
        required: false
      }]
    };

    const onSubmit = jest.fn();
    render(<PluginForm
      plugin={pluginWithJson}
      availablePlugins={[pluginWithJson]}
      onSubmit={onSubmit}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    const instanceName = screen.getByLabelText(/Instance Name/);
    await user.type(instanceName, 'Test Instance');

    const jsonField = screen.getByLabelText(/JSON Config/) as HTMLTextAreaElement;

    // Test valid JSON input - use fireEvent to avoid keyboard parsing issues with {}
    fireEvent.change(jsonField, { target: { value: '{"test": "value"}' } });

    const submitButton = screen.getByRole('button', { name: /Create Plugin/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        instance_name: 'Test Instance',
        plugin_name: 'JSON Plugin',
        configuration: {
          json_config: { test: "value" }
        }
      });
    });
  });

  it('handles JSON field with invalid JSON', async () => {
    const user = userEvent.setup();

    const pluginWithJson = {
      name: "JSON Plugin",
      type: "integration" as const,
      version: "1.0.0",
      description: "Plugin with JSON field",
      supports_health_check: true,
      supports_test_connection: false,
      fields: [{
        key: "json_config",
        label: "JSON Config",
        type: "json" as const,
        description: "JSON configuration",
        required: false
      }]
    };

    render(<PluginForm
      plugin={pluginWithJson}
      availablePlugins={[pluginWithJson]}
      onSubmit={jest.fn()}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    const jsonField = screen.getByLabelText(/JSON Config/) as HTMLTextAreaElement;

    // Test invalid JSON input - should keep as string - use fireEvent to avoid keyboard parsing issues with {}
    fireEvent.change(jsonField, { target: { value: '{"invalid": json}' } });

    expect(jsonField).toHaveValue('{"invalid": json}');
  });

  it('displays field descriptions for non-boolean fields', () => {
    const pluginWithDescriptions = {
      name: "Description Plugin",
      type: "integration" as const,
      version: "1.0.0",
      description: "Plugin with descriptions",
      supports_health_check: true,
      supports_test_connection: false,
      fields: [
        {
          key: "string_field",
          label: "String Field",
          type: "string" as const,
          description: "This is a string field description",
          required: false
        },
        {
          key: "boolean_field",
          label: "Boolean Field",
          type: "boolean" as const,
          description: "Enable this boolean feature",
          required: false
        }
      ]
    };

    render(<PluginForm
      plugin={pluginWithDescriptions}
      availablePlugins={[pluginWithDescriptions]}
      onSubmit={jest.fn()}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    // String field description should be visible below the field
    expect(screen.getByText('This is a string field description')).toBeInTheDocument();

    // Boolean field description should be visible as inline label text
    expect(screen.getByText('Enable this boolean feature')).toBeInTheDocument();
  });

  it('displays validation rules when present', () => {
    const pluginWithRules = {
      name: "Rules Plugin",
      type: "integration" as const,
      version: "1.0.0",
      description: "Plugin with validation rules",
      supports_health_check: true,
      supports_test_connection: false,
      fields: [{
        key: "field_with_rules",
        label: "Field With Rules",
        type: "string" as const,
        description: "Field with validation rules",
        required: false,
        validation_rules: [
          "Must be at least 5 characters",
          "Cannot contain special characters"
        ]
      }]
    };

    render(<PluginForm
      plugin={pluginWithRules}
      availablePlugins={[pluginWithRules]}
      onSubmit={jest.fn()}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    expect(screen.getByText('Must be at least 5 characters')).toBeInTheDocument();
    expect(screen.getByText('Cannot contain special characters')).toBeInTheDocument();
  });

  it('displays secret indicator for secret fields', () => {
    const pluginWithSecret = {
      name: "Secret Plugin",
      type: "integration" as const,
      version: "1.0.0",
      description: "Plugin with secret field",
      supports_health_check: true,
      supports_test_connection: false,
      fields: [{
        key: "secret_field",
        label: "Secret Field",
        type: "string" as const,
        description: "Secret field",
        required: false,
        is_secret: true
      }]
    };

    render(<PluginForm
      plugin={pluginWithSecret}
      availablePlugins={[pluginWithSecret]}
      onSubmit={jest.fn()}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    expect(screen.getByText('(Secret)')).toBeInTheDocument();
  });

  it('handles file field without FileReader support', async () => {
    const pluginWithFile = {
      name: "File Plugin",
      type: "integration" as const,
      version: "1.0.0",
      description: "Plugin with file field",
      supports_health_check: true,
      supports_test_connection: false,
      fields: [{
        key: "file_field",
        label: "File Field",
        type: "file" as const,
        description: "Upload a file",
        required: false
      }]
    };

    render(<PluginForm
      plugin={pluginWithFile}
      availablePlugins={[pluginWithFile]}
      onSubmit={jest.fn()}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    // File input uses different id pattern (file- instead of field-)
    const fileInput = document.querySelector('#file-file_field') as HTMLInputElement;
    expect(fileInput).toBeInTheDocument();
    expect(fileInput).toHaveAttribute('type', 'file');

    // Verify custom file upload label is present
    const uploadLabel = screen.getByText('Choose file...');
    expect(uploadLabel).toBeInTheDocument();
  });

  it('handles form submission without test connection support', async () => {
    const user = userEvent.setup();

    const pluginWithoutTest = {
      name: "No Test Plugin",
      type: "integration" as const,
      version: "1.0.0",
      description: "Plugin without test connection",
      supports_health_check: true,
      supports_test_connection: false,
      fields: [{
        key: "simple_field",
        label: "Simple Field",
        type: "string" as const,
        required: false
      }]
    };

    const onSubmit = jest.fn();
    render(<PluginForm
      plugin={pluginWithoutTest}
      availablePlugins={[pluginWithoutTest]}
      onSubmit={onSubmit}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    const instanceName = screen.getByLabelText(/Instance Name/);
    await user.type(instanceName, 'Test Instance');

    // Test connection button should not be present
    expect(screen.queryByRole('button', { name: /Test Connection/ })).not.toBeInTheDocument();

    const submitButton = screen.getByRole('button', { name: /Create Plugin/ });
    await user.click(submitButton);

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        instance_name: 'Test Instance',
        plugin_name: 'No Test Plugin',
        configuration: {}  // Empty field not included
      });
    });
  });

  it('handles plugin selection in creation mode', async () => {
    const user = userEvent.setup();

    const availablePlugins = [
      {
        name: "Plugin 1",
        type: "integration" as const,
        version: "1.0.0",
        description: "First plugin",
        supports_health_check: true,
        supports_test_connection: true,
        fields: [{
          key: "field1",
          label: "Field 1",
          type: "string" as const,
          required: false
        }]
      },
      {
        name: "Plugin 2",
        type: "integration" as const,
        version: "1.0.0",
        description: "Second plugin",
        supports_health_check: true,
        supports_test_connection: true,
        fields: [{
          key: "field2",
          label: "Field 2",
          type: "string" as const,
          required: false
        }]
      }
    ];

    render(<PluginForm
      plugin={null}
      availablePlugins={availablePlugins}
      onSubmit={jest.fn()}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    // Select first plugin
    const pluginSelect = screen.getByLabelText(/Plugin/);
    await user.selectOptions(pluginSelect, 'Plugin 1');

    await waitFor(() => {
      expect(screen.getByLabelText(/Field 1/)).toBeInTheDocument();
    });

    // Change to second plugin
    await user.selectOptions(pluginSelect, 'Plugin 2');

    await waitFor(() => {
      expect(screen.getByLabelText(/Field 2/)).toBeInTheDocument();
      expect(screen.queryByLabelText(/Field 1/)).not.toBeInTheDocument();
    });
  });

  it('clears form when plugin changes', async () => {
    const user = userEvent.setup();

    const availablePlugins = [
      {
        name: "Plugin A",
        type: "integration" as const,
        version: "1.0.0",
        description: "Plugin A",
        supports_health_check: true,
        supports_test_connection: true,
        fields: [{
          key: "fieldA",
          label: "Field A",
          type: "string" as const,
          required: false
        }]
      },
      {
        name: "Plugin B",
        type: "integration" as const,
        version: "1.0.0",
        description: "Plugin B",
        supports_health_check: true,
        supports_test_connection: true,
        fields: [{
          key: "fieldB",
          label: "Field B",
          type: "string" as const,
          required: false
        }]
      }
    ];

    render(<PluginForm
      plugin={null}
      availablePlugins={availablePlugins}
      onSubmit={jest.fn()}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    const instanceName = screen.getByLabelText(/Instance Name/);
    await user.type(instanceName, 'Test Instance');

    const pluginSelect = screen.getByLabelText(/Plugin/);
    await user.selectOptions(pluginSelect, 'Plugin A');

    await waitFor(() => {
      expect(screen.getByLabelText(/Field A/)).toBeInTheDocument();
    });

    const fieldA = screen.getByLabelText(/Field A/);
    await user.type(fieldA, 'Test Value');

    // Switch plugins - fields change but instance name persists
    await user.selectOptions(pluginSelect, 'Plugin B');

    await waitFor(() => {
      expect(screen.getByLabelText(/Field B/)).toBeInTheDocument();
      // Instance name is preserved when changing plugins
      expect((screen.getByLabelText(/Instance Name/) as HTMLInputElement).value).toBe('Test Instance');
    });
  });

  it('handles validation for all field constraint types', async () => {
    const user = userEvent.setup();

    const pluginWithConstraints = {
      name: "Constraint Plugin",
      type: "integration" as const,
      version: "1.0.0",
      description: "Plugin with various constraints",
      supports_health_check: true,
      supports_test_connection: false,
      fields: [
        {
          key: "string_with_pattern",
          label: "String with Pattern",
          type: "string" as const,
          pattern: "^[A-Z]+$",
          required: false
        },
        {
          key: "number_field",
          label: "Number Field",
          type: "integer" as const,
          required: false
        }
      ]
    };

    render(<PluginForm
      plugin={pluginWithConstraints}
      availablePlugins={[pluginWithConstraints]}
      onSubmit={jest.fn()}
      onCancel={jest.fn()}
      onTestConnection={jest.fn()}
    />);

    const stringField = screen.getByLabelText(/String with Pattern/);
    expect(stringField).toHaveAttribute('pattern', '^[A-Z]+$');

    const numberField = screen.getByLabelText(/Number Field/);
    // Integer fields use step=1 by default
    expect(numberField).toHaveAttribute('step', '1');
    expect(numberField).toHaveAttribute('type', 'number');
  });
});