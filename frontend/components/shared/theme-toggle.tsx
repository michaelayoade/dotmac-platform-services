"use client";

import { useState, useRef, useEffect, type ElementType } from "react";
import { Sun, Moon, Monitor, Check } from "lucide-react";
import { useTheme } from "@/lib/dotmac/core";
import { cn } from "@/lib/utils";

type ColorScheme = "light" | "dark" | "system";

const themeOptions: { value: ColorScheme; label: string; icon: ElementType }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { config, resolvedColorScheme, setColorScheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen]);

  const CurrentIcon = resolvedColorScheme === "dark" ? Moon : Sun;

  return (
    <div ref={dropdownRef} className={cn("relative", className)}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "relative p-2 rounded-md",
          "text-text-muted hover:text-text-secondary",
          "hover:bg-surface-overlay",
          "transition-colors duration-150",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        )}
        aria-label="Toggle theme"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <CurrentIcon className="w-5 h-5" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={cn(
            "absolute right-0 top-full mt-2 z-50",
            "w-36 py-1",
            "bg-surface-elevated border border-border rounded-lg",
            "shadow-lg shadow-black/20",
            "animate-fade-in"
          )}
          role="listbox"
          aria-label="Theme options"
        >
          {themeOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = config.colorScheme === option.value;

            return (
              <button
                key={option.value}
                onClick={() => {
                  setColorScheme(option.value);
                  setIsOpen(false);
                }}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2",
                  "text-sm text-left",
                  "transition-colors duration-100",
                  isSelected
                    ? "text-accent bg-accent-subtle"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-overlay"
                )}
                role="option"
                aria-selected={isSelected}
              >
                <Icon className="w-4 h-4" />
                <span className="flex-1">{option.label}</span>
                {isSelected && <Check className="w-4 h-4" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Simple toggle button variant (just switches between light/dark)
export function ThemeToggleSimple({ className }: ThemeToggleProps) {
  const { resolvedColorScheme, setColorScheme } = useTheme();

  const toggleTheme = () => {
    setColorScheme(resolvedColorScheme === "dark" ? "light" : "dark");
  };

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        "relative p-2 rounded-md",
        "text-text-muted hover:text-text-secondary",
        "hover:bg-surface-overlay",
        "transition-colors duration-150",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
        className
      )}
      aria-label={`Switch to ${resolvedColorScheme === "dark" ? "light" : "dark"} mode`}
    >
      <div className="relative w-5 h-5">
        {/* Sun icon */}
        <Sun
          className={cn(
            "absolute inset-0 w-5 h-5 transition-all duration-300",
            resolvedColorScheme === "dark"
              ? "opacity-0 rotate-90 scale-0"
              : "opacity-100 rotate-0 scale-100"
          )}
        />
        {/* Moon icon */}
        <Moon
          className={cn(
            "absolute inset-0 w-5 h-5 transition-all duration-300",
            resolvedColorScheme === "dark"
              ? "opacity-100 rotate-0 scale-100"
              : "opacity-0 -rotate-90 scale-0"
          )}
        />
      </div>
    </button>
  );
}
