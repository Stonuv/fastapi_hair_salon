/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Playfair Display', 'serif'],
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        brand: {
          900: '#78350F',
          800: '#92400E',
          700: '#B45309',
        },
        accent: {
          400: '#FBBF24',
          100: '#FEF3C7',
        },
        ink: {
          900: '#2B1607',
          600: '#52453B',
        },
        stone: {
          50: '#FBF8F3',
          200: '#E7DDD0',
        },
        danger: '#B91C1C',
        success: '#15803D',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(43, 22, 7, 0.06)',
        md: '0 4px 6px rgba(43, 22, 7, 0.08)',
        lg: '0 10px 15px rgba(43, 22, 7, 0.1)',
      },
    },
  },
  plugins: [],
}
