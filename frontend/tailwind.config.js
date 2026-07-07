// Тематизируемые токены (brand/accent/ink/stone) читаются из CSS-переменных
// вида "R G B" (см. src/assets/main.css :root) — это единственный способ
// дать Tailwind и админ-панели "Тема оформления" (frontend/src/theme/presets.js)
// менять эти цвета в рантайме, а не только на этапе сборки. Формат
// rgb(var(...) / <alpha-value>) сохраняет поддержку модификаторов
// прозрачности (bg-brand-900/40 и т.п.).
function withOpacity(variable) {
  return ({ opacityValue }) =>
    opacityValue === undefined
      ? `rgb(var(${variable}))`
      : `rgb(var(${variable}) / ${opacityValue})`
}

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Аналогично цветам — читаются из CSS-переменных (см. main.css :root),
      // переключаются админ-панелью через applyFont() (src/theme/fonts.js).
      fontFamily: {
        display: 'var(--font-display)',
        sans: 'var(--font-display)',
        mono: 'var(--font-mono)',
      },
      colors: {
        brand: {
          900: withOpacity('--color-brand-900'),
          800: withOpacity('--color-brand-800'),
          700: withOpacity('--color-brand-700'),
        },
        accent: {
          400: withOpacity('--color-accent-400'),
          100: withOpacity('--color-accent-100'),
        },
        ink: {
          900: withOpacity('--color-ink-900'),
          600: withOpacity('--color-ink-600'),
        },
        stone: {
          50: withOpacity('--color-stone-50'),
          200: withOpacity('--color-stone-200'),
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
