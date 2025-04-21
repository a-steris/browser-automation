/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "./static/**/*.{html,js}"
  ],
  safelist: [
    'bg-gradient-to-r',
    'from-teal-500',
    'via-cyan-600',
    'to-indigo-700',
    'hover:bg-teal-50',
    'text-teal-700',
    'text-teal-100',
    'ring-teal-500'
  ],
  theme: {
    extend: {
      colors: {
        teal: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          500: '#14b8a6',
          700: '#0f766e',
        },
        cyan: {
          600: '#0891b2',
        },
        indigo: {
          700: '#4338ca',
        }
      }
    }
  },
  plugins: [],
}
