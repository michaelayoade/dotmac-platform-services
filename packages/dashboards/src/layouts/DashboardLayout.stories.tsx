import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { DashboardLayout, DashboardSection } from "./DashboardLayout";
import { KPITile, KPIGrid } from "../components/KPITile";
import { FilterBar, type FilterConfig, type FilterValues } from "../components/FilterBar";
import { ChartGrid, ChartCard } from "../components/ChartGrid";

const meta: Meta<typeof DashboardLayout> = {
  title: "Dashboards/DashboardLayout",
  component: DashboardLayout,
  parameters: {
    layout: "fullscreen",
    docs: {
      description: {
        component:
          "A complete dashboard layout component with header, filters, and content sections.",
      },
    },
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof DashboardLayout>;

const filterConfig: FilterConfig[] = [
  {
    id: "status",
    label: "Status",
    type: "select",
    options: [
      { value: "all", label: "All Status" },
      { value: "active", label: "Active" },
      { value: "inactive", label: "Inactive" },
      { value: "pending", label: "Pending" },
    ],
  },
  {
    id: "department",
    label: "Department",
    type: "select",
    options: [
      { value: "all", label: "All Departments" },
      { value: "engineering", label: "Engineering" },
      { value: "marketing", label: "Marketing" },
      { value: "sales", label: "Sales" },
    ],
  },
  {
    id: "dateRange",
    label: "Date",
    type: "date",
  },
];

export const Basic: Story = {
  render: () => (
    <DashboardLayout title="Dashboard" subtitle="Overview of your business metrics">
      <DashboardSection>
        <p className="text-gray-600">Dashboard content goes here...</p>
      </DashboardSection>
    </DashboardLayout>
  ),
};

export const WithFilters: Story = {
  render: () => {
    const DashboardWithFilters = () => {
      const [filterValues, setFilterValues] = useState<FilterValues>({});
      const [searchValue, setSearchValue] = useState("");

      return (
        <DashboardLayout
          title="Analytics Dashboard"
          subtitle="Real-time insights into your business"
          filters={
            <FilterBar
              filters={filterConfig}
              values={filterValues}
              onChange={setFilterValues}
              searchValue={searchValue}
              onSearchChange={setSearchValue}
            />
          }
        >
          <DashboardSection>
            <p className="text-gray-600">Dashboard content with filters...</p>
          </DashboardSection>
        </DashboardLayout>
      );
    };

    return <DashboardWithFilters />;
  },
};

export const WithKPIs: Story = {
  render: () => (
    <DashboardLayout title="Sales Dashboard" subtitle="Monthly performance overview">
      <KPIGrid columns={4}>
        <KPITile
          title="Total Revenue"
          value="$45,231"
          change={20.1}
          changeType="increase"
          changeLabel="from last month"
        />
        <KPITile
          title="New Customers"
          value="+2,350"
          change={18.2}
          changeType="increase"
          changeLabel="from last month"
        />
        <KPITile
          title="Active Users"
          value="12,234"
          change={4.1}
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
    </DashboardLayout>
  ),
};

export const WithCharts: Story = {
  render: () => (
    <DashboardLayout title="Analytics" subtitle="Data visualization dashboard">
      <KPIGrid columns={3} className="mb-6">
        <KPITile title="Revenue" value="$45,231" change={20.1} changeType="increase" />
        <KPITile title="Users" value="12,234" change={4.1} changeType="increase" />
        <KPITile title="Conversion" value="3.2%" change={-0.3} changeType="decrease" />
      </KPIGrid>

      <ChartGrid columns={2}>
        <ChartCard title="Revenue Over Time" subtitle="Monthly revenue for 2024">
          <div className="h-full flex items-center justify-center bg-gray-50 rounded">
            <span className="text-gray-400">[Line Chart]</span>
          </div>
        </ChartCard>
        <ChartCard title="Traffic Sources" subtitle="Breakdown by channel">
          <div className="h-full flex items-center justify-center bg-gray-50 rounded">
            <span className="text-gray-400">[Pie Chart]</span>
          </div>
        </ChartCard>
        <ChartCard title="User Growth" subtitle="New vs returning users" fullWidth>
          <div className="h-full flex items-center justify-center bg-gray-50 rounded">
            <span className="text-gray-400">[Area Chart]</span>
          </div>
        </ChartCard>
      </ChartGrid>
    </DashboardLayout>
  ),
};

export const WithSections: Story = {
  render: () => (
    <DashboardLayout title="Operations Dashboard">
      <DashboardSection title="Overview" description="Key metrics at a glance">
        <KPIGrid columns={4}>
          <KPITile title="Active Jobs" value="234" change={12} changeType="increase" />
          <KPITile title="Completed" value="1,892" change={8.5} changeType="increase" />
          <KPITile title="Pending" value="45" change={-3.2} changeType="decrease" />
          <KPITile title="Failed" value="7" change={2} changeType="increase" />
        </KPIGrid>
      </DashboardSection>

      <DashboardSection title="Recent Activity" description="Latest system events">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <ul className="divide-y divide-gray-100">
            {[1, 2, 3, 4, 5].map((i) => (
              <li key={i} className="py-3 flex justify-between">
                <span className="text-gray-700">Event {i}</span>
                <span className="text-gray-400 text-sm">2 min ago</span>
              </li>
            ))}
          </ul>
        </div>
      </DashboardSection>
    </DashboardLayout>
  ),
};

export const WithHeaderActions: Story = {
  render: () => (
    <DashboardLayout
      title="Team Dashboard"
      subtitle="Manage your team's performance"
      headerActions={
        <div className="flex gap-2">
          <button className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
            Export
          </button>
          <button className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700">
            Add Member
          </button>
        </div>
      }
    >
      <DashboardSection>
        <p className="text-gray-600">Team content...</p>
      </DashboardSection>
    </DashboardLayout>
  ),
};

export const FullExample: Story = {
  render: () => {
    const FullDashboard = () => {
      const [filterValues, setFilterValues] = useState<FilterValues>({});
      const [searchValue, setSearchValue] = useState("");

      return (
        <DashboardLayout
          title="Business Dashboard"
          subtitle="Complete overview of your operations"
          filters={
            <FilterBar
              filters={filterConfig}
              values={filterValues}
              onChange={setFilterValues}
              searchValue={searchValue}
              onSearchChange={setSearchValue}
              actions={
                <button className="px-3 py-1.5 text-sm text-blue-600 hover:text-blue-800">
                  Save View
                </button>
              }
            />
          }
          headerActions={
            <div className="flex gap-2">
              <button className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 text-sm">
                Export PDF
              </button>
              <button className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 text-sm">
                Schedule Report
              </button>
            </div>
          }
        >
          {/* KPIs */}
          <KPIGrid columns={4} className="mb-6">
            <KPITile
              title="Total Revenue"
              value="$245,890"
              change={23.5}
              changeType="increase"
              changeLabel="vs last month"
            />
            <KPITile
              title="Active Customers"
              value="8,234"
              change={12.3}
              changeType="increase"
              changeLabel="vs last month"
            />
            <KPITile
              title="Avg Order Value"
              value="$156.32"
              change={-2.1}
              changeType="decrease"
              changeLabel="vs last month"
            />
            <KPITile
              title="Net Promoter Score"
              value="72"
              change={5}
              changeType="increase"
              changeLabel="vs last month"
            />
          </KPIGrid>

          {/* Charts Section */}
          <DashboardSection title="Performance Trends" className="mb-6">
            <ChartGrid columns={2}>
              <ChartCard title="Revenue Trend" subtitle="Last 12 months">
                <div className="h-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100 rounded">
                  <span className="text-blue-400">[Revenue Line Chart]</span>
                </div>
              </ChartCard>
              <ChartCard title="Customer Acquisition" subtitle="By channel">
                <div className="h-full flex items-center justify-center bg-gradient-to-br from-green-50 to-green-100 rounded">
                  <span className="text-green-400">[Acquisition Bar Chart]</span>
                </div>
              </ChartCard>
            </ChartGrid>
          </DashboardSection>

          {/* Bottom Section */}
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2">
              <DashboardSection title="Recent Orders">
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Order
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Customer
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Amount
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {[
                        { id: "#1234", customer: "John Doe", amount: "$250.00", status: "Completed" },
                        { id: "#1235", customer: "Jane Smith", amount: "$120.00", status: "Processing" },
                        { id: "#1236", customer: "Bob Wilson", amount: "$450.00", status: "Completed" },
                      ].map((order) => (
                        <tr key={order.id}>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {order.id}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{order.customer}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{order.amount}</td>
                          <td className="px-4 py-3 text-sm">
                            <span
                              className={`px-2 py-1 rounded-full text-xs ${
                                order.status === "Completed"
                                  ? "bg-green-100 text-green-800"
                                  : "bg-yellow-100 text-yellow-800"
                              }`}
                            >
                              {order.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </DashboardSection>
            </div>
            <div>
              <DashboardSection title="Quick Stats">
                <div className="space-y-4">
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <h4 className="text-sm font-medium text-gray-500">Top Product</h4>
                    <p className="text-lg font-semibold text-gray-900">Premium Plan</p>
                    <p className="text-sm text-gray-500">$12,450 revenue</p>
                  </div>
                  <div className="bg-white rounded-lg border border-gray-200 p-4">
                    <h4 className="text-sm font-medium text-gray-500">Top Region</h4>
                    <p className="text-lg font-semibold text-gray-900">North America</p>
                    <p className="text-sm text-gray-500">42% of total sales</p>
                  </div>
                </div>
              </DashboardSection>
            </div>
          </div>
        </DashboardLayout>
      );
    };

    return <FullDashboard />;
  },
};
