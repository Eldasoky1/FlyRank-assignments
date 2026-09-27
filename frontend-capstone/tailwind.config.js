/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // base design tokens (FE-05): semantic palette used across the app
        ink: { DEFAULT: '#18211f', mute: '#6c7771' },
        paper: { DEFAULT: '#f4f1eb', elev: '#fffdf9' },
        accent: { DEFAULT: '#1c7469', soft: '#e7f2ee', fg: '#fffdf9' },
        danger: { DEFAULT: '#b7443e', soft: '#fbeceb' },
        ok: { DEFAULT: '#397957', soft: '#e8f3e9' },
      },
      fontFamily: {
        sans: ['Trebuchet MS', 'Verdana', 'sans-serif'],
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