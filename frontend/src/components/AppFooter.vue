<template>
  <footer class="bg-[#0c0c0c] px-4 py-16 sm:px-6">
    <div class="mx-auto max-w-6xl">
      <div class="grid gap-10 border-b border-white/15 pb-12 sm:grid-cols-[1.6fr_2fr_1fr]">
        <div>
          <div class="flex items-baseline gap-2.5">
            <span class="font-display text-2xl font-black uppercase tracking-tight text-stone-50">{{ content.header.brand_name }}</span>
            <span class="font-mono text-[10px] uppercase tracking-[0.2em] text-white/60">{{ content.header.brand_tagline }}</span>
          </div>
          <EditableText
            v-model="content.footer.tagline" :editable="editable" multiline
            class="mt-4 max-w-xs whitespace-pre-line text-sm leading-relaxed text-white/50"
          />
        </div>
        <!-- Адреса и часы берутся из точек сети, а не из контента сайта: при
             двух и более салонах один общий адрес в подвале некорректен по
             определению (ROADMAP.md §4.4). Правятся в «Админ → Точки сети»,
             поэтому здесь нет EditableText даже в режиме редактора. -->
        <div>
          <div class="mb-4 font-mono text-[11px] uppercase tracking-wide text-white/60">
            {{ salons.length > 1 ? 'Наши салоны' : 'Адрес' }}
          </div>
          <ul v-if="salons.length" class="space-y-3">
            <li v-for="salon in salons" :key="salon.id" class="text-sm leading-relaxed text-white/70">
              <span v-if="salons.length > 1" class="block text-white/90">{{ salon.name }}</span>
              <span class="block whitespace-pre-line">{{ salon.address }}</span>
              <span class="block font-mono text-[11px] uppercase tracking-wide text-white/60">
                Ежедневно {{ salon.open_time.slice(0, 5) }}–{{ salon.close_time.slice(0, 5) }}<template v-if="salon.phone"> · {{ salon.phone }}</template>
              </span>
            </li>
          </ul>
          <p v-else class="text-sm text-white/50">Точки скоро появятся</p>
        </div>
        <div>
          <div class="mb-4 font-mono text-[11px] uppercase tracking-wide text-white/60">Мы в сети</div>
          <div class="flex flex-col gap-2.5">
            <template v-if="editable">
              <div v-for="(link, i) in content.footer.social_links" :key="i" class="flex items-center gap-2">
                <EditableText
                  v-model="link.label" editable
                  class="font-mono text-xs uppercase tracking-wide text-white/70 hover:text-white"
                />
                <EditableText
                  v-model="link.url" editable
                  class="font-mono text-[11px] text-white/60" placeholder="URL"
                />
              </div>
            </template>
            <a v-else v-for="link in content.footer.social_links" :key="link.label" :href="link.url" class="font-mono text-xs uppercase tracking-wide text-white/70 hover:text-white">{{ link.label }}</a>
          </div>
        </div>
      </div>
      <div class="flex flex-wrap items-center justify-between gap-2 pt-6 font-mono text-[11px] uppercase tracking-wide text-white/60">
        <span class="flex flex-wrap items-center gap-x-4 gap-y-1">
          <span>© {{ year }} {{ content.header.brand_tagline }} «{{ content.header.brand_name }}»</span>
          <router-link :to="{ name: 'privacy-policy' }" class="hover:text-white">Обработка персональных данных</router-link>
        </span>
        <EditableText v-model="content.footer.bottom_note" :editable="editable" />
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useSiteContentStore } from '../stores/siteContent'
import { useSalonStore } from '../stores/salon'
import EditableText from './ui/EditableText.vue'

const props = defineProps({
  content: { type: Object, default: null },
  editable: { type: Boolean, default: false },
})

const { content: storeContent } = storeToRefs(useSiteContentStore())
const content = computed(() => props.content ?? storeContent.value)
const salonStore = useSalonStore()
// Закрытые точки в подвале публичного сайта не показываем (в сторе может
// лежать расширенный список — см. stores/salon.js).
const salons = computed(() => salonStore.activeSalons)
const year = new Date().getFullYear()
</script>
