/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      spacing: {
        '3.5': '0.875rem',
        '4.5': '1.125rem',
        '6.5': '1.625rem',
      },
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#2563eb', // Official ExpenseFlow AI Royal Blue
          600: '#1d4ed8',
          700: '#1e40af',
          800: '#1e3a8a',
          900: '#172554',
          950: '#0b132b',
        },
        cyanFlow: {
          400: '#22d3ee',
          500: '#06b6d4', // Official ExpenseFlow AI Cyan
          600: '#0891b2',
        },
        dark: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b', // Slate 800 Surface
          850: '#0f172a', // Slate 900 Surface
          900: '#0b1120', // Dark Slate Card Base
          950: '#020617', // Slate 950 Deep Space Black
        },
        // Official ExpenseFlow AI Color Language
        income: '#10b981',   // Emerald Green from logo arrow
        savings: '#06b6d4',  // Cyan Flow from logo ledger lines
        goals: '#2563eb',    // Royal Blue from logo brand icon
        expenses: '#f43f5e', // Rose Coral for outflows
        investments: '#10b981',
        debt: '#f97316',
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'edl-depth': '0 20px 48px -10px rgba(0, 0, 0, 0.65)',
        'edl-glow-brand': '0 0 30px rgba(37, 99, 235, 0.18)',
        'edl-glow-income': '0 0 30px rgba(16, 185, 129, 0.18)',
        'edl-glow-savings': '0 0 30px rgba(6, 182, 212, 0.18)',
        'edl-glow-expenses': '0 0 30px rgba(244, 63, 94, 0.18)',
        'edl-glow-goals': '0 0 30px rgba(37, 99, 235, 0.18)',
        'edl-glow-investments': '0 0 30px rgba(16, 185, 129, 0.18)',
        'edl-glow-debt': '0 0 30px rgba(249, 115, 22, 0.18)',
        'edl-card': '0 12px 32px -4px rgba(0, 0, 0, 0.45)',
        'edl-inset': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
      }
    },
  },
  plugins: [],
}
