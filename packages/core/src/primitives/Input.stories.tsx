import type { Meta, StoryObj } from "@storybook/react";
import { Input } from "./Input";

const meta: Meta<typeof Input> = {
  title: "Core/Primitives/Input",
  component: Input,
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component:
          "A form input component with variants for different states and sizes.",
      },
    },
  },
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "error", "success"],
    },
    inputSize: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
    disabled: {
      control: "boolean",
    },
  },
};

export default meta;
type Story = StoryObj<typeof Input>;

export const Default: Story = {
  args: {
    placeholder: "Enter text...",
  },
};

export const WithLabel: Story = {
  render: () => (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">Email</label>
      <Input type="email" placeholder="you@example.com" />
    </div>
  ),
};

export const Error: Story = {
  render: () => (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">Email</label>
      <Input
        type="email"
        placeholder="you@example.com"
        variant="error"
        defaultValue="invalid-email"
      />
      <p className="text-sm text-red-500">Please enter a valid email address</p>
    </div>
  ),
};

export const Success: Story = {
  render: () => (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">Username</label>
      <Input
        placeholder="username"
        variant="success"
        defaultValue="johndoe123"
      />
      <p className="text-sm text-green-500">Username is available</p>
    </div>
  ),
};

export const Disabled: Story = {
  args: {
    placeholder: "Disabled input",
    disabled: true,
    defaultValue: "Cannot edit this",
  },
};

export const Sizes: Story = {
  render: () => (
    <div className="space-y-4 w-80">
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">Small</label>
        <Input inputSize="sm" placeholder="Small input" />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">Medium</label>
        <Input inputSize="md" placeholder="Medium input" />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">Large</label>
        <Input inputSize="lg" placeholder="Large input" />
      </div>
    </div>
  ),
};

export const InputTypes: Story = {
  render: () => (
    <div className="space-y-4 w-80">
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">Text</label>
        <Input type="text" placeholder="Enter text" />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">Email</label>
        <Input type="email" placeholder="you@example.com" />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">Password</label>
        <Input type="password" placeholder="••••••••" />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">Number</label>
        <Input type="number" placeholder="0" />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-700">Date</label>
        <Input type="date" />
      </div>
    </div>
  ),
};
