const DESCRIPTION_META_NAME = 'description'
const FAVICON_LINK_ID = 'site-favicon'

/**
 * Применяет <title>, <meta name="description"> и favicon из настроек сайта
 * (Админка → Настройки → SEO) — тот же приём, что applyTheme/applyFont
 * (theme/presets.js, theme/fonts.js): index.html хранит статичный дефолт
 * для самого первого рендера/краулера без JS, а дальше значения из БД
 * применяются здесь через прямые DOM-манипуляции (SPA, серверного рендера
 * нет).
 */
export function applySeo(seo) {
  if (!seo) return

  if (seo.title) document.title = seo.title

  let descriptionTag = document.querySelector(`meta[name="${DESCRIPTION_META_NAME}"]`)
  if (!descriptionTag) {
    descriptionTag = document.createElement('meta')
    descriptionTag.setAttribute('name', DESCRIPTION_META_NAME)
    document.head.appendChild(descriptionTag)
  }
  descriptionTag.setAttribute('content', seo.description || '')

  let faviconLink = document.getElementById(FAVICON_LINK_ID)
  if (!faviconLink) {
    faviconLink = document.createElement('link')
    faviconLink.id = FAVICON_LINK_ID
    faviconLink.rel = 'icon'
    document.head.appendChild(faviconLink)
  }
  if (seo.favicon_url) {
    // Загруженный через ImageUpload.vue файл может быть PNG/JPEG/WebP/GIF
    // (см. ImageUpload.vue accept) — type="image/svg+xml" из index.html
    // тут был бы враньём, убираем его, браузер сам разберётся по содержимому.
    faviconLink.removeAttribute('type')
    faviconLink.href = seo.favicon_url
  } else {
    faviconLink.type = 'image/svg+xml'
    faviconLink.href = '/favicon.svg'
  }
}
