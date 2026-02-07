import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // MAPS brand colors based on teal-theme.css
        maps: {
          blue: "#3B82F6",
          purple: "#8B5CF6",
          teal: "#14B8A6",
          "teal-dark": "#0F766E",
          "teal-light": "#5EEAD4",
          navy: "#1E3A5F",
          "navy-light": "#2E4A6F",
          gray: "#6B7280",
          "gray-light": "#E5E7EB",
          background: "#F9FAFB",
          surface: "#FFFFFF",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        lg: "0.75rem",
        xl: "1rem",
      },
      boxShadow: {
        soft: "0 4px 20px rgba(0, 0, 0, 0.05)",
        medium: "0 4px 25px rgba(0, 0, 0, 0.1)",
        strong: "0 10px 40px rgba(0, 0, 0, 0.15)",
      },
    },
  },
  plugins: [],
};

export default config;
