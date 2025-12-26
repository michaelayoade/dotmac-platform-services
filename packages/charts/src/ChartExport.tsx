/**
 * Chart Export Utilities
 *
 * Export charts to PNG or SVG format
 */

"use client";

import { useRef, useCallback, type ReactNode, type RefObject } from "react";
import { Download, Image, FileCode } from "lucide-react";
import { chartExportColors } from "./theme";

// ============================================================================
// Types
// ============================================================================

export type ExportFormat = "png" | "svg";

export interface ChartExportOptions {
  /** File name without extension */
  filename?: string;
  /** Export format */
  format?: ExportFormat;
  /** Background color for PNG export */
  backgroundColor?: string;
  /** Scale factor for PNG export (higher = better quality) */
  scale?: number;
  /** Width override */
  width?: number;
  /** Height override */
  height?: number;
}

export interface ChartContainerProps {
  /** Chart content */
  children: ReactNode;
  /** Chart title for filename */
  title?: string;
  /** Show export buttons */
  showExportButtons?: boolean;
  /** Custom export button renderer */
  renderExportButton?: (props: {
    exportToPng: (options?: Partial<ChartExportOptions>) => Promise<void>;
    exportToSvg: (options?: Partial<ChartExportOptions>) => void;
  }) => ReactNode;
  /** CSS class */
  className?: string;
  /** Default export options */
  exportOptions?: Partial<ChartExportOptions>;
}

// ============================================================================
// Export Functions
// ============================================================================

/**
 * Export a DOM element containing an SVG chart to PNG
 */
export async function exportChartToPng(
  element: HTMLElement,
  options: ChartExportOptions = {}
): Promise<void> {
  // Detect dark mode from document class or system preference
  const isDarkMode =
    document.documentElement.classList.contains("dark") ||
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  const defaultBg = isDarkMode ? chartExportColors.dark : chartExportColors.light;

  const {
    filename = "chart",
    backgroundColor = defaultBg,
    scale = 2,
    width,
    height,
  } = options;

  // Find the SVG element
  const svg = element.querySelector("svg");
  if (!svg) {
    console.error("No SVG element found in chart container");
    return;
  }

  // Clone the SVG to avoid modifying the original
  const clonedSvg = svg.cloneNode(true) as SVGElement;

  // Get dimensions
  const svgWidth = width || svg.clientWidth || 600;
  const svgHeight = height || svg.clientHeight || 400;

  // Set explicit dimensions on cloned SVG
  clonedSvg.setAttribute("width", String(svgWidth));
  clonedSvg.setAttribute("height", String(svgHeight));

  // Add background
  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("width", "100%");
  rect.setAttribute("height", "100%");
  rect.setAttribute("fill", backgroundColor);
  clonedSvg.insertBefore(rect, clonedSvg.firstChild);

  // Serialize SVG
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(clonedSvg);
  const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const svgUrl = URL.createObjectURL(svgBlob);

  // Create image and canvas
  const img = new window.Image();
  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = svgWidth * scale;
    canvas.height = svgHeight * scale;

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      console.error("Could not get canvas context");
      URL.revokeObjectURL(svgUrl);
      return;
    }

    // Scale for higher resolution
    ctx.scale(scale, scale);

    // Draw image
    ctx.drawImage(img, 0, 0, svgWidth, svgHeight);

    // Convert to PNG and download
    canvas.toBlob((blob) => {
      if (!blob) {
        console.error("Could not create PNG blob");
        return;
      }

      const url = URL.createObjectURL(blob);
      downloadFile(url, `${filename}.png`);
      URL.revokeObjectURL(url);
      URL.revokeObjectURL(svgUrl);
    }, "image/png");
  };

  img.onerror = () => {
    console.error("Failed to load SVG as image");
    URL.revokeObjectURL(svgUrl);
  };

  img.src = svgUrl;
}

/**
 * Export a DOM element containing an SVG chart to SVG file
 */
