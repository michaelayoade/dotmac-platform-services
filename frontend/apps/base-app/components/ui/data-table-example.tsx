/**
 * DataTable Usage Examples
 * Copy these patterns when implementing tables in your pages
 */

import { ColumnDef } from "@tanstack/react-table";
import { DataTable, createSortableHeader } from "@/components/ui/data-table";
import { StatusBadge, getStatusVariant } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { MoreHorizontal, Eye, Edit, Trash } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Example 1: User Management Table
interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

const userColumns: ColumnDef<User>[] = [
  {
    accessorKey: "name",
    header: createSortableHeader("Name"),
  },
  {
    accessorKey: "email",
    header: createSortableHeader("Email"),
  },
  {
    accessorKey: "role",
    header: "Role",
    cell: ({ row }) => (
      <StatusBadge variant="info" size="sm">
        {row.getValue("role")}
      </StatusBadge>
    ),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as string;
      return (
        <StatusBadge variant={getStatusVariant(status)} size="sm" showDot>
          {status}
        </StatusBadge>
      );
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const user = row.original;

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-card">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem onClick={() => navigator.clipboard.writeText(user.id)}>
              Copy user ID
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <Eye className="mr-2 h-4 w-4" />
              View details
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="mr-2 h-4 w-4" />
              Edit user
            </DropdownMenuItem>
            <DropdownMenuItem className="text-red-600 dark:text-red-400">
              <Trash className="mr-2 h-4 w-4" />
              Delete user
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];

export function UsersTableExample({ data }: { data: User[] }) {
  return (
    <DataTable
      columns={userColumns}
      data={data}
      searchable
      searchColumn="name"
      searchPlaceholder="Search users by name..."
      paginated
      columnVisibility
      emptyMessage="No users found."
    />
  );
}

// Example 2: Invoice Table (with row click handler)
interface Invoice {
  id: string;
  invoice_number: string;
  customer_name: string;
  amount: number;
  status: "paid" | "unpaid" | "overdue";
  due_date: string;
}

const invoiceColumns: ColumnDef<Invoice>[] = [
  {
    accessorKey: "invoice_number",
    header: createSortableHeader("Invoice #"),
  },
  {
    accessorKey: "customer_name",
    header: createSortableHeader("Customer"),
  },
  {
    accessorKey: "amount",
    header: createSortableHeader("Amount"),
    cell: ({ row }) => {
      const amount = parseFloat(row.getValue("amount"));
      const formatted = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(amount);
      return <div className="font-medium">{formatted}</div>;
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as string;
      return (
        <StatusBadge variant={getStatusVariant(status)} showDot>
          {status}
        </StatusBadge>
      );
    },
  },
  {
    accessorKey: "due_date",
    header: createSortableHeader("Due Date"),
    cell: ({ row }) => {
      const date = new Date(row.getValue("due_date"));
      return date.toLocaleDateString();
    },
  },
];

export function InvoicesTableExample({
  data,
  onInvoiceClick,
}: {
  data: Invoice[];
  onInvoiceClick: (invoice: Invoice) => void;
}) {
  return (
    <DataTable
      columns={invoiceColumns}
      data={data}
      searchable
      searchColumn="invoice_number"
      searchPlaceholder="Search invoices..."
      paginated
      defaultPageSize={20}
      pageSizeOptions={[10, 20, 50, 100]}
      onRowClick={onInvoiceClick}
      emptyMessage="No invoices found. Create your first invoice to get started."
    />
  );
}

// Example 3: Simple Table (no search, no pagination)
interface Product {
  id: string;
  name: string;
  price: number;
  stock: number;
}

const productColumns: ColumnDef<Product>[] = [
  {
    accessorKey: "name",
    header: "Product Name",
  },
  {
    accessorKey: "price",
    header: "Price",
    cell: ({ row }) => {
      const price = parseFloat(row.getValue("price"));
      return `$${price.toFixed(2)}`;
    },
  },
  {
    accessorKey: "stock",
    header: "Stock",
    cell: ({ row }) => {
      const stock = row.getValue("stock") as number;
      return (
        <span
          className={stock < 10 ? "text-red-600 dark:text-red-400" : "text-foreground"}
        >
          {stock}
        </span>
      );
    },
  },
];

export function ProductsTableExample({ data }: { data: Product[] }) {
  return (
    <DataTable
      columns={productColumns}
      data={data}
      searchable={false}
      paginated={false}
      emptyMessage="No products available."
    />
  );
}

// Example 4: Table with Loading State
export function LoadingTableExample({ isLoading, data }: { isLoading: boolean; data: User[] }) {
  return (
    <DataTable
      columns={userColumns}
      data={data}
      isLoading={isLoading}
      searchable
      searchColumn="name"
      paginated
    />
  );
}
