import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eefbf4",
          100: "#d6f5e4",
          200: "#b0ebcc",
          300: "#7dd9ad",
          400: "#3dd68c",
          500: "#22b872",
          600: "#17965c",
          700: "#14774b",
          800: "#145e3e",
          900: "#124d35",
        },
        surface: {
          DEFAULT: "#0a0c0f",
          raised: "#10141a",
          card: "#141a22",
          hover: "#1c2430",
          border: "#262f3c",
          muted: "#8b949e",
        },
        ink: {
          DEFAULT: "#e8eaed",
          soft: "#b4bcc8",
          faint: "#6b7380",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset",
        lift: "0 8px 24px -12px rgba(0,0,0,0.55)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.45s ease-out both",
        "fade-in": "fade-in 0.35s ease-out both",
        shimmer: "shimmer 1.6s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