export function exportChartToSvg(
  element: HTMLElement,
  options: ChartExportOptions = {}
): void {
  // Detect dark mode from document class or system preference
  const isDarkMode =
    document.documentElement.classList.contains("dark") ||
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  const defaultBg = isDarkMode ? chartExportColors.dark : chartExportColors.light;

  const { filename = "chart", backgroundColor = defaultBg, width, height } = options;

  // Find the SVG element
  const svg = element.querySelector("svg");
  if (!svg) {
    console.error("No SVG element found in chart container");
    return;
  }

  // Clone the SVG
  const clonedSvg = svg.cloneNode(true) as SVGElement;

  // Get dimensions
  const svgWidth = width || svg.clientWidth || 600;
  const svgHeight = height || svg.clientHeight || 400;

  // Set explicit dimensions
  clonedSvg.setAttribute("width", String(svgWidth));
  clonedSvg.setAttribute("height", String(svgHeight));
  clonedSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");

  // Add background
  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("width", "100%");
  rect.setAttribute("height", "100%");
  rect.setAttribute("fill", backgroundColor);
  clonedSvg.insertBefore(rect, clonedSvg.firstChild);

  // Serialize and download
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(clonedSvg);
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  downloadFile(url, `${filename}.svg`);
  URL.revokeObjectURL(url);
}

/**
 * Helper to download a file
 */
function downloadFile(url: string, filename: string): void {
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Hook to enable chart export functionality
 */
export function useChartExport(
  ref: RefObject<HTMLElement>,
  defaultOptions: Partial<ChartExportOptions> = {}
) {
  const exportToPng = useCallback(
    async (options: Partial<ChartExportOptions> = {}) => {
      if (!ref.current) return;
      await exportChartToPng(ref.current, { ...defaultOptions, ...options });
    },
    [ref, defaultOptions]
  );

  const exportToSvg = useCallback(
    (options: Partial<ChartExportOptions> = {}) => {
      if (!ref.current) return;
      exportChartToSvg(ref.current, { ...defaultOptions, ...options });
    },
    [ref, defaultOptions]
  );

  return { exportToPng, exportToSvg };
}

// ============================================================================
// Export Button Component
// ============================================================================

export interface ExportButtonProps {
  /** Export to PNG handler */
  onExportPng?: () => void;
  /** Export to SVG handler */
  onExportSvg?: () => void;
  /** Show only specific format */
  format?: ExportFormat | "both";
  /** Button size */
  size?: "sm" | "md";
  /** CSS class */
  className?: string;
}

export function ExportButton({
  onExportPng,
  onExportSvg,
  format = "both",
  size = "sm",
  className,
}: ExportButtonProps) {
  const sizeClass = size === "sm" ? "p-1.5" : "p-2";
  const iconSize = size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4";

  return (
    <div className={`flex items-center gap-1 ${className || ""}`}>
      {(format === "both" || format === "png") && onExportPng && (
        <button
          type="button"
          onClick={onExportPng}
          className={`${sizeClass} rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors`}
          title="Export as PNG"
        >
          <Image className={iconSize} />
        </button>
      )}
      {(format === "both" || format === "svg") && onExportSvg && (
        <button
          type="button"
          onClick={onExportSvg}
          className={`${sizeClass} rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors`}
          title="Export as SVG"
        >
          <FileCode className={iconSize} />
        </button>
      )}
    </div>
  );
}

// ============================================================================
// Chart Container with Export
// ============================================================================

/**
 * Wrapper component that adds export functionality to any chart
 */
export function ExportableChart({
  children,
  title = "chart",
  showExportButtons = true,
  renderExportButton,
  className,
  exportOptions = {},
}: ChartContainerProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const { exportToPng, exportToSvg } = useChartExport(chartRef, {
    filename: title.toLowerCase().replace(/\s+/g, "-"),
    ...exportOptions,
  });

  return (
    <div className={`relative ${className || ""}`}>
      {showExportButtons && !renderExportButton && (
        <div className="absolute top-2 right-2 z-10 opacity-0 hover:opacity-100 transition-opacity">
          <ExportButton
            onExportPng={exportToPng}
            onExportSvg={exportToSvg}
          />
        </div>
      )}

      {renderExportButton?.({ exportToPng, exportToSvg })}

      <div ref={chartRef}>{children}</div>
    </div>
  );
}

export default ExportableChart;
