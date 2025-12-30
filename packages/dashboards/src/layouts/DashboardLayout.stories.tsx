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
        <p className="text-text-muted">Dashboard content goes here...</p>
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
            <p className="text-text-muted">Dashboard content with filters...</p>
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
          title="New Tenants"
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
          <div className="h-full flex items-center justify-center bg-surface-overlay rounded">
            <span className="text-text-muted">[Line Chart]</span>
          </div>
        </ChartCard>
        <ChartCard title="Traffic Sources" subtitle="Breakdown by channel">
          <div className="h-full flex items-center justify-center bg-surface-overlay rounded">
            <span className="text-text-muted">[Pie Chart]</span>
          </div>
        </ChartCard>
        <ChartCard title="User Growth" subtitle="New vs returning users" fullWidth>
          <div className="h-full flex items-center justify-center bg-surface-overlay rounded">
            <span className="text-text-muted">[Area Chart]</span>
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
        <div className="bg-surface rounded-lg border border-border p-4">
          <ul className="divide-y divide-border-subtle">
            {[1, 2, 3, 4, 5].map((i) => (
              <li key={i} className="py-3 flex justify-between">
                <span className="text-text-secondary">Event {i}</span>
                <span className="text-text-muted text-sm">2 min ago</span>
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
          <button className="px-4 py-2 text-text-secondary bg-surface border border-border rounded-md hover:bg-surface-overlay">
            Export
          </button>
          <button className="px-4 py-2 text-white bg-accent rounded-md hover:bg-accent-hover">
            Add Member
          </button>
        </div>
      }
    >
      <DashboardSection>
        <p className="text-text-muted">Team content...</p>
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
                <button className="px-3 py-1.5 text-sm text-accent hover:text-accent/80">
                  Save View
                </button>
              }
            />
          }
          headerActions={
            <div className="flex gap-2">
              <button className="px-4 py-2 text-text-secondary bg-surface border border-border rounded-md hover:bg-surface-overlay text-sm">
                Export PDF
              </button>
              <button className="px-4 py-2 text-white bg-accent rounded-md hover:bg-accent-hover text-sm">
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
              title="Active Tenants"
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
                <div className="h-full flex items-center justify-center bg-accent/5 rounded">
                  <span className="text-accent/60">[Revenue Line Chart]</span>
                </div>
              </ChartCard>
              <ChartCard title="Tenant Acquisition" subtitle="By channel">
                <div className="h-full flex items-center justify-center bg-status-success/5 rounded">
                  <span className="text-status-success/60">[Acquisition Bar Chart]</span>
                </div>
              </ChartCard>
            </ChartGrid>
          </DashboardSection>

          {/* Bottom Section */}
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2">
              <DashboardSection title="Recent Orders">
                <div className="bg-surface rounded-lg border border-border overflow-hidden">
                  <table className="min-w-full divide-y divide-border">
                    <thead className="bg-surface-overlay">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">
                          Order
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">
                          Tenant
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">
                          Amount
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {[
                        { id: "#1234", tenant: "Acme Corp", amount: "$250.00", status: "Completed" },
                        { id: "#1235", tenant: "Nova Labs", amount: "$120.00", status: "Processing" },
                        { id: "#1236", tenant: "Silverline", amount: "$450.00", status: "Completed" },
                      ].map((order) => (
                        <tr key={order.id}>
                          <td className="px-4 py-3 text-sm font-medium text-text-primary">
                            {order.id}
                          </td>
                          <td className="px-4 py-3 text-sm text-text-secondary">{order.tenant}</td>
                          <td className="px-4 py-3 text-sm text-text-secondary">{order.amount}</td>
                          <td className="px-4 py-3 text-sm">
                            <span
                              className={`px-2 py-1 rounded-full text-xs ${
                                order.status === "Completed"
                                  ? "bg-status-success/10 text-status-success"
                                  : "bg-status-warning/10 text-status-warning"
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
                  <div className="bg-surface rounded-lg border border-border p-4">
                    <h4 className="text-sm font-medium text-text-muted">Top Product</h4>
                    <p className="text-lg font-semibold text-text-primary">Premium Plan</p>
                    <p className="text-sm text-text-muted">$12,450 revenue</p>
                  </div>
                  <div className="bg-surface rounded-lg border border-border p-4">
                    <h4 className="text-sm font-medium text-text-muted">Top Region</h4>
                    <p className="text-lg font-semibold text-text-primary">North America</p>
                    <p className="text-sm text-text-muted">42% of total sales</p>
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
