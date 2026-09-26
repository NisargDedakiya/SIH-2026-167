/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        /* Core backgrounds */
        background:  "#0B0F16",
        "bg-deep":   "#070A0F",
        "bg-raised": "#10151D",

        /* Surfaces */
        surface:     "#111821",
        "surface-1": "#151C26",
        "surface-2": "#19212C",
        "surface-3": "#1D2533",

        /* Borders */
        "border-0":  "#1C2535",
        "border-1":  "#25303D",
        "border-2":  "#303B49",
        "border-3":  "#3D4A5C",

        /* Accent — Electric Cyan */
        accent:      "#06B6D4",
        "accent-light": "#22D3EE",
        "accent-dim":   "#0E7490",

        /* Semantic */
        success:     "#10B981",
        warning:     "#F59E0B",
        error:       "#EF4444",
        info:        "#3B82F6",

        /* Legacy compat */
        radarCyan: {
          light:   "#22D3EE",
          DEFAULT: "#06B6D4",
          dark:    "#0891B2",
        },
        orbitTeal: {
          light:   "#2DD4BF",
          DEFAULT: "#14B8A6",
          dark:    "#0F766E",
        },
        satelliteGold: "#F59E0B",
        surfaceBorder: "#25303D",
        cardBg:        "#151C26",
        statusValid:   "#10B981",
        statusWarn:    "#F59E0B",
        statusError:   "#EF4444",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        "2xs": ["10px", { lineHeight: "14px" }],
      },
      borderRadius: {
        "4xl": "28px",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          from: { opacity: "0", transform: "translateX(12px)" },
          to:   { opacity: "1", transform: "translateX(0)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0.4" },
        },
        shimmer: {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "scanning": {
          "0%":   { transform: "translateY(-100%)", opacity: "0" },
          "10%":  { opacity: "0.8" },
          "90%":  { opacity: "0.8" },
          "100%": { transform: "translateY(100%)", opacity: "0" },
        },
      },
      animation: {
        "fade-in":        "fade-in 0.25s ease-out forwards",
        "slide-in-right": "slide-in-right 0.25s ease-out forwards",
        "pulse-dot":      "pulse-dot 2s infinite",
        shimmer:          "shimmer 1.8s infinite",
        scanning:         "scanning 3s linear infinite",
      },
      boxShadow: {
        accent:    "0 0 24px rgba(6,182,212,0.12)",
        "accent-lg": "0 0 48px rgba(6,182,212,0.20)",
        surface:   "0 4px 12px rgba(0,0,0,0.50)",
        "inner-top": "inset 0 1px 0 rgba(255,255,255,0.04)",
      },
    },
  },
  plugins: [],
};
