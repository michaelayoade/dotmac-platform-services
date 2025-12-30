/**
 * @dotmac/data-table
 *
 * Advanced data table component with server-side pagination,
 * selection, column config, and virtualization
 *
 * @example
 * ```tsx
 * import { DataTable, useDataTablePagination } from '@dotmac/data-table';
 *
 * const columns = [
 *   { accessorKey: 'name', header: 'Name' },
 *   { accessorKey: 'email', header: 'Email' },
 * ];
 *
 * function MyTable() {
 *   const { serverSidePagination, loading, refresh } = useDataTablePagination({
 *     onFetch: async ({ pageIndex, pageSize }) => {
 *       const res = await fetch(`/api/users?page=${pageIndex}&size=${pageSize}`);
 *       return res.json();
 *     },
 *   });
 *
 *   return (
 *     <DataTable
 *       columns={columns}
 *       data={data}
 *       serverSidePagination={serverSidePagination}
 *       loading={loading}
 *       selectable
 *       exportable
 *     />
 *   );
 * }
 * ```
 */

// ============================================================================
// Main Component
// ============================================================================

export {
  DataTable,
  type DataTableProps,
  type BulkAction,
  type QuickFilter,
  type FilterConfig,
  type ServerSidePagination,
  type DataTableTranslations,
} from "./DataTable";

// ============================================================================
// Hooks
// ============================================================================

export {
  useDataTablePagination,
  type UseDataTablePaginationOptions,
  type UseDataTablePaginationResult,
} from "./hooks/useDataTablePagination";

export {
  useColumnConfig,
  type UseColumnConfigOptions,
  type UseColumnConfigResult,
  type ColumnConfig,
} from "./hooks/useColumnConfig";

// ============================================================================
// Utilities
// ============================================================================

export { cn } from "./utils/cn";

// ============================================================================
// Re-export TanStack Table types for convenience
// ============================================================================

export type {
  ColumnDef,
  Row,
  SortingState,
  VisibilityState,
  ColumnFiltersState,
  PaginationState,
} from "@tanstack/react-table";

// ============================================================================
// Version
// ============================================================================

export const version = "1.0.0";
