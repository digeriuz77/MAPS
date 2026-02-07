import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Design Direction: Sophistication & Trust + Warmth & Approachability
      // Color Foundation: Cool neutrals (slate) with teal accent for growth

      colors: {
        // Neutral foundation (cool slate - professional & trustworthy)
        neutral: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617",
        },

        // MAPS brand - teal for growth & learning
        primary: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6", // Main brand
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
          950: "#042f2e",
        },

        // Semantic colors - muted for professionalism
        success: {
          DEFAULT: "#10b981",
          light: "#d1fae5",
          bg: "#ecfdf5",
          text: "#065f46",
        },
        warning: {
          DEFAULT: "#f59e0b",
          light: "#fef3c7",
          bg: "#fffbeb",
          text: "#92400e",
        },
        error: {
          DEFAULT: "#ef4444",
          light: "#fee2e2",
          bg: "#fef2f2",
          text: "#991b1b",
        },
        info: {
          DEFAULT: "#3b82f6",
          light: "#dbeafe",
          bg: "#eff6ff",
          text: "#1e40af",
        },

        // Surfaces
        surface: {
          DEFAULT: "#ffffff",
          elevated: "#ffffff",
          sunken: "#f8fafc",
          border: "#e2e8f0",
        },
      },

      // Typography: Geometric sans (Inter) - modern, clean, readable
      fontFamily: {
        sans: [
          "var(--font-inter)",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: ["var(--font-geist-mono)", "ui-monospace", "SFMono-Regular", "Monaco", "Consolas", "monospace"],
      },

      // 4px Grid System
      spacing: {
        // Base grid values (explicit)
        "1": "0.25rem",   // 4px
        "2": "0.5rem",    // 8px
        "3": "0.75rem",   // 12px
        "4": "1rem",      // 16px
        "5": "1.25rem",   // 20px
        "6": "1.5rem",    // 24px
        "8": "2rem",      // 32px
        "10": "2.5rem",   // 40px
        "12": "3rem",     // 48px
        "16": "4rem",     // 64px
        "20": "5rem",     // 80px
      },

      // Border Radius: Sharp to Soft system (4px, 8px, 12px)
      borderRadius: {
        sm: "4px",
        DEFAULT: "8px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },

      // Depth: Subtle single shadows + surface color shifts
      boxShadow: {
        sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        DEFAULT: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
        md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
        xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
        none: "0",
      },

      // Animation: Fast, no bounce
      transitionDuration: {
        DEFAULT: "150ms",
        "150": "150ms",
        "200": "200ms",
        "250": "250ms",
        "300": "300ms",
      },

      transitionTimingFunction: {
        DEFAULT: "cubic-bezier(0.25, 1, 0.5, 1)",
        "in-out": "cubic-bezier(0.25, 1, 0.5, 1)",
      },

      // Typography Scale
      fontSize: {
        xs: ["0.75rem", { lineHeight: "1rem" }],     // 12px
        sm: ["0.875rem", { lineHeight: "1.25rem" }],   // 14px
        base: ["0.9375rem", { lineHeight: "1.5rem" }], // 15px
        lg: ["1.125rem", { lineHeight: "1.75rem" }],   // 18px
        xl: ["1.25rem", { lineHeight: "1.75rem" }],    // 20px
        "2xl": ["1.5rem", { lineHeight: "2rem" }],     // 24px
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }], // 30px
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],   // 36px
      },

      // Letter spacing for hierarchy
      letterSpacing: {
        tight: "-0.025em",
        normal: "0",
        wide: "0.025em",
        wider: "0.05em",
      },

      // Z-index layers
      zIndex: {
        dropdown: "100",
        sticky: "200",
        fixed: "300",
        modal: "400",
        popover: "500",
        tooltip: "600",
      },

      // Keyframes for animations
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-up": {
          from: { transform: "translateY(4px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        "slide-down": {
          from: { transform: "translateY(-4px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
      },
      animation: {
        "fade-in": "fade-in 150ms ease-out",
        "slide-up": "slide-up 200ms ease-out",
        "slide-down": "slide-down 200ms ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
