import type { Meta, StoryObj } from "@storybook/react";
import { LineChart } from "./LineChart";

const meta: Meta<typeof LineChart> = {
  title: "Charts/LineChart",
  component: LineChart,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component:
          "A line chart component for visualizing trends and time series data.",
      },
    },
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof LineChart>;

const monthlyData = [
  { month: "Jan", revenue: 4000, expenses: 2400 },
  { month: "Feb", revenue: 3000, expenses: 1398 },
  { month: "Mar", revenue: 5000, expenses: 3800 },
  { month: "Apr", revenue: 4780, expenses: 2908 },
  { month: "May", revenue: 5890, expenses: 4800 },
  { month: "Jun", revenue: 4390, expenses: 3800 },
  { month: "Jul", revenue: 6490, expenses: 4300 },
];

export const Basic: Story = {
  args: {
    data: monthlyData,
    xKey: "month",
    series: [{ dataKey: "revenue", name: "Revenue" }],
    height: 300,
  },
};

export const MultipleSeries: Story = {
  args: {
    data: monthlyData,
    xKey: "month",
    series: [
      { dataKey: "revenue", name: "Revenue", color: "#3b82f6" },
      { dataKey: "expenses", name: "Expenses", color: "#ef4444" },
    ],
    height: 300,
  },
};

export const WithGrid: Story = {
  args: {
    data: monthlyData,
    xKey: "month",
    series: [{ dataKey: "revenue", name: "Revenue" }],
    height: 300,
    showGrid: true,
  },
};

export const WithLegend: Story = {
  args: {
    data: monthlyData,
    xKey: "month",
    series: [
      { dataKey: "revenue", name: "Revenue" },
      { dataKey: "expenses", name: "Expenses" },
    ],
    height: 300,
    showLegend: true,
  },
};

export const WithTooltip: Story = {
  args: {
    data: monthlyData,
    xKey: "month",
    series: [
      { dataKey: "revenue", name: "Revenue" },
      { dataKey: "expenses", name: "Expenses" },
    ],
    height: 300,
    showTooltip: true,
    tooltipFormatter: (value: number) =>
      new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(value),
  },
};

export const CustomColors: Story = {
  args: {
    data: monthlyData,
    xKey: "month",
    series: [
      { dataKey: "revenue", name: "Revenue", color: "#10b981" },
      { dataKey: "expenses", name: "Expenses", color: "#f59e0b" },
    ],
    height: 300,
    showLegend: true,
  },
};

export const Curved: Story = {
  args: {
    data: monthlyData,
    xKey: "month",
    series: [{ dataKey: "revenue", name: "Revenue" }],
    height: 300,
    curveType: "monotone",
  },
};

export const WithDots: Story = {
  args: {
    data: monthlyData,
    xKey: "month",
    series: [{ dataKey: "revenue", name: "Revenue" }],
    height: 300,
    showDots: true,
  },
};

export const FullFeatured: Story = {
  render: () => (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Revenue vs Expenses
        </h3>
        <p className="text-sm text-gray-500">Monthly comparison for 2024</p>
      </div>
      <LineChart
        data={monthlyData}
        xKey="month"
        series={[
          { dataKey: "revenue", name: "Revenue", color: "#3b82f6" },
          { dataKey: "expenses", name: "Expenses", color: "#ef4444" },
        ]}
        height={350}
        showGrid
        showLegend
        showTooltip
        showDots
        curveType="monotone"
        tooltipFormatter={(value) =>
          new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
          }).format(value as number)
        }
      />
    </div>
  ),
};
