import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f6f7f9",
          100: "#eceef2",
          200: "#d4d8e0",
          300: "#a8b0bf",
          400: "#76819a",
          500: "#4f5a76",
          600: "#37405a",
          700: "#262d44",
          800: "#181d32",
          900: "#0c1024",
        },
        forge: {
          green: "#22c55e",
          red: "#ef4444",
          amber: "#f59e0b",
          accent: "#7c3aed",
          ice: "#22d3ee",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(124, 58, 237, 0.4), 0 8px 32px -8px rgba(34, 211, 238, 0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
