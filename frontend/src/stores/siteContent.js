import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '../api'
import { applyTheme, THEME_PRESETS } from '../theme/presets'

/**
 * Контент сайта, редактируемый через /admin/settings (CMS).
 * Значения по умолчанию совпадают с backend-дефолтами в SiteContent —
 * до первой загрузки шапка/футер/главная уже выглядят как обычно.
 */
function defaultContent() {
  return {
    header: { brand_name: 'Сайтама', brand_tagline: 'Барбершоп' },
    hero: {
      variant: 'split',
      eyebrow: 'С 2019 года — современное барберство',
      title: 'Чёткий\nсрез.\nТихий\nзал.',
      subtitle: 'Без навязанных услуг и спешки. Точная стрижка и чистый финиш — запись с точностью до минуты.',
      primary_button: 'Записаться',
      secondary_button: 'Услуги и цены',
      photo_url: null,
    },
    features: {
      eyebrow: 'Почему «Сайтама»',
      title: 'Барбершоп без лишнего.',
      items: [
        { title: 'Точная стрижка', text: 'Каждый мастер начинает с консультации, а не с догадок. Вы уходите ровно с тем образом, который просили.' },
        { title: 'Без спешки', text: 'Между записями достаточно времени на каждого клиента. Никакого двойного бронирования и поторапливания.' },
        { title: 'Чистый финиш', text: 'Каждая стрижка заканчивается аккуратным оформлением линии шеи — это стандарт, а не платная опция.' },
      ],
    },
    services: {
      eyebrow: 'Услуги и цены',
      title: 'Меню.',
      note: 'Цены в рублях\nОплата картой и наличными',
    },
    masters: {
      eyebrow: 'Наши мастера',
      title: 'Мастера, которым доверяют.',
    },
    cta: {
      eyebrow: 'Готовы, когда будете вы',
      title: 'Займите место.',
      subtitle: 'Выберите мастера, дату и время. Подтверждение приходит сразу после записи.',
      button_label: 'Записаться',
    },
    footer: {
      tagline: 'Чёткий срез, тихий зал. Современное барберство с точностью до минуты.',
      address: 'ул. Тверская, 12\nМосква\n+7 (495) 123-45-67',
      hours: 'Пн–Пт 9:00–20:00\nСб 10:00–18:00\nВс — выходной',
      social_links: [
        { label: 'Instagram ↗', url: '#' },
        { label: 'Google Карты ↗', url: '#' },
        { label: 'Сертификаты ↗', url: '#' },
      ],
      bottom_note: 'Запись онлайн · Оплата картой и наличными',
    },
    theme: { preset: 'default', colors: { ...THEME_PRESETS.default.colors } },
  }
}

export const useSiteContentStore = defineStore('siteContent', () => {
  const content = ref(defaultContent())
  const loaded = ref(false)
  applyTheme(content.value.theme.colors)

  async function load(force = false) {
    if (loaded.value && !force) return
    try {
      const { data } = await settingsApi.get()
      content.value = data
      applyTheme(data.theme?.colors)
    } finally {
      loaded.value = true
    }
  }

  function set(data) {
    content.value = data
    applyTheme(data.theme?.colors)
  }

  return { content, loaded, load, set }
})
