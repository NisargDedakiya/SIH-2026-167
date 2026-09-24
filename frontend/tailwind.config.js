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
        background: "#090D16",
        surface: "#101626",
        surfaceBorder: "#1E293B",
        cardBg: "#131B2E",
        radarCyan: {
          light: "#22D3EE",
          DEFAULT: "#06B6D4",
          dark: "#0891B2"
        },
        orbitTeal: {
          light: "#2DD4BF",
          DEFAULT: "#14B8A6",
          dark: "#0F766E"
        },
        satelliteGold: "#F59E0B",
        statusValid: "#10B981",
        statusWarn: "#F59E0B",
        statusError: "#EF4444"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
