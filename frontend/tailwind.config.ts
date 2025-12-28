import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    // Include local workspace packages
    "../packages/*/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Platform-specific color palette - "Precision Control Room"
      // Uses CSS variables for theme switching support
      //
      // Token Mapping (design tokens → Tailwind):
      // - accent     → primary action color (buttons, links)
      // - status-*   → semantic feedback colors
      // - surface-*  → background layers
      // - text-*     → typography hierarchy
      // - border-*   → dividers and outlines
      colors: {
        // Base surfaces - dynamic via CSS variables
        background: "hsl(var(--color-background))",
        surface: {
          DEFAULT: "hsl(var(--color-surface))",
          elevated: "hsl(var(--color-surface-elevated))",
          overlay: "hsl(var(--color-surface-overlay))",
          subtle: "hsl(var(--color-surface-subtle))",
        },
        overlay: "hsl(var(--color-overlay))",
        // Borders and dividers
        border: {
          DEFAULT: "hsl(var(--color-border))",
          subtle: "hsl(var(--color-border-subtle))",
          strong: "hsl(var(--color-border-strong))",
        },
        input: "hsl(var(--color-border))",
        // Text hierarchy
        text: {
          primary: "hsl(var(--color-text-primary))",
          secondary: "hsl(var(--color-text-secondary))",
          muted: "hsl(var(--color-text-muted))",
          inverse: "hsl(var(--color-text-inverse))",
        },
        // Foreground colors (for component text on colored backgrounds)
        foreground: "hsl(var(--color-text-primary))",
        "muted-foreground": "hsl(var(--color-text-muted))",
        // Status accents - sharp, intentional (semantic colors)
        status: {
          success: "hsl(var(--color-status-success))",
          warning: "hsl(var(--color-status-warning))",
          error: "hsl(var(--color-status-error))",
          info: "hsl(var(--color-status-info))",
        },
        // Primary action color - maps to accent
        primary: {
          DEFAULT: "hsl(var(--color-accent))",
          foreground: "hsl(var(--color-text-inverse))",
        },
        // Secondary action color - subtle variant
        secondary: {
          DEFAULT: "hsl(var(--color-surface-overlay))",
          foreground: "hsl(var(--color-text-primary))",
        },
        // Destructive action color - maps to status-error
        destructive: {
          DEFAULT: "hsl(var(--color-status-error))",
          foreground: "hsl(var(--color-text-inverse))",
        },
        // Accent color - primary brand color
        accent: {
          DEFAULT: "hsl(var(--color-accent))",
          subtle: "var(--color-accent-subtle)",
          hover: "hsl(var(--color-accent-hover))",
          muted: "hsl(var(--color-accent-muted))",
          foreground: "hsl(var(--color-text-inverse))",
        },
        // Secondary accent - amber for highlights
        highlight: {
          DEFAULT: "hsl(var(--color-highlight))",
          subtle: "hsl(var(--color-highlight) / 0.15)",
        },
        // Portal-specific colors
        "portal-admin": "hsl(var(--color-portal-admin))",
        "portal-tenant": "hsl(var(--color-portal-tenant))",
        "portal-reseller": "hsl(var(--color-portal-reseller))",
        "portal-technician": "hsl(var(--color-portal-technician))",
        "portal-management": "hsl(var(--color-portal-management))",
      },
      // Typography - authoritative yet modern
      fontFamily: {
        sans: ["var(--font-family-sans)", "var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-family-mono)", "var(--font-geist-mono)", "ui-monospace", "monospace"],
        display: ["var(--font-display)", "var(--font-family-sans)", "system-ui", "sans-serif"],
      },
      fontSize: {
        // Precise type scale
        "2xs": ["0.65rem", { lineHeight: "1rem" }],
        xs: ["0.75rem", { lineHeight: "1rem" }],
        sm: ["0.8125rem", { lineHeight: "1.25rem" }],
        base: ["0.875rem", { lineHeight: "1.5rem" }],
        lg: ["1rem", { lineHeight: "1.5rem" }],
        xl: ["1.125rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.25rem", { lineHeight: "1.75rem" }],
        "3xl": ["1.5rem", { lineHeight: "2rem" }],
        "4xl": ["2rem", { lineHeight: "2.5rem" }],
        "5xl": ["2.5rem", { lineHeight: "3rem" }],
      },
      // Spacing system
      spacing: {
        "4.5": "1.125rem",
        "13": "3.25rem",
        "15": "3.75rem",
        "18": "4.5rem",
        "22": "5.5rem",
        "26": "6.5rem",
        "30": "7.5rem",
      },
      // Animation presets
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "fade-up": "fadeUp 0.4s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "slide-in-left": "slideInLeft 0.3s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 1.5s linear infinite",
        "status-blink": "statusBlink 1.5s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        statusBlink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },
      // Shadows for depth - uses CSS variable for theme-aware shadows
      boxShadow: {
        glow: "0 0 20px -5px hsl(var(--color-accent) / 0.3)",
        "glow-sm": "0 0 10px -3px hsl(var(--color-accent) / 0.25)",
        "inner-glow": "inset 0 1px 0 0 hsl(var(--color-border-strong))",
        card: "0 1px 3px 0 hsl(var(--shadow-color) / 0.5), 0 1px 2px -1px hsl(var(--shadow-color) / 0.5)",
        "card-hover":
          "0 4px 6px -1px hsl(var(--shadow-color) / 0.5), 0 2px 4px -2px hsl(var(--shadow-color) / 0.5)",
      },
      // Border radius
      borderRadius: {
        sm: "0.25rem",
        DEFAULT: "0.375rem",
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
      },
      // Backdrop blur
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

export default config;
