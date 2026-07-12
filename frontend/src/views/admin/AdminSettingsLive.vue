<template>
  <div class="-m-4 sm:-m-6">
    <Skeleton v-if="loading" height="h-96" class="m-6" />

    <template v-else>
      <AppHeader :content="form" editable />
      <HomePreview :content="form" editable interactive />
      <AppFooter :content="form" editable />
    </template>

    <!-- floating editor toolbar -->
    <div v-if="!loading" class="sticky bottom-0 z-40 border-t border-stone-200 bg-white/95 backdrop-blur">
      <div class="relative mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
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
import AppHeader from '../../components/AppHeader.vue'
import AppFooter from '../../components/AppFooter.vue'
import HomePreview from '../../components/HomePreview.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import Skeleton from '../../components/ui/Skeleton.vue'

const toast = useToastStore()
const siteContentStore = useSiteContentStore()

const loading = ref(true)
const saving = ref(false)
const showColors = ref(false)
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
