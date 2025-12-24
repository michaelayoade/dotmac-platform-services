import type { Meta, StoryObj } from "@storybook/react";
import { KPITile, KPIGrid } from "./KPITile";

const meta: Meta<typeof KPITile> = {
  title: "Dashboards/KPITile",
  component: KPITile,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component:
          "KPI tile component for displaying key metrics with trend indicators.",
      },
    },
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof KPITile>;

export const Basic: Story = {
  args: {
    title: "Total Revenue",
    value: "$45,231.89",
  },
};

export const WithIncrease: Story = {
  args: {
    title: "Total Revenue",
    value: "$45,231.89",
    change: 20.1,
    changeType: "increase",
    changeLabel: "from last month",
  },
};

export const WithDecrease: Story = {
  args: {
    title: "Churn Rate",
    value: "2.4%",
    change: -0.5,
    changeType: "decrease",
    changeLabel: "from last month",
  },
};

export const WithIcon: Story = {
  args: {
    title: "Active Users",
    value: "12,234",
    change: 19.5,
    changeType: "increase",
    icon: (
      <svg
        className="w-5 h-5 text-blue-600"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
        />
      </svg>
    ),
  },
};

export const WithSparkline: Story = {
  args: {
    title: "Page Views",
    value: "89,234",
    change: 12.3,
    changeType: "increase",
    sparklineData: [30, 40, 35, 50, 49, 60, 70, 91, 80],
  },
};

export const LoadingState: Story = {
  args: {
    title: "Loading Metric",
    value: "",
    loading: true,
  },
};

export const KPIGridExample: Story = {
  render: () => (
    <KPIGrid columns={4}>
      <KPITile
        title="Total Revenue"
        value="$45,231.89"
        change={20.1}
        changeType="increase"
        changeLabel="from last month"
      />
      <KPITile
        title="Subscriptions"
        value="+2,350"
        change={180.1}
        changeType="increase"
        changeLabel="from last month"
      />
      <KPITile
        title="Active Users"
        value="12,234"
        change={19}
        changeType="increase"
        changeLabel="from last month"
      />
      <KPITile
        title="Churn Rate"
        value="2.4%"
        change={-0.5}
        changeType="decrease"
        changeLabel="from last month"
      />
    </KPIGrid>
  ),
};

export const ResponsiveGrid: Story = {
  render: () => (
    <KPIGrid>
      <KPITile
        title="Revenue"
        value="$45,231"
        change={20.1}
        changeType="increase"
        icon={
          <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
      />
      <KPITile
        title="Orders"
        value="1,234"
        change={12.5}
        changeType="increase"
        icon={
          <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
        }
      />
      <KPITile
        title="Customers"
        value="8,923"
        change={8.2}
        changeType="increase"
        icon={
          <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        }
      />
      <KPITile
        title="Bounce Rate"
        value="32.4%"
        change={-2.1}
        changeType="decrease"
        icon={
          <svg className="w-5 h-5 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        }
      />
    </KPIGrid>
  ),
};

export const DifferentSizes: Story = {
  render: () => (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-gray-500">Default Size</h3>
      <KPITile
        title="Revenue"
        value="$45,231"
        change={20.1}
        changeType="increase"
      />
      <h3 className="text-sm font-medium text-gray-500 mt-6">Compact Size</h3>
      <KPITile
        title="Revenue"
        value="$45,231"
        change={20.1}
        changeType="increase"
        size="compact"
      />
    </div>
  ),
};
