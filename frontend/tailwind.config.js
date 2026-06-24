/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Golos Text"', 'sans-serif'],
        sans: ['"Golos Text"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        brand: {
          900: '#111111',
          800: '#3A3A3A',
          700: '#5C5C5C',
        },
        accent: {
          400: '#FBBF24',
          100: '#ECEAE5',
        },
        ink: {
          900: '#111111',
          600: '#5C5955',
        },
        stone: {
          50: '#F4F3F0',
          200: '#E3E1DC',
        },
        danger: '#B91C1C',
        success: '#15803D',
      },
      borderRadius: {
        DEFAULT: '1px',
        sm: '1px',
        md: '2px',
        lg: '2px',
        xl: '2px',
        '2xl': '2px',
        '3xl': '2px',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(17, 17, 17, 0.04)',
        md: '0 2px 5px rgba(17, 17, 17, 0.06)',
        lg: '0 6px 16px rgba(17, 17, 17, 0.08)',
      },
    },
  },
  plugins: [],
}
