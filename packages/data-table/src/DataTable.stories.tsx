import type { Meta, StoryObj } from "@storybook/react";
import { useState, useCallback } from "react";
import { DataTable, type ColumnDef } from "./DataTable";
import { useDataTablePagination } from "./hooks/useDataTablePagination";

// Sample data types
interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "active" | "inactive" | "pending";
  department: string;
  joinDate: string;
  salary: number;
}

// Sample data generator
const generateUsers = (count: number): User[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `user-${i + 1}`,
    name: `User ${i + 1}`,
    email: `user${i + 1}@example.com`,
    role: ["Admin", "Editor", "Viewer", "Manager"][i % 4],
    status: (["active", "inactive", "pending"] as const)[i % 3],
    department: ["Engineering", "Marketing", "Sales", "HR", "Finance"][i % 5],
    joinDate: new Date(2020 + (i % 4), i % 12, (i % 28) + 1)
      .toISOString()
      .split("T")[0],
    salary: 50000 + (i % 10) * 10000,
  }));

const allUsers = generateUsers(100);

// Column definitions
const columns: ColumnDef<User>[] = [
  {
    id: "name",
    header: "Name",
    accessorKey: "name",
    enableSorting: true,
  },
  {
    id: "email",
    header: "Email",
    accessorKey: "email",
    enableSorting: true,
  },
  {
    id: "role",
    header: "Role",
    accessorKey: "role",
    enableSorting: true,
  },
  {
    id: "status",
    header: "Status",
    accessorKey: "status",
    cell: ({ row }) => {
      const status = row.original.status;
      const colors = {
        active: "bg-green-100 text-green-800",
        inactive: "bg-gray-100 text-gray-800",
        pending: "bg-yellow-100 text-yellow-800",
      };
      return (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status]}`}
        >
          {status}
        </span>
      );
    },
  },
  {
    id: "department",
    header: "Department",
    accessorKey: "department",
    enableSorting: true,
  },
  {
    id: "joinDate",
    header: "Join Date",
    accessorKey: "joinDate",
    enableSorting: true,
  },
  {
    id: "salary",
    header: "Salary",
    accessorKey: "salary",
    cell: ({ row }) =>
      new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(row.original.salary),
    enableSorting: true,
  },
];

const meta: Meta<typeof DataTable<User>> = {
  title: "Components/DataTable",
  component: DataTable,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component:
          "A powerful data table component with sorting, pagination, selection, and column customization.",
      },
    },
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof DataTable<User>>;

// Basic usage
export const Basic: Story = {
  render: () => (
    <DataTable
      data={allUsers.slice(0, 10)}
      columns={columns}
      pageSize={10}
      enablePagination={false}
    />
  ),
};

// With client-side pagination
export const WithPagination: Story = {
  render: () => (
    <DataTable
      data={allUsers}
      columns={columns}
      pageSize={10}
      enablePagination
      pageSizeOptions={[5, 10, 20, 50]}
    />
  ),
};

// With row selection
export const WithSelection: Story = {
  render: () => {
    const [selected, setSelected] = useState<User[]>([]);

    return (
      <div className="space-y-4">
        <div className="text-sm text-gray-600">
          Selected: {selected.length} rows
          {selected.length > 0 && (
            <span className="ml-2">
              ({selected.map((u) => u.name).join(", ")})
            </span>
          )}
        </div>
        <DataTable
          data={allUsers.slice(0, 20)}
          columns={columns}
          pageSize={10}
          enableSelection
          onSelectionChange={setSelected}
        />
      </div>
    );
  },
};

// With search
export const WithSearch: Story = {
  render: () => (
    <DataTable
      data={allUsers}
      columns={columns}
      pageSize={10}
      enablePagination
      enableSearch
      searchPlaceholder="Search users..."
    />
  ),
};

// Server-side pagination example
export const ServerSidePagination: Story = {
  render: () => {
    // Simulate server-side fetching
    const fetchUsers = useCallback(
      async (params: { page: number; pageSize: number }) => {
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 500));

        const start = params.page * params.pageSize;
        const end = start + params.pageSize;

        return {
          data: allUsers.slice(start, end),
          totalCount: allUsers.length,
        };
      },
      []
    );

    const {
      data,
      isLoading,
      pagination,
      setPagination,
      totalPages,
      totalCount,
    } = useDataTablePagination({
      fetchFn: fetchUsers,
      initialPageSize: 10,
    });

    return (
      <div className="space-y-4">
        <div className="text-sm text-gray-600">
          Server-side pagination - Total records: {totalCount}
        </div>
        <DataTable
          data={data}
          columns={columns}
          pageSize={pagination.pageSize}
          loading={isLoading}
          enablePagination
          manualPagination
          pageIndex={pagination.pageIndex}
          pageCount={totalPages}
          onPaginationChange={(updater) => {
            if (typeof updater === "function") {
              setPagination(updater(pagination));
            } else {
              setPagination(updater);
            }
          }}
        />
      </div>
    );
  },
};

// With column visibility toggle
export const WithColumnConfig: Story = {
  render: () => {
    const [visibleColumns, setVisibleColumns] = useState<string[]>([
      "name",
      "email",
      "role",
      "status",
    ]);

    const toggleColumn = (columnId: string) => {
      setVisibleColumns((prev) =>
        prev.includes(columnId)
          ? prev.filter((id) => id !== columnId)
          : [...prev, columnId]
      );
    };

    const filteredColumns = columns.filter((col) =>
      visibleColumns.includes(col.id as string)
    );

    return (
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {columns.map((col) => (
            <button
              key={col.id}
              onClick={() => toggleColumn(col.id as string)}
              className={`px-3 py-1 text-sm rounded-md border ${
                visibleColumns.includes(col.id as string)
                  ? "bg-blue-50 border-blue-200 text-blue-700"
                  : "bg-white border-gray-200 text-gray-600"
              }`}
            >
              {col.header as string}
            </button>
          ))}
        </div>
        <DataTable
          data={allUsers.slice(0, 20)}
          columns={filteredColumns}
          pageSize={10}
          enablePagination
        />
      </div>
    );
  },
};

// Loading state
export const LoadingState: Story = {
  render: () => (
    <DataTable
      data={[]}
      columns={columns}
      pageSize={10}
      loading
      loadingRows={5}
    />
  ),
};

// Empty state
export const EmptyState: Story = {
  render: () => (
    <DataTable
      data={[]}
      columns={columns}
      pageSize={10}
      emptyMessage="No users found"
      emptyDescription="Try adjusting your search or filters"
    />
  ),
};

// With row actions
export const WithRowActions: Story = {
  render: () => {
    const columnsWithActions: ColumnDef<User>[] = [
      ...columns,
      {
        id: "actions",
        header: "Actions",
        cell: ({ row }) => (
          <div className="flex gap-2">
            <button
              onClick={() => alert(`Edit ${row.original.name}`)}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              Edit
            </button>
            <button
              onClick={() => alert(`Delete ${row.original.name}`)}
              className="text-red-600 hover:text-red-800 text-sm"
            >
              Delete
            </button>
          </div>
        ),
      },
    ];

    return (
      <DataTable
        data={allUsers.slice(0, 10)}
        columns={columnsWithActions}
        pageSize={10}
      />
    );
  },
};

// Compact variant
export const CompactVariant: Story = {
  render: () => (
    <DataTable
      data={allUsers.slice(0, 15)}
      columns={columns}
      pageSize={15}
      variant="compact"
      enablePagination
    />
  ),
};

// Striped rows
export const StripedRows: Story = {
  render: () => (
    <DataTable
      data={allUsers.slice(0, 10)}
      columns={columns}
      pageSize={10}
      striped
    />
  ),
};

// Full featured example
export const FullFeatured: Story = {
  render: () => {
    const [selected, setSelected] = useState<User[]>([]);

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">User Management</h2>
          {selected.length > 0 && (
            <button className="px-4 py-2 bg-red-600 text-white rounded-md text-sm">
              Delete {selected.length} selected
            </button>
          )}
        </div>
        <DataTable
          data={allUsers}
          columns={columns}
          pageSize={10}
          enablePagination
          enableSearch
          enableSelection
          onSelectionChange={setSelected}
          pageSizeOptions={[10, 25, 50, 100]}
          searchPlaceholder="Search by name, email..."
        />
      </div>
    );
  },
};
