"use client";

import {
  useEffect,
  useMemo,
  useState,
  useRef,
  useCallback,
  memo,
  type KeyboardEvent,
} from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogOverlay,
  DialogTitle,
} from "@dotmac/core";

import { cn } from "@/lib/utils";
import {
  getAllNavItems,
  quickActions,
  footerNavItem,
  searchNavigation,
  type NavItem,
  type ActionItem,
} from "@/lib/config/navigation";

// ============================================================================
// Types
// ============================================================================

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

interface CommandItemData {
  id: string;
  label: string;
  description?: string;
  icon: React.ElementType;
  href: string;
  section: "navigation" | "actions";
}

// ============================================================================
// Hooks
// ============================================================================

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// ============================================================================
// Components
// ============================================================================

const CommandRow = memo(function CommandRow({
  item,
  selected,
  onClick,
}: {
  item: CommandItemData;
  selected: boolean;
  onClick: () => void;
}) {
  const Icon = item.icon;

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors",
        "focus:outline-none",
        selected
          ? "bg-accent-subtle text-accent"
          : "text-text-secondary hover:bg-surface-overlay"
      )}
    >
      <Icon
        className={cn(
          "w-4 h-4 flex-shrink-0",
          selected ? "text-accent" : "text-text-muted"
        )}
      />
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm font-medium", selected && "text-accent")}>
          {item.label}
        </p>
        {item.description && (
          <p className="text-xs text-text-muted truncate">{item.description}</p>
        )}
      </div>
    </button>
  );
});

export const CommandPalette = memo(function CommandPalette({
  open,
  onClose,
}: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Debounce search for performance
  const debouncedQuery = useDebounce(query, 150);

  // Track the element that was focused before opening
  useEffect(() => {
    if (open) {
      previousActiveElement.current = document.activeElement as HTMLElement;
    }
  }, [open]);

  // Get all nav items including help
  const allNavItems = useMemo(() => {
    return [...getAllNavItems(), footerNavItem];
  }, []);

  // Convert to command items format
  const commands = useMemo<CommandItemData[]>(() => {
    const navCommands: CommandItemData[] = allNavItems.map((item) => ({
      id: `nav-${item.id}`,
      label: `Go to ${item.label}`,
      description: item.description,
      icon: item.icon,
      href: item.href,
      section: "navigation" as const,
    }));

    const actionCommands: CommandItemData[] = quickActions.map((action) => ({
      id: action.id,
      label: action.label,
      description: action.description,
      icon: action.icon,
      href: action.href,
      section: "actions" as const,
    }));

    return [...actionCommands, ...navCommands];
  }, [allNavItems]);

  // Filter commands based on debounced query
  const filteredCommands = useMemo(() => {
    if (!debouncedQuery.trim()) {
      return commands;
    }

    const { navItems, actionItems } = searchNavigation(
      debouncedQuery,
      allNavItems,
      quickActions
    );

    const matchedNavIds = new Set(navItems.map((n) => `nav-${n.id}`));
    const matchedActionIds = new Set(actionItems.map((a) => a.id));

    return commands.filter(
      (cmd) => matchedNavIds.has(cmd.id) || matchedActionIds.has(cmd.id)
    );
  }, [commands, debouncedQuery, allNavItems]);

  // Group by section
  const groupedCommands = useMemo(
    () => ({
      actions: filteredCommands.filter((c) => c.section === "actions"),
      navigation: filteredCommands.filter((c) => c.section === "navigation"),
    }),
    [filteredCommands]
  );

  const flatCommands = useMemo(
    () => [...groupedCommands.actions, ...groupedCommands.navigation],
    [groupedCommands]
  );

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [debouncedQuery]);

  // Execute command
  const executeCommand = useCallback(
    (command: CommandItemData) => {
      router.push(command.href);
      onClose();
    },
    [router, onClose]
  );

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (flatCommands.length === 0) {
        if (e.key === "Escape") {
          e.preventDefault();
          onClose();
        }
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((i) => (i + 1) % flatCommands.length);
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex(
            (i) => (i - 1 + flatCommands.length) % flatCommands.length
          );
          break;
        case "Enter":
          e.preventDefault();
          if (flatCommands[selectedIndex]) {
            executeCommand(flatCommands[selectedIndex]);
          }
          break;
        case "Escape":
          e.preventDefault();
          onClose();
          break;
      }
    },
    [flatCommands, selectedIndex, executeCommand, onClose]
  );

  // Reset state and restore focus when closing
  useEffect(() => {
    if (!open) {
      setQuery("");
      setSelectedIndex(0);
      // Restore focus to the element that was focused before opening
      if (
        previousActiveElement.current &&
        typeof previousActiveElement.current.focus === "function"
      ) {
        requestAnimationFrame(() => {
          previousActiveElement.current?.focus();
        });
      }
    }
  }, [open]);

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogOverlay className="bg-surface/80 backdrop-blur-sm" />
      <DialogContent
        className="fixed top-[20%] left-1/2 -translate-x-1/2 w-[calc(100%-2rem)] sm:w-full max-w-xl bg-surface-elevated border border-border rounded-xl shadow-2xl overflow-hidden animate-scale-in"
        onKeyDown={handleKeyDown}
        aria-describedby={undefined}
      >
        {/* Visually hidden title for screen readers */}
        <DialogTitle className="sr-only">Command Palette</DialogTitle>

        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search className="w-5 h-5 text-text-muted flex-shrink-0" />
          <input
            type="text"
            placeholder="Search commands, pages, or actions..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-text-primary placeholder:text-text-muted focus:outline-none text-base"
            autoFocus
          />
          <kbd className="px-2 py-1 text-xs font-mono text-text-muted bg-surface rounded border border-border">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto py-2">
          {flatCommands.length === 0 ? (
            <div className="px-4 py-8 text-center text-text-muted">
              <p>No results found for &quot;{query}&quot;</p>
            </div>
          ) : (
            <>
              {/* Actions */}
              {groupedCommands.actions.length > 0 && (
                <div className="mb-2">
                  <div className="px-4 py-1">
                    <span className="text-2xs font-semibold uppercase tracking-wider text-text-muted">
                      Actions
                    </span>
                  </div>
                  {groupedCommands.actions.map((cmd) => (
                    <CommandRow
                      key={cmd.id}
                      item={cmd}
                      selected={flatCommands.indexOf(cmd) === selectedIndex}
                      onClick={() => executeCommand(cmd)}
                    />
                  ))}
                </div>
              )}

              {/* Navigation */}
              {groupedCommands.navigation.length > 0 && (
                <div>
                  <div className="px-4 py-1">
                    <span className="text-2xs font-semibold uppercase tracking-wider text-text-muted">
                      Navigation
                    </span>
                  </div>
                  {groupedCommands.navigation.map((cmd) => (
                    <CommandRow
                      key={cmd.id}
                      item={cmd}
                      selected={flatCommands.indexOf(cmd) === selectedIndex}
                      onClick={() => executeCommand(cmd)}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-border text-2xs text-text-muted">
          <div className="flex items-center gap-4">
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border mr-1">
                ↑↓
              </kbd>
              Navigate
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border mr-1">
                ↵
              </kbd>
              Select
            </span>
          </div>
          <span>
            <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border mr-1">
              ESC
            </kbd>
            Close
          </span>
        </div>
      </DialogContent>
    </Dialog>
  );
});

export default CommandPalette;
