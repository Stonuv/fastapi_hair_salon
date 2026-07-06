<template>
  <div :class="{ 'pointer-events-none': !interactive }">
    <!-- Hero -->
    <section class="bg-stone-50">
      <div class="mx-auto grid max-w-6xl sm:grid-cols-2">
        <div class="flex flex-col justify-center gap-6 px-4 py-16 sm:px-6 sm:py-24">
          <div class="font-mono text-xs uppercase tracking-[0.16em] text-ink-600">{{ content.hero.eyebrow }}</div>
          <h1 class="whitespace-pre-line font-display text-5xl font-black uppercase leading-[0.95] tracking-tight text-ink-900 sm:text-6xl lg:text-7xl">
            {{ content.hero.title }}
          </h1>
          <p class="max-w-md text-base leading-relaxed text-ink-600">
            {{ content.hero.subtitle }}
          </p>
          <div class="flex flex-wrap gap-3">
            <router-link :to="{ name: 'masters' }"><BaseButton size="lg">{{ content.hero.primary_button }}</BaseButton></router-link>
            <a href="#services"><BaseButton variant="ghost" size="lg">{{ content.hero.secondary_button }}</BaseButton></a>
          </div>
          <div class="flex flex-wrap gap-8 border-t border-stone-200 pt-6">
            <div>
              <div class="font-display text-2xl font-extrabold text-ink-900">{{ avgDurationLabel }}</div>
              <div class="mt-1 font-mono text-[10px] uppercase tracking-wide text-ink-600">Средняя стрижка</div>
            </div>
            <div>
              <div class="font-display text-2xl font-extrabold text-ink-900">{{ servicesTotal }}</div>
              <div class="mt-1 font-mono text-[10px] uppercase tracking-wide text-ink-600">Услуг в каталоге</div>
            </div>
            <div>
              <div class="font-display text-2xl font-extrabold text-ink-900">{{ mastersTotal }}</div>
              <div class="mt-1 font-mono text-[10px] uppercase tracking-wide text-ink-600">Мастеров на смене</div>
            </div>
          </div>
        </div>
        <div class="relative min-h-[280px] overflow-hidden bg-[repeating-linear-gradient(135deg,#e4e2dd_0_14px,#dbd8d2_14px_28px)] sm:min-h-full">
          <img v-if="content.hero.photo_url" :src="content.hero.photo_url" alt="" class="absolute inset-0 h-full w-full object-cover" />
          <span v-else class="absolute bottom-5 left-5 bg-stone-50 px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-wide text-ink-600">
            [ мастер за креслом ]
          </span>
        </div>
      </div>
    </section>

    <!-- marquee -->
    <div class="flex h-12 items-center overflow-hidden bg-ink-900">
      <div class="flex animate-[sai-scroll_28s_linear_infinite] whitespace-nowrap font-mono text-sm uppercase tracking-[0.16em] text-stone-50">
        <span>{{ marqueeText }}&nbsp;</span>
        <span>{{ marqueeText }}&nbsp;</span>
      </div>
    </div>

    <!-- features -->
    <section class="bg-stone-50 px-4 py-20 sm:px-6">
      <div class="mx-auto max-w-6xl">
        <div class="font-mono text-xs uppercase tracking-[0.16em] text-ink-600">{{ content.features.eyebrow }}</div>
        <h2 class="mt-3 max-w-xl font-display text-4xl font-extrabold uppercase leading-tight tracking-tight text-ink-900 sm:text-5xl">
          {{ content.features.title }}
        </h2>
        <div class="mt-12 grid gap-10 sm:grid-cols-3">
          <div v-for="(f, i) in content.features.items" :key="f.title" class="border-t border-ink-900 pt-5">
            <div class="font-mono text-xs text-ink-600">{{ String(i + 1).padStart(2, '0') }}</div>
            <h3 class="mt-4 font-display text-xl font-bold text-ink-900">{{ f.title }}</h3>
            <p class="mt-2 text-sm leading-relaxed text-ink-600">{{ f.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- services & pricing -->
    <section id="services" class="bg-ink-900 px-4 py-20 sm:px-6">
      <div class="mx-auto max-w-6xl">
        <div class="mb-10 flex flex-wrap items-end justify-between gap-4">
          <div>
            <div class="font-mono text-xs uppercase tracking-[0.16em] text-white/50">{{ content.services.eyebrow }}</div>
            <h2 class="mt-3 font-display text-4xl font-extrabold uppercase leading-tight tracking-tight text-stone-50 sm:text-5xl">{{ content.services.title }}</h2>
          </div>
          <div class="whitespace-pre-line font-mono text-xs leading-relaxed text-white/50">{{ content.services.note }}</div>
        </div>

        <div v-if="servicesLoading" class="grid gap-x-16 sm:grid-cols-2">
          <Skeleton v-for="i in 6" :key="i" height="h-16" class="bg-white/10" />
        </div>
        <EmptyState v-else-if="services.length === 0" title="Пока нет доступных услуг" />
        <div v-else class="grid gap-x-16 sm:grid-cols-2">
          <div v-for="s in services" :key="s.id" class="flex items-baseline justify-between gap-4 border-t border-white/15 py-5">
            <div>
              <div class="font-display text-xl font-semibold text-stone-50">{{ s.name }}</div>
              <div class="mt-1 font-mono text-[11px] uppercase tracking-wide text-white/45">{{ s.duration_min }} мин</div>
            </div>
            <div class="font-mono text-lg font-bold text-stone-50">{{ s.price }} ₽</div>
          </div>
        </div>
      </div>
    </section>

    <!-- masters -->
    <section class="bg-stone-50 px-4 py-20 sm:px-6">
      <div class="mx-auto max-w-6xl">
        <div class="font-mono text-xs uppercase tracking-[0.16em] text-ink-600">{{ content.masters.eyebrow }}</div>
        <h2 class="mt-3 font-display text-4xl font-extrabold uppercase leading-tight tracking-tight text-ink-900 sm:text-5xl">
          {{ content.masters.title }}
        </h2>

        <div v-if="mastersLoading" class="mt-12 grid grid-cols-2 gap-6 sm:grid-cols-4">
          <Skeleton v-for="i in 4" :key="i" height="h-72" />
        </div>
        <EmptyState v-else-if="masters.length === 0" title="Мастера скоро появятся" class="mt-12" />
        <div v-else class="mt-12 grid grid-cols-2 gap-6 sm:grid-cols-4">
          <MasterCard v-for="m in masters" :key="m.id" :master="m" />
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="bg-ink-900 px-4 py-24 text-center sm:px-6">
      <div class="font-mono text-xs uppercase tracking-[0.2em] text-white/50">{{ content.cta.eyebrow }}</div>
      <h2 class="mx-auto mt-5 max-w-2xl font-display text-5xl font-black uppercase leading-[0.95] tracking-tight text-stone-50 sm:text-6xl">
        {{ content.cta.title }}
      </h2>
      <p class="mx-auto mt-5 max-w-md text-base text-white/60">
        {{ content.cta.subtitle }}
      </p>
      <router-link :to="{ name: 'masters' }">
        <BaseButton size="lg" class="mt-8 !border-stone-50 !bg-stone-50 !text-ink-900 hover:!bg-white">{{ content.cta.button_label }} ↗</BaseButton>
      </router-link>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { mastersApi, servicesApi } from '../api'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'
import BaseButton from './ui/BaseButton.vue'
import Skeleton from './ui/Skeleton.vue'
import EmptyState from './ui/EmptyState.vue'
import MasterCard from './MasterCard.vue'

defineProps({
  content: { type: Object, required: true },
  interactive: { type: Boolean, default: true },
})

const toast = useToastStore()

const services = ref([])
const servicesLoading = ref(true)
const servicesTotal = ref('—')
const masters = ref([])
const mastersLoading = ref(true)
const mastersTotal = ref('—')

const marqueeText = computed(() =>
  services.value.length
    ? services.value.map((s) => s.name.toUpperCase()).join(' — ') + ' —'
    : 'СТРИЖКА — ФЕЙД — ОФОРМЛЕНИЕ БОРОДЫ — ГОРЯЧЕЕ БРИТЬЕ —'
)

const avgDurationLabel = computed(() => {
  if (!services.value.length) return '—'
  const avg = services.value.reduce((sum, s) => sum + s.duration_min, 0) / services.value.length
  return `${Math.round(avg)} мин`
})

async function loadServices() {
  servicesLoading.value = true
  try {
    const { data } = await servicesApi.list({ page: 1, page_size: 8, is_active: true })
    services.value = data.items
    servicesTotal.value = data.total
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить услуги'))
  } finally {
    servicesLoading.value = false
  }
}

async function loadMasters() {
  mastersLoading.value = true
  try {
    const { data } = await mastersApi.list({ page: 1, page_size: 4 })
    masters.value = data.items
    mastersTotal.value = data.total
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить мастеров'))
  } finally {
    mastersLoading.value = false
  }
}

onMounted(() => {
  loadServices()
  loadMasters()
})
</script>
