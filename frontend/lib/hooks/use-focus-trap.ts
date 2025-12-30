import { useEffect, useRef, useCallback } from "react";

interface UseFocusTrapOptions {
  /** Whether the focus trap is active */
  enabled: boolean;
  /** Callback when Escape key is pressed */
  onEscape?: () => void;
  /** Whether to restore focus to the previously focused element on close */
  restoreFocusOnClose?: boolean;
}

const FOCUSABLE_SELECTORS =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

/**
 * Focus trap hook for dropdown menus and modals
 * Traps focus within a container and handles keyboard navigation.
 *
 * @param options - Configuration options
 * @returns A ref to attach to the container element
 */
export function useFocusTrap<T extends HTMLElement>({
  enabled,
  onEscape,
  restoreFocusOnClose = true,
}: UseFocusTrapOptions) {
  const containerRef = useRef<T>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Store the element that was focused before trap was enabled
  useEffect(() => {
    if (enabled) {
      previousActiveElement.current = document.activeElement as HTMLElement;
    }
  }, [enabled]);

  // Restore focus when trap is disabled
  useEffect(() => {
    if (!enabled && restoreFocusOnClose && previousActiveElement.current) {
      requestAnimationFrame(() => {
        previousActiveElement.current?.focus();
      });
    }
  }, [enabled, restoreFocusOnClose]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled || !containerRef.current) return;

      const focusableElements =
        containerRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS);
      const focusableArray = Array.from(focusableElements);
      const firstElement = focusableArray[0];
      const lastElement = focusableArray[focusableArray.length - 1];

      if (e.key === "Escape") {
        e.preventDefault();
        onEscape?.();
        return;
      }

      if (e.key === "Tab") {
        if (focusableArray.length === 0) {
          e.preventDefault();
          return;
        }

        if (e.shiftKey) {
          // Shift+Tab: if on first element, wrap to last
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          // Tab: if on last element, wrap to first
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      }

      // Arrow key navigation for menu items
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        const currentIndex = focusableArray.indexOf(
          document.activeElement as HTMLElement
        );
        let nextIndex: number;

        if (e.key === "ArrowDown") {
          nextIndex =
            currentIndex < focusableArray.length - 1 ? currentIndex + 1 : 0;
        } else {
          nextIndex =
            currentIndex > 0 ? currentIndex - 1 : focusableArray.length - 1;
        }

        focusableArray[nextIndex]?.focus();
      }
    },
    [enabled, onEscape]
  );

  // Attach keyboard listener
  useEffect(() => {
    if (enabled) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [enabled, handleKeyDown]);

  // Focus first element when trap is enabled
  useEffect(() => {
    if (enabled && containerRef.current) {
      const firstFocusable =
        containerRef.current.querySelector<HTMLElement>(FOCUSABLE_SELECTORS);
      requestAnimationFrame(() => {
        firstFocusable?.focus();
      });
    }
  }, [enabled]);

  return containerRef;
}
