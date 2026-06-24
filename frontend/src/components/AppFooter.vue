<template>
  <footer class="bg-[#0c0c0c] px-4 py-16 sm:px-6">
    <div class="mx-auto max-w-6xl">
      <div class="grid gap-10 border-b border-white/15 pb-12 sm:grid-cols-[1.6fr_1fr_1fr_1fr]">
        <div>
          <div class="flex items-baseline gap-2.5">
            <span class="font-display text-2xl font-black uppercase tracking-tight text-stone-50">{{ content.header.brand_name }}</span>
            <span class="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">{{ content.header.brand_tagline }}</span>
          </div>
          <p class="mt-4 max-w-xs whitespace-pre-line text-sm leading-relaxed text-white/50">{{ content.footer.tagline }}</p>
        </div>
        <div>
          <div class="mb-4 font-mono text-[11px] uppercase tracking-wide text-white/40">Адрес</div>
          <div class="whitespace-pre-line text-sm leading-relaxed text-white/70">{{ content.footer.address }}</div>
        </div>
        <div>
          <div class="mb-4 font-mono text-[11px] uppercase tracking-wide text-white/40">Часы работы</div>
          <div class="whitespace-pre-line text-sm leading-relaxed text-white/70">{{ content.footer.hours }}</div>
        </div>
        <div>
          <div class="mb-4 font-mono text-[11px] uppercase tracking-wide text-white/40">Мы в сети</div>
          <div class="flex flex-col gap-2.5">
            <a v-for="link in content.footer.social_links" :key="link.label" :href="link.url" class="font-mono text-xs uppercase tracking-wide text-white/70 hover:text-white">{{ link.label }}</a>
          </div>
        </div>
      </div>
      <div class="flex flex-wrap items-center justify-between gap-2 pt-6 font-mono text-[11px] uppercase tracking-wide text-white/40">
        <span>© {{ year }} {{ content.header.brand_tagline }} «{{ content.header.brand_name }}»</span>
        <span>{{ content.footer.bottom_note }}</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useSiteContentStore } from '../stores/siteContent'

const { content } = storeToRefs(useSiteContentStore())
const year = new Date().getFullYear()
</script>
