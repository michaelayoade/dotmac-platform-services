/**
 * Hook for server-side pagination
 */

import { useState, useCallback, useEffect, useRef } from "react";

export interface UseDataTablePaginationOptions {
  initialPageIndex?: number;
  initialPageSize?: number;
  /** Whether to fetch data on mount. Defaults to true. */
  fetchOnMount?: boolean;
  onFetch?: (params: { pageIndex: number; pageSize: number }) => Promise<{
    data: unknown[];
    totalRows: number;
    pageCount: number;
  }>;
}

export interface UseDataTablePaginationResult {
  pageIndex: number;
  pageSize: number;
  pageCount: number;
  totalRows: number;
  data: unknown[];
  loading: boolean;
  error: string | null;
  setPageIndex: (index: number) => void;
  setPageSize: (size: number) => void;
  refresh: () => Promise<void>;
  serverSidePagination: {
    pageIndex: number;
    pageSize: number;
    pageCount: number;
    totalRows: number;
    onPageChange: (index: number) => void;
    onPageSizeChange: (size: number) => void;
  };
}

export function useDataTablePagination({
  initialPageIndex = 0,
  initialPageSize = 10,
  fetchOnMount = true,
  onFetch,
}: UseDataTablePaginationOptions = {}): UseDataTablePaginationResult {
  const [pageIndex, setPageIndexState] = useState(initialPageIndex);
  const [pageSize, setPageSizeState] = useState(initialPageSize);
  const [pageCount, setPageCount] = useState(0);
  const [totalRows, setTotalRows] = useState(0);
  const [data, setData] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasFetchedRef = useRef(false);

  const fetchData = useCallback(
    async (index: number, size: number) => {
      if (!onFetch) return;

      setLoading(true);
      setError(null);

      try {
        const result = await onFetch({ pageIndex: index, pageSize: size });
        setData(result.data);
        setTotalRows(result.totalRows);
        setPageCount(result.pageCount);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      } finally {
        setLoading(false);
      }
    },
    [onFetch]
  );

  const setPageIndex = useCallback(
    (index: number) => {
      setPageIndexState(index);
      fetchData(index, pageSize);
    },
    [pageSize, fetchData]
  );

  const setPageSize = useCallback(
    (size: number) => {
      setPageSizeState(size);
      setPageIndexState(0); // Reset to first page
      fetchData(0, size);
    },
    [fetchData]
  );

  const refresh = useCallback(async () => {
    await fetchData(pageIndex, pageSize);
  }, [pageIndex, pageSize, fetchData]);

  // Initial fetch on mount
  useEffect(() => {
    if (fetchOnMount && onFetch && !hasFetchedRef.current) {
      hasFetchedRef.current = true;
      fetchData(initialPageIndex, initialPageSize);
    }
  }, [fetchOnMount, onFetch, fetchData, initialPageIndex, initialPageSize]);

  return {
    pageIndex,
    pageSize,
    pageCount,
    totalRows,
    data,
    loading,
    error,
    setPageIndex,
    setPageSize,
    refresh,
    serverSidePagination: {
      pageIndex,
      pageSize,
      pageCount,
      totalRows,
      onPageChange: setPageIndex,
      onPageSizeChange: setPageSize,
    },
  };
}
