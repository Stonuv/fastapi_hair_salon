/**
 * Пары шрифтов (Админка → Настройки → Тема). Только готовые пары — без
 * произвольного ввода названия шрифта, чтобы не тянуть невалидные Google
 * Fonts URL и не ломать первую отрисовку. "golos" зеркалит текущий
 * хардкод в index.html / tailwind.config.js — если админ ничего не
 * менял, сайт выглядит как сейчас.
 */
export const FONT_PRESETS = {
  golos: {
    label: 'Golos + JetBrains',
    display: '"Golos Text", sans-serif',
    mono: '"JetBrains Mono", monospace',
    href: 'https://fonts.googleapis.com/css2?family=Golos+Text:wght@500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap',
  },
  archivo: {
    label: 'Archivo + Space Mono',
    display: '"Archivo", sans-serif',
    mono: '"Space Mono", monospace',
    href: 'https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800;900&family=Space+Mono:wght@400;700&display=swap',
  },
  manrope: {
    label: 'Manrope + IBM Plex Mono',
    display: '"Manrope", sans-serif',
    mono: '"IBM Plex Mono", monospace',
    href: 'https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;700&display=swap',
  },
  grotesk: {
    label: 'Space Grotesk + Space Mono',
    display: '"Space Grotesk", sans-serif',
    mono: '"Space Mono", monospace',
    href: 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap',
  },
  inter: {
    label: 'Inter + Roboto Mono',
    display: '"Inter", sans-serif',
    mono: '"Roboto Mono", monospace',
    href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Roboto+Mono:wght@400;500;700&display=swap',
  },
}

const LINK_ID = 'theme-font-link'

/** Переключает CSS-переменные шрифтов и подгружает нужный Google Fonts стиль. */
export function applyFont(key) {
  const preset = FONT_PRESETS[key] || FONT_PRESETS.golos
  const root = document.documentElement
  root.style.setProperty('--font-display', preset.display)
  root.style.setProperty('--font-mono', preset.mono)

  let link = document.getElementById(LINK_ID)
  if (!link) {
    link = document.createElement('link')
    link.id = LINK_ID
    link.rel = 'stylesheet'
    document.head.appendChild(link)
  }
  if (link.href !== preset.href) link.href = preset.href
}
