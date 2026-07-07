/**
 * Пресеты темы оформления (Админка → Настройки → Тема). Ключи и значения
 * по умолчанию зеркалят backend ThemeColors (schemas/site_settings.py) —
 * "default" совпадает с текущими хардкод-значениями в tailwind.config.js /
 * assets/main.css, поэтому если админ ничего не менял, сайт выглядит как
 * сейчас.
 */
export const THEME_TOKENS = [
  { key: 'brand_900', label: 'Основной тёмный (кнопки, текст)' },
  { key: 'brand_800', label: 'Основной — hover' },
  { key: 'brand_700', label: 'Основной — приглушённый' },
  { key: 'accent_400', label: 'Акцент' },
  { key: 'accent_100', label: 'Акцент — мягкий фон' },
  { key: 'ink_900', label: 'Заголовки' },
  { key: 'ink_600', label: 'Основной текст' },
  { key: 'stone_50', label: 'Фон страницы' },
  { key: 'stone_200', label: 'Границы, разделители' },
]

export const THEME_PRESETS = {
  default: {
    label: 'Чёрный и бежевый',
    colors: {
      brand_900: '#111111',
      brand_800: '#3A3A3A',
      brand_700: '#5C5C5C',
      accent_400: '#FBBF24',
      accent_100: '#ECEAE5',
      ink_900: '#111111',
      ink_600: '#5C5955',
      stone_50: '#F4F3F0',
      stone_200: '#E3E1DC',
    },
  },
  coffee: {
    label: 'Кофе и карамель',
    colors: {
      brand_900: '#2B1B12',
      brand_800: '#4A3226',
      brand_700: '#6B4F3D',
      accent_400: '#C08A4E',
      accent_100: '#F1E4D2',
      ink_900: '#2B1B12',
      ink_600: '#6B5B4F',
      stone_50: '#F7F1E8',
      stone_200: '#E6D8C3',
    },
  },
  slate: {
    label: 'Графит и бирюза',
    colors: {
      brand_900: '#1E2530',
      brand_800: '#3A4453',
      brand_700: '#57626F',
      accent_400: '#2FA6A6',
      accent_100: '#DCEEEC',
      ink_900: '#1E2530',
      ink_600: '#5B6673',
      stone_50: '#F2F4F6',
      stone_200: '#DEE3E8',
    },
  },
}

function hexToRgbTriplet(hex) {
  const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex || '')
  if (!m) return '0 0 0'
  return m.slice(1).map((h) => parseInt(h, 16)).join(' ')
}

/** Применяет цвета темы ко всему документу через CSS-переменные (см. main.css). */
export function applyTheme(colors) {
  if (!colors) return
  const root = document.documentElement
  for (const { key } of THEME_TOKENS) {
    if (!colors[key]) continue
    const varName = `--color-${key.replace(/_/g, '-')}`
    root.style.setProperty(varName, hexToRgbTriplet(colors[key]))
  }
}

/** Находит совпадающий пресет для набора цветов, либо null (значит "custom"). */
export function matchPreset(colors) {
  if (!colors) return null
  for (const [name, preset] of Object.entries(THEME_PRESETS)) {
    if (THEME_TOKENS.every(({ key }) => preset.colors[key].toLowerCase() === colors[key]?.toLowerCase())) {
      return name
    }
  }
  return null
}
