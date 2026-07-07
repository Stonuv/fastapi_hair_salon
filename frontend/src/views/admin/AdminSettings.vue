<template>
  <div>
    <Skeleton v-if="loading" height="h-96" />

    <div v-else class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_660px] lg:items-start">
      <form class="space-y-6" @submit.prevent="save">
      <BaseCard>
        <StepTitle n="1" title="Шапка сайта" />
        <div class="grid gap-4 sm:grid-cols-2">
          <BaseInput v-model="form.header.brand_name" label="Название бренда" required />
          <BaseInput v-model="form.header.brand_tagline" label="Подпись под названием" required />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="2" title="Главный экран" />
        <div class="space-y-4">
          <div>
            <p class="mb-2 text-sm font-medium text-ink-900">Дизайн главного экрана</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="v in heroVariants" :key="v.value" type="button"
                class="border px-3 py-2 text-left font-mono text-xs uppercase tracking-wide transition-colors"
                :class="form.hero.variant === v.value
                  ? 'border-brand-900 bg-brand-900 text-stone-50'
                  : 'border-stone-200 text-ink-600 hover:border-brand-900'"
                @click="form.hero.variant = v.value"
              >
                {{ v.label }}
              </button>
            </div>
          </div>
          <BaseInput v-model="form.hero.eyebrow" label="Надпись над заголовком" />
          <BaseInput v-model="form.hero.title" as="textarea" :rows="3" label="Заголовок" hint="Каждая строка — перенос строки в заголовке" required />
          <BaseInput v-model="form.hero.subtitle" as="textarea" label="Подзаголовок" />
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseInput v-model="form.hero.primary_button" label="Текст основной кнопки" required />
            <BaseInput v-model="form.hero.secondary_button" label="Текст второй кнопки" required />
          </div>
          <BaseInput v-model="form.hero.photo_url" label="Фото справа (URL)" placeholder="https://…" hint="Если не указано — показывается заглушка" />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="3" title="Блок «Почему мы»" />
        <div class="space-y-4">
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseInput v-model="form.features.eyebrow" label="Надпись над заголовком" />
            <BaseInput v-model="form.features.title" label="Заголовок" required />
          </div>
          <div v-for="(item, i) in form.features.items" :key="i" class="grid gap-3 border-t border-stone-200 pt-4 sm:grid-cols-2">
            <BaseInput v-model="item.title" :label="`Карточка ${i + 1} — заголовок`" required />
            <BaseInput v-model="item.text" :label="`Карточка ${i + 1} — текст`" as="textarea" :rows="2" required />
          </div>
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="4" title="Услуги и цены" />
        <div class="grid gap-4 sm:grid-cols-2">
          <BaseInput v-model="form.services.eyebrow" label="Надпись над заголовком" />
          <BaseInput v-model="form.services.title" label="Заголовок" required />
          <BaseInput v-model="form.services.note" as="textarea" :rows="2" label="Примечание справа" class="sm:col-span-2" />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="5" title="Блок «Мастера»" />
        <div class="grid gap-4 sm:grid-cols-2">
          <BaseInput v-model="form.masters.eyebrow" label="Надпись над заголовком" />
          <BaseInput v-model="form.masters.title" label="Заголовок" required />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="6" title="Призыв к действию" />
        <div class="space-y-4">
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseInput v-model="form.cta.eyebrow" label="Надпись над заголовком" />
            <BaseInput v-model="form.cta.title" label="Заголовок" required />
          </div>
          <BaseInput v-model="form.cta.subtitle" as="textarea" :rows="2" label="Текст" />
          <BaseInput v-model="form.cta.button_label" label="Текст кнопки" required class="sm:w-64" />
        </div>
      </BaseCard>

      <BaseCard>
        <StepTitle n="7" title="Подвал (footer)" />
        <div class="space-y-4">
          <BaseInput v-model="form.footer.tagline" as="textarea" :rows="2" label="Описание под названием бренда" />
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseInput v-model="form.footer.address" as="textarea" :rows="3" label="Адрес" hint="Каждая строка — перенос строки" />
            <BaseInput v-model="form.footer.hours" as="textarea" :rows="3" label="Часы работы" hint="Каждая строка — перенос строки" />
          </div>
          <div>
            <p class="mb-2 text-sm font-medium text-ink-900">Ссылки «Мы в сети»</p>
            <div v-for="(link, i) in form.footer.social_links" :key="i" class="mb-2 grid gap-3 sm:grid-cols-2">
              <BaseInput v-model="link.label" :label="`Ссылка ${i + 1} — текст`" required />
              <BaseInput v-model="link.url" :label="`Ссылка ${i + 1} — URL`" required />
            </div>
          </div>
          <BaseInput v-model="form.footer.bottom_note" label="Нижняя строка справа" />
        </div>
      </BaseCard>

      <BaseCard v-if="form.theme">
        <StepTitle n="8" title="Тема оформления" />
        <div class="space-y-5">
          <div>
            <p class="mb-2 text-sm font-medium text-ink-900">Готовые палитры</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="(preset, name) in themePresets" :key="name" type="button"
                class="flex items-center gap-2 border px-3 py-2 font-mono text-xs uppercase tracking-wide transition-colors"
                :class="form.theme.preset === name
                  ? 'border-brand-900 bg-brand-900 text-stone-50'
                  : 'border-stone-200 text-ink-600 hover:border-brand-900'"
                @click="selectThemePreset(name)"
              >
                <span class="flex -space-x-1">
                  <span class="h-4 w-4 rounded-full border border-white/40" :style="{ background: preset.colors.brand_900 }" />
                  <span class="h-4 w-4 rounded-full border border-white/40" :style="{ background: preset.colors.accent_400 }" />
                  <span class="h-4 w-4 rounded-full border border-white/40" :style="{ background: preset.colors.stone_50 }" />
                </span>
                {{ preset.label }}
              </button>
              <span
                class="flex items-center border px-3 py-2 font-mono text-xs uppercase tracking-wide"
                :class="form.theme.preset === 'custom' ? 'border-brand-900 bg-brand-900 text-stone-50' : 'border-stone-200 text-ink-600'"
              >
                Свой вариант
              </span>
            </div>
          </div>

          <div>
            <p class="mb-2 text-sm font-medium text-ink-900">Шрифты</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="(preset, name) in fontPresets" :key="name" type="button"
                class="border px-3 py-2 text-left transition-colors"
                :class="form.theme.font === name
                  ? 'border-brand-900 bg-brand-900 text-stone-50'
                  : 'border-stone-200 text-ink-600 hover:border-brand-900'"
                @click="form.theme.font = name"
              >
                <span class="block text-base" :style="{ fontFamily: preset.display }">{{ preset.label.split(' + ')[0] }}</span>
                <span class="mt-0.5 block font-mono text-[10px] uppercase tracking-wide opacity-70" :style="{ fontFamily: preset.mono }">
                  {{ preset.label.split(' + ')[1] }}
                </span>
              </button>
            </div>
          </div>

          <div>
            <p class="mb-2 text-sm font-medium text-ink-900">Цвета вручную</p>
            <div class="grid gap-3 sm:grid-cols-2">
              <label v-for="t in themeTokens" :key="t.key" class="flex items-center gap-3 border border-stone-200 px-3 py-2">
                <input
                  type="color" :value="form.theme.colors[t.key]"
                  class="h-8 w-8 shrink-0 cursor-pointer border-0 bg-transparent p-0"
                  @input="setThemeColor(t.key, $event.target.value)"
                />
                <span class="text-sm text-ink-600">{{ t.label }}</span>
              </label>
            </div>
          </div>
        </div>
      </BaseCard>

        <div class="flex justify-end">
          <BaseButton type="submit" :loading="saving">Сохранить все изменения</BaseButton>
        </div>
      </form>

      <div class="hidden lg:sticky lg:top-6 lg:block">
        <p class="mb-2 font-mono text-xs uppercase tracking-widest text-ink-600">Предпросмотр главной страницы</p>
        <div class="max-h-[calc(100vh-8rem)] overflow-y-auto overflow-x-hidden rounded-lg border border-stone-200 bg-white">
          <div style="width: 1280px; zoom: 0.5;">
            <HomePreview :content="form" :interactive="false" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { settingsApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { useSiteContentStore } from '../../stores/siteContent'
import { extractErrorMessage } from '../../utils/errors'
import { applyTheme, THEME_PRESETS, THEME_TOKENS } from '../../theme/presets'
import { applyFont, FONT_PRESETS } from '../../theme/fonts'
import BaseCard from '../../components/ui/BaseCard.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import StepTitle from '../../components/ui/StepTitle.vue'
import HomePreview from '../../components/HomePreview.vue'

const toast = useToastStore()
const siteContentStore = useSiteContentStore()

const loading = ref(true)
const saving = ref(false)
const form = reactive({})

const heroVariants = [
  { value: 'split', label: 'A — Разделённый' },
  { value: 'poster', label: 'B — Постер' },
  { value: 'dark', label: 'C — Тёмный' },
]
const themePresets = THEME_PRESETS
const themeTokens = THEME_TOKENS
const fontPresets = FONT_PRESETS

onMounted(async () => {
  try {
    const { data } = await settingsApi.get()
    Object.assign(form, data)
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить настройки сайта'))
  } finally {
    loading.value = false
  }
  // Живое превью темы по всему сайту (включая саму админку), пока форма открыта;
  // при уходе со страницы без сохранения возвращаем сохранённую тему (см. ниже).
  watch(() => form.theme?.colors, (colors) => applyTheme(colors), { deep: true })
  watch(() => form.theme?.font, (font) => applyFont(font))
})

onBeforeUnmount(() => {
  applyTheme(siteContentStore.content.theme?.colors)
  applyFont(siteContentStore.content.theme?.font)
})

function selectThemePreset(name) {
  form.theme.preset = name
  form.theme.colors = { ...THEME_PRESETS[name].colors }
}

function setThemeColor(key, value) {
  form.theme.preset = 'custom'
  form.theme.colors[key] = value
}

async function save() {
  saving.value = true
  try {
    const { data } = await settingsApi.update(form)
    Object.assign(form, data)
    siteContentStore.set(data)
    toast.success('Настройки сайта сохранены')
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось сохранить настройки'))
  } finally {
    saving.value = false
  }
}
</script>
