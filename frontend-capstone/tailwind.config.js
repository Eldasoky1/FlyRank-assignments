/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // base design tokens (FE-05): semantic palette used across the app
        ink: { DEFAULT: '#0f172a', mute: '#64748b' },
        paper: { DEFAULT: '#f8fafc', elev: '#ffffff' },
        accent: { DEFAULT: '#2563eb', soft: '#eff6ff', fg: '#ffffff' },
        danger: { DEFAULT: '#dc2626', soft: '#fef2f2' },
        ok: { DEFAULT: '#16a34a', soft: '#f0fdf4' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        control: '0.75rem',
        chip: '9999px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(15,23,42,0.08)',
      },
    },
  },
  plugins: [],
}