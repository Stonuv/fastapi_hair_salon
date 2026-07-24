<template>
  <div>
    <Skeleton v-if="loading" height="h-96" class="m-6" />

    <template v-else>
      <AppHeader :content="form" editable />
      <HomePreview :content="form" editable interactive />
      <AppFooter :content="form" editable />
    </template>

    <!-- floating editor toolbar -->
    <div v-if="!loading" class="sticky bottom-0 z-40 border-t border-stone-200 bg-white/95 backdrop-blur">
      <div class="relative mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
        <router-link
          :to="{ name: 'admin-stats' }"
          class="flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide text-ink-600 hover:text-brand-700"
        >
          <ArrowLeftIcon class="h-3.5 w-3.5" aria-hidden="true" /> Админка
        </router-link>

        <div class="h-6 w-px bg-stone-200" />

        <div class="flex flex-wrap items-center gap-1.5">
          <button
            v-for="v in heroVariants" :key="v.value" type="button"
            class="border px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wide transition-colors"
            :class="form.hero?.variant === v.value ? 'border-brand-900 bg-brand-900 text-stone-50' : 'border-stone-200 text-ink-600 hover:border-brand-900'"
            @click="form.hero.variant = v.value"
          >{{ v.label }}</button>
        </div>

        <div class="h-6 w-px bg-stone-200" />

        <div class="flex flex-wrap items-center gap-1.5">
          <button
            v-for="(preset, name) in themePresets" :key="name" type="button"
            class="flex items-center gap-1.5 border px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wide transition-colors"
            :class="form.theme?.preset === name ? 'border-brand-900 bg-brand-900 text-stone-50' : 'border-stone-200 text-ink-600 hover:border-brand-900'"
            @click="selectThemePreset(name)"
          >
            <span class="flex -space-x-1">
              <span class="h-3 w-3 rounded-full border border-white/40" :style="{ background: preset.colors.brand_900 }" />
              <span class="h-3 w-3 rounded-full border border-white/40" :style="{ background: preset.colors.accent_400 }" />
            </span>
            {{ preset.label }}
          </button>
          <button
            type="button" class="border px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wide transition-colors"
            :class="showColors ? 'border-brand-900 bg-brand-900 text-stone-50' : 'border-stone-200 text-ink-600 hover:border-brand-900'"
            @click="showColors = !showColors"
          >Цвета вручную</button>
        </div>

        <div class="h-6 w-px bg-stone-200" />

        <div class="flex flex-wrap items-center gap-1.5">
          <button
            v-for="(preset, name) in fontPresets" :key="name" type="button"
            class="border px-2.5 py-1.5 text-left transition-colors"
            :class="form.theme?.font === name ? 'border-brand-900 bg-brand-900 text-stone-50' : 'border-stone-200 text-ink-600 hover:border-brand-900'"
            @click="form.theme.font = name"
          >
            <span class="block text-xs" :style="{ fontFamily: preset.display }">{{ preset.label.split(' + ')[0] }}</span>
          </button>
        </div>

        <button
          type="button" class="border border-stone-200 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wide text-ink-600 transition-colors hover:border-brand-900"
          @click="showMore = true"
        >Ещё настройки</button>

        <div class="ml-auto flex items-center gap-3">
          <span v-if="saving" class="font-mono text-[10px] uppercase tracking-wide text-ink-600">Сохранение…</span>
          <BaseButton size="sm" :loading="saving" @click="save">Сохранить</BaseButton>
        </div>

        <div v-if="showColors" class="absolute bottom-full left-4 right-4 mb-2 grid gap-2 border border-stone-200 bg-white p-4 shadow-lg sm:left-6 sm:right-auto sm:grid-cols-2">
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

    <Teleport to="body">
      <div v-if="showMore" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" @click="showMore = false" />
        <div class="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-stone-200 bg-white p-6 shadow-lg" role="dialog" aria-modal="true">
          <h2 class="font-display text-lg font-bold uppercase tracking-tight text-ink-900">Ещё настройки</h2>

          <div v-if="form.business_hours" class="mt-5">
            <p class="mb-1.5 text-sm font-medium text-ink-900">Время работы салона</p>
            <p class="mb-2 text-sm text-ink-600">
              Жёсткая граница для расписаний мастеров и записей клиентов — ни одно расписание и ни одна запись
              не могут выходить за эти рамки, даже если мастер укажет для себя более широкие часы.
            </p>
            <div class="flex items-center gap-3">
              <BaseTimeInput v-model="form.business_hours.open_time" />
              <span class="text-ink-600">—</span>
              <BaseTimeInput v-model="form.business_hours.close_time" />
            </div>
          </div>

          <div v-if="form.seo" class="mt-6 space-y-4 border-t border-stone-200 pt-5">
            <p class="text-sm font-medium text-ink-900">SEO</p>
            <p class="text-sm text-ink-600">
              Заголовок вкладки браузера, описание в поисковой выдаче и иконка сайта (favicon) — служебные
              метаданные для браузера/поисковика/соцсетей, на самом сайте не отображаются.
            </p>
            <BaseInput v-model="form.seo.title" label="Заголовок вкладки (&lt;title&gt;)" required />
            <BaseInput v-model="form.seo.description" as="textarea" :rows="2" label="Описание для поисковиков" />
            <div>
              <p class="mb-1.5 block text-sm font-medium text-ink-900">Иконка сайта (favicon)</p>
              <ImageUpload v-model="form.seo.favicon_url" />
              <p class="mt-1 text-sm text-ink-600/80">Если не загружена — используется стандартная иконка сайта</p>
            </div>
          </div>

          <div class="mt-6 flex justify-end">
            <BaseButton size="sm" @click="showMore = false">Готово</BaseButton>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ArrowLeftIcon } from '@heroicons/vue/24/outline'
import { settingsApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { useSiteContentStore } from '../../stores/siteContent'
import { extractErrorMessage } from '../../utils/errors'
import { applyTheme, THEME_PRESETS, THEME_TOKENS } from '../../theme/presets'
import { applyFont, FONT_PRESETS } from '../../theme/fonts'
import { applySeo } from '../../theme/seo'
import AppHeader from '../../components/AppHeader.vue'
import AppFooter from '../../components/AppFooter.vue'
import HomePreview from '../../components/HomePreview.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseTimeInput from '../../components/ui/BaseTimeInput.vue'
import ImageUpload from '../../components/ui/ImageUpload.vue'
import Skeleton from '../../components/ui/Skeleton.vue'

const toast = useToastStore()
const siteContentStore = useSiteContentStore()

const loading = ref(true)
const saving = ref(false)
const showColors = ref(false)
const showMore = ref(false)
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
  watch(() => form.theme?.colors, (colors) => applyTheme(colors), { deep: true })
  watch(() => form.theme?.font, (font) => applyFont(font))
  watch(() => form.seo, (seo) => applySeo(seo), { deep: true })
})

onBeforeUnmount(() => {
  applyTheme(siteContentStore.content.theme?.colors)
  applyFont(siteContentStore.content.theme?.font)
  applySeo(siteContentStore.content.seo)
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
