/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        tcs: {
          navy: '#00142D',
          dark: '#071324',
          card: '#0d1b2a',
          surface: '#12233f',
          blue: '#0076CE',
          cyan: '#00A3E0',
          accent: '#005a9c',
          border: '#1b3252',
          light: '#e2e8f0',
          muted: '#94a3b8',
        }
      }
    },
  },
  plugins: [],
}

