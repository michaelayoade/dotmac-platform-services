"use client";

import { memo, useMemo, useEffect, useRef, useState, useCallback } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { X, Zap } from "lucide-react";

import { cn } from "@/lib/utils";
import { usePermission } from "@/lib/hooks/use-permission";
import {
  navigationSections,
  footerNavItem,
  filterNavByPermissions,
  isPathActive,
} from "@/lib/config/navigation";
import type { PlatformUser } from "@/types/auth";

// ============================================================================
// Types
// ============================================================================

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
  user: PlatformUser;
}

// ============================================================================
// Components
// ============================================================================

const MobileNavLink = memo(function MobileNavLink({
  href,
  label,
  icon: Icon,
  badge,
  active,
  onClick,
}: {
  href: string;
  label: string;
  icon: React.ElementType;
  badge?: string | number;
  active: boolean;
  onClick?: () => void;
}) {
  return (
    <Link
      href={href}
      prefetch={true}
      onClick={onClick}
      className={cn(
        "relative flex items-center gap-3 rounded-md px-3 py-2.5 transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset",
        active
          ? "bg-accent-subtle text-accent"
          : "text-text-secondary hover:bg-surface-overlay hover:text-text-primary"
      )}
      aria-current={active ? "page" : undefined}
    >
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-accent rounded-r" />
      )}
      <Icon
        className={cn("w-5 h-5 flex-shrink-0", active && "text-accent")}
        aria-hidden="true"
      />
      <span className="text-sm font-medium">{label}</span>
      {badge !== undefined && (
        <span
          className="ml-auto inline-flex items-center justify-center w-5 h-5 text-2xs font-semibold rounded-full bg-status-error text-text-inverse"
          role="status"
          aria-label={`${badge} notifications`}
        >
          {badge}
        </span>
      )}
    </Link>
  );
});

export const MobileDrawer = memo(function MobileDrawer({
  open,
  onClose,
  user,
}: MobileDrawerProps) {
  const pathname = usePathname();
  const { hasPermission, isLoading } = usePermission();
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previousPathRef = useRef(pathname);
  const previousBodyOverflowRef = useRef<string | null>(null);
  const openerRef = useRef<HTMLElement | null>(null);

  // Animation states
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  // Filter navigation by permissions - memoized
  const filteredSections = useMemo(
    () => filterNavByPermissions(navigationSections, hasPermission),
    [hasPermission]
  );

  // Handle open/close with animation
  useEffect(() => {
    if (open) {
      setIsVisible(true);
      // Small delay to trigger animation
      requestAnimationFrame(() => {
        setIsAnimating(true);
      });
    } else if (isVisible) {
      setIsAnimating(false);
      // Wait for animation to complete before hiding
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 200); // Match animation duration
      return () => clearTimeout(timer);
    }
  }, [open, isVisible]);

  // Close on route change (only when route actually changes)
  useEffect(() => {
    if (previousPathRef.current !== pathname && open) {
      onClose();
    }
    previousPathRef.current = pathname;
  }, [pathname, open, onClose]);

  // Focus trap and escape key
  useEffect(() => {
    if (!open) return;

    openerRef.current = document.activeElement as HTMLElement | null;
    // Focus close button when opened
    const timer = setTimeout(() => {
      closeButtonRef.current?.focus();
    }, 100);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }

      if (e.key === "Tab") {
        const focusables = drawerRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusables || focusables.length === 0) {
          e.preventDefault();
          return;
        }

        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    previousBodyOverflowRef.current = document.body.style.overflow || "";
    document.body.style.overflow = "hidden";

    return () => {
      clearTimeout(timer);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousBodyOverflowRef.current ?? "";
      openerRef.current?.focus();
    };
  }, [open, onClose]);

  // Handle link click - close after small delay for smooth transition
  const handleLinkClick = useCallback(() => {
    // Don't close immediately, let the navigation start first
    setTimeout(onClose, 50);
  }, [onClose]);

  if (!isVisible) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          "fixed inset-0 z-50 bg-overlay/50 backdrop-blur-sm lg:hidden transition-opacity duration-200",
          isAnimating ? "opacity-100" : "opacity-0"
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 lg:hidden",
          "bg-surface-elevated border-r border-border",
          "flex flex-col",
          "transition-transform duration-200 ease-out",
          isAnimating ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-border">
          <Link
            href="/"
            prefetch={true}
            className="flex items-center gap-3"
            onClick={handleLinkClick}
          >
            <div className="relative w-8 h-8 flex items-center justify-center">
              <Zap className="w-6 h-6 text-accent" />
              <div className="absolute inset-0 bg-accent/20 rounded-lg blur-sm" />
            </div>
            <span className="font-semibold text-lg tracking-tight text-text-primary">
              DotMac
            </span>
          </Link>
          <button
            ref={closeButtonRef}
            onClick={onClose}
            className="p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            aria-label="Close navigation menu"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Navigation */}
        <nav
          className="flex-1 overflow-y-auto py-4 px-2"
          aria-label="Main navigation"
        >
          {isLoading ? (
            <div className="space-y-4 px-2">
              {Array.from({ length: 6 }).map((_, idx) => (
                <div
                  key={`mobile-nav-skeleton-${idx}`}
                  className="h-4 rounded bg-surface-overlay/70 animate-pulse"
                  style={{ width: `${65 + idx * 4}%` }}
                />
              ))}
            </div>
          ) : (
            filteredSections.map((section, sectionIdx) => (
              <div key={section.id} className={cn(sectionIdx > 0 && "mt-6")}>
                <h3 className="px-3 mb-2 text-2xs font-semibold uppercase tracking-wider text-text-muted">
                  {section.title}
                </h3>
                <ul className="space-y-1">
                  {section.items.map((item) => (
                    <li key={item.id}>
                      <MobileNavLink
                        href={item.href}
                        label={item.label}
                        icon={item.icon}
                        badge={item.badge}
                        active={isPathActive(item.href, pathname)}
                        onClick={handleLinkClick}
                      />
                    </li>
                  ))}
                </ul>
              </div>
            ))
          )}
        </nav>

        {/* Footer */}
        <div className="border-t border-border p-2">
          <Link
            href={footerNavItem.href}
            prefetch={true}
            onClick={handleLinkClick}
            className="flex items-center gap-3 rounded-md px-3 py-2.5 text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset"
          >
            <footerNavItem.icon className="w-5 h-5" aria-hidden="true" />
            <span className="text-sm font-medium">{footerNavItem.label}</span>
          </Link>

          {/* User profile */}
          <div className="flex items-center gap-3 rounded-md px-3 py-2.5 mt-1">
            <div className="relative flex-shrink-0">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-highlight flex items-center justify-center text-sm font-semibold text-text-inverse">
                {user.fullName?.charAt(0).toUpperCase() ||
                  user.username?.charAt(0).toUpperCase() ||
                  "U"}
              </div>
              <span
                className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-status-success border-2 border-surface-elevated rounded-full"
                role="status"
                aria-label="Online"
              >
                <span className="sr-only">Status: Online</span>
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {user.fullName || user.username}
              </p>
              <p className="text-2xs text-text-muted truncate">{user.email}</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
});

export default MobileDrawer;
