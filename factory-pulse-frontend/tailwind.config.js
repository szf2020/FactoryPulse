/** @type {import('tailwindcss').Config} */
export default {
  // Enable dark mode via a specific class on the root element
  darkMode: 'class',

  // Paths to all files that contain Tailwind class names
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],

  theme: {
    extend: {
      // Extended Color Palette
      colors: {
        dark: {
          900: '#020617', // Deep background (matches Slate 950)
          800: '#0f172a', // Card/Panel background (matches Slate 900)
          700: '#1e293b', // Borders & Separators (matches Slate 800)
        },
        // Custom Neon Palette for Dashboard Indicators
        neon: {
          blue: '#3b82f6',
          green: '#10b981',
          orange: '#f59e0b',
          purple: '#8b5cf6',
        }
      },
      // Global Font Stack
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}