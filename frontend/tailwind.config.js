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
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6', // Aurora Purple
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
          950: '#2e1065',
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
          800: '#151c2e', // Deep Navy-Slate
          850: '#101424',
          900: '#0b0f19', // Dark Slate Card Base
          950: '#04060d', // Ultra Deep Space black
        },
        // EDL Color Language
        income: '#05b074',
        savings: '#00d2fc',
        goals: '#8b5cf6',
        expenses: '#fa5f70',
        investments: '#ffb000',
        debt: '#f97316',
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'edl-depth': '0 20px 48px -10px rgba(0, 0, 0, 0.65)',
        'edl-glow-brand': '0 0 30px rgba(139, 92, 246, 0.15)',
        'edl-glow-income': '0 0 30px rgba(5, 176, 116, 0.15)',
        'edl-glow-savings': '0 0 30px rgba(0, 210, 252, 0.15)',
        'edl-glow-expenses': '0 0 30px rgba(250, 95, 112, 0.15)',
        'edl-glow-goals': '0 0 30px rgba(139, 92, 246, 0.15)',
        'edl-glow-investments': '0 0 30px rgba(255, 176, 0, 0.15)',
        'edl-glow-debt': '0 0 30px rgba(249, 115, 22, 0.15)',
        'edl-card': '0 12px 32px -4px rgba(0, 0, 0, 0.45)',
        'edl-inset': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
      }
    },
  },
  plugins: [],
}
