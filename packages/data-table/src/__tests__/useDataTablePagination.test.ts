import { renderHook, act, waitFor } from "@testing-library/react";
import { useDataTablePagination } from "../hooks/useDataTablePagination";

describe("useDataTablePagination", () => {
  const mockFetch = jest.fn();

  beforeEach(() => {
    mockFetch.mockReset();
    mockFetch.mockResolvedValue({
      data: [{ id: 1 }, { id: 2 }],
      totalRows: 100,
      pageCount: 10,
    });
  });

  it("should initialize with default values", () => {
    const { result } = renderHook(() => useDataTablePagination());

    expect(result.current.pageIndex).toBe(0);
    expect(result.current.pageSize).toBe(10);
    expect(result.current.data).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should initialize with custom values", () => {
    const { result } = renderHook(() =>
      useDataTablePagination({
        initialPageIndex: 2,
        initialPageSize: 25,
      })
    );

    expect(result.current.pageIndex).toBe(2);
    expect(result.current.pageSize).toBe(25);
  });

  it("should fetch data on mount when fetchOnMount is true (default)", async () => {
    const { result } = renderHook(() =>
      useDataTablePagination({
        onFetch: mockFetch,
      })
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    expect(mockFetch).toHaveBeenCalledWith({ pageIndex: 0, pageSize: 10 });
    expect(result.current.data).toEqual([{ id: 1 }, { id: 2 }]);
    expect(result.current.totalRows).toBe(100);
    expect(result.current.pageCount).toBe(10);
  });

  it("should not fetch data on mount when fetchOnMount is false", async () => {
    renderHook(() =>
      useDataTablePagination({
        onFetch: mockFetch,
        fetchOnMount: false,
      })
    );

    // Give time for any async operations
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should fetch data when page index changes", async () => {
    const { result } = renderHook(() =>
      useDataTablePagination({
        onFetch: mockFetch,
        fetchOnMount: false,
      })
    );

    act(() => {
      result.current.setPageIndex(2);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith({ pageIndex: 2, pageSize: 10 });
    });
  });

  it("should reset to page 0 when page size changes", async () => {
    const { result } = renderHook(() =>
      useDataTablePagination({
        onFetch: mockFetch,
        fetchOnMount: false,
        initialPageIndex: 5,
      })
    );

    act(() => {
      result.current.setPageSize(25);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith({ pageIndex: 0, pageSize: 25 });
    });

    expect(result.current.pageIndex).toBe(0);
    expect(result.current.pageSize).toBe(25);
  });

  it("should handle fetch errors", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() =>
      useDataTablePagination({
        onFetch: mockFetch,
      })
    );

    await waitFor(() => {
      expect(result.current.error).toBe("Network error");
    });

    expect(result.current.loading).toBe(false);
  });

  it("should refresh data", async () => {
    const { result } = renderHook(() =>
      useDataTablePagination({
        onFetch: mockFetch,
        fetchOnMount: false,
      })
    );

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockFetch).toHaveBeenCalledWith({ pageIndex: 0, pageSize: 10 });
  });

  it("should provide serverSidePagination config object", () => {
    const { result } = renderHook(() =>
      useDataTablePagination({
        initialPageIndex: 1,
        initialPageSize: 20,
      })
    );

    expect(result.current.serverSidePagination).toEqual({
      pageIndex: 1,
      pageSize: 20,
      pageCount: 0,
      totalRows: 0,
      onPageChange: expect.any(Function),
      onPageSizeChange: expect.any(Function),
    });
  });

  it("should set loading state during fetch", async () => {
    let resolvePromise: (value: unknown) => void;
    mockFetch.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
    );

    const { result } = renderHook(() =>
      useDataTablePagination({
        onFetch: mockFetch,
      })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(true);
    });

    act(() => {
      resolvePromise!({
        data: [],
        totalRows: 0,
        pageCount: 0,
      });
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });
});
