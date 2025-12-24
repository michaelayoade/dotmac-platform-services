/**
 * Hook for column configuration (visibility, ordering, pinning)
 */

import { useState, useCallback, useMemo } from "react";
import type { VisibilityState } from "@tanstack/react-table";

export interface ColumnConfig {
  id: string;
  label: string;
  visible: boolean;
  pinned?: "left" | "right" | false;
  order: number;
}

export interface UseColumnConfigOptions {
  columns: Array<{ id: string; header?: string }>;
  defaultVisibility?: VisibilityState;
  storageKey?: string;
}

export interface UseColumnConfigResult {
  columnVisibility: VisibilityState;
  columnConfigs: ColumnConfig[];
  setColumnVisibility: (visibility: VisibilityState) => void;
  toggleColumn: (columnId: string) => void;
  showAllColumns: () => void;
  hideAllColumns: () => void;
  resetColumns: () => void;
  reorderColumns: (fromIndex: number, toIndex: number) => void;
  pinColumn: (columnId: string, position: "left" | "right" | false) => void;
}

export function useColumnConfig({
  columns,
  defaultVisibility = {},
  storageKey,
}: UseColumnConfigOptions): UseColumnConfigResult {
  // Load from storage if available
  const loadFromStorage = (): VisibilityState | null => {
    if (!storageKey || typeof window === "undefined") return null;
    try {
      const stored = localStorage.getItem(storageKey);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  };

  const saveToStorage = (visibility: VisibilityState) => {
    if (!storageKey || typeof window === "undefined") return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(visibility));
    } catch {
      // Ignore storage errors
    }
  };

  const initialVisibility = loadFromStorage() ?? defaultVisibility;

  const [columnVisibility, setColumnVisibilityState] =
    useState<VisibilityState>(initialVisibility);
  const [columnOrder, setColumnOrder] = useState<string[]>(columns.map((c) => c.id));
  const [pinnedColumns, setPinnedColumns] = useState<
    Record<string, "left" | "right" | false>
  >({});

  const setColumnVisibility = useCallback(
    (visibility: VisibilityState) => {
      setColumnVisibilityState(visibility);
      saveToStorage(visibility);
    },
    [storageKey]
  );

  const toggleColumn = useCallback((columnId: string) => {
    setColumnVisibilityState((prev) => {
      const next = { ...prev, [columnId]: !prev[columnId] };
      saveToStorage(next);
      return next;
    });
  }, []);

  const showAllColumns = useCallback(() => {
    const visibility = Object.fromEntries(columns.map((c) => [c.id, true]));
    setColumnVisibility(visibility);
  }, [columns, setColumnVisibility]);

  const hideAllColumns = useCallback(() => {
    const visibility = Object.fromEntries(columns.map((c) => [c.id, false]));
    setColumnVisibility(visibility);
  }, [columns, setColumnVisibility]);

  const resetColumns = useCallback(() => {
    setColumnVisibility(defaultVisibility);
    setColumnOrder(columns.map((c) => c.id));
    setPinnedColumns({});
  }, [columns, defaultVisibility, setColumnVisibility]);

  const reorderColumns = useCallback((fromIndex: number, toIndex: number) => {
    setColumnOrder((prev) => {
      const next = [...prev];
      const [removed] = next.splice(fromIndex, 1);
      next.splice(toIndex, 0, removed);
      return next;
    });
  }, []);

  const pinColumn = useCallback(
    (columnId: string, position: "left" | "right" | false) => {
      setPinnedColumns((prev) => ({ ...prev, [columnId]: position }));
    },
    []
  );

  const columnConfigs = useMemo<ColumnConfig[]>(() => {
    return columnOrder.map((id, index) => {
      const column = columns.find((c) => c.id === id);
      return {
        id,
        label: column?.header ?? id,
        visible: columnVisibility[id] !== false,
        pinned: pinnedColumns[id] ?? false,
        order: index,
      };
    });
  }, [columns, columnOrder, columnVisibility, pinnedColumns]);

  return {
    columnVisibility,
    columnConfigs,
    setColumnVisibility,
    toggleColumn,
    showAllColumns,
    hideAllColumns,
    resetColumns,
    reorderColumns,
    pinColumn,
  };
}
