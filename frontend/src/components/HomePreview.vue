<template>
  <div :class="{ 'pointer-events-none': !interactive }">
    <!-- Hero A — split (editorial) -->
    <section v-if="heroVariant === 'split'" class="bg-stone-50">
      <div class="mx-auto grid max-w-6xl sm:grid-cols-2">
        <div class="flex flex-col justify-center gap-6 px-4 py-16 sm:px-6 sm:py-24">
          <EditableText v-model="content.hero.eyebrow" :editable="editable" class="font-mono text-xs uppercase tracking-[0.16em] text-ink-600" />
          <EditableText
            v-model="content.hero.title" :editable="editable" multiline tag="h1"
            class="whitespace-pre-line font-display text-5xl font-black uppercase leading-[0.95] tracking-tight text-ink-900 sm:text-6xl lg:text-7xl"
          />
          <EditableText v-model="content.hero.subtitle" :editable="editable" multiline tag="p" class="max-w-md text-base leading-relaxed text-ink-600" />
          <div class="flex flex-wrap gap-3">
            <EditableLink :to="{ name: 'masters' }" :editable="editable">
              <BaseButton size="lg"><EditableText v-model="content.hero.primary_button" :editable="editable" /></BaseButton>
            </EditableLink>
            <EditableLink href="#services" :editable="editable">
              <BaseButton variant="ghost" size="lg"><EditableText v-model="content.hero.secondary_button" :editable="editable" /></BaseButton>
            </EditableLink>
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
        <div class="relative min-h-[280px] overflow-hidden sm:min-h-full" :class="panelBgClass('light')">
          <Hero3DRoom v-if="content.hero.media_type === '3d'" />
          <template v-else>
            <img v-if="content.hero.photo_url" :src="content.hero.photo_url" alt="" class="absolute inset-0 h-full w-full object-cover" />
            <span v-else class="absolute bottom-5 left-5 bg-stone-50 px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-wide text-ink-600">
              [ мастер за креслом ]
            </span>
          </template>
          <div v-if="editable" class="absolute right-3 top-3 flex gap-1">
            <button type="button" class="rounded px-2 py-1 font-mono text-[10px] uppercase tracking-wide shadow" :class="mediaTypeBtnClass('photo')" @click="content.hero.media_type = 'photo'">Фото</button>
            <button type="button" class="rounded px-2 py-1 font-mono text-[10px] uppercase tracking-wide shadow" :class="mediaTypeBtnClass('3d')" @click="content.hero.media_type = '3d'">3D</button>
          </div>
          <EditableText
            v-if="editable && content.hero.media_type !== '3d'" v-model="content.hero.photo_url" editable placeholder="URL фото"
            class="absolute inset-x-3 bottom-3 rounded bg-white/90 px-2.5 py-1.5 font-mono text-[11px] text-ink-900 shadow"
          />
        </div>
      </div>
    </section>

    <!-- Hero B — centered poster -->
    <section v-else-if="heroVariant === 'poster'" class="bg-stone-50">
      <div class="mx-auto flex max-w-5xl flex-col items-center px-4 py-16 text-center sm:px-6 sm:py-24">
        <EditableText v-model="content.hero.eyebrow" :editable="editable" class="font-mono text-xs uppercase tracking-[0.22em] text-ink-600" />
        <EditableText
          v-model="content.header.brand_name" :editable="editable"
          class="mt-8 w-full font-display font-black uppercase leading-[1.15] tracking-tight text-ink-900"
          style="font-size: clamp(2.75rem, 11vw, 7rem)"
        />
        <div class="relative mt-6 h-56 w-full overflow-hidden sm:h-72" :class="panelBgClass('light')">
          <Hero3DRoom v-if="content.hero.media_type === '3d'" />
          <template v-else>
            <img v-if="content.hero.photo_url" :src="content.hero.photo_url" alt="" class="absolute inset-0 h-full w-full object-cover" />
            <span v-else class="absolute bottom-4 left-4 bg-stone-50 px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-wide text-ink-600">
              [ интерьер барбершопа ]
            </span>
          </template>
          <div v-if="editable" class="absolute right-3 top-3 flex gap-1">
            <button type="button" class="rounded px-2 py-1 font-mono text-[10px] uppercase tracking-wide shadow" :class="mediaTypeBtnClass('photo')" @click="content.hero.media_type = 'photo'">Фото</button>
            <button type="button" class="rounded px-2 py-1 font-mono text-[10px] uppercase tracking-wide shadow" :class="mediaTypeBtnClass('3d')" @click="content.hero.media_type = '3d'">3D</button>
          </div>
          <EditableText
            v-if="editable && content.hero.media_type !== '3d'" v-model="content.hero.photo_url" editable placeholder="URL фото"
            class="absolute inset-x-3 bottom-3 rounded bg-white/90 px-2.5 py-1.5 font-mono text-[11px] text-ink-900 shadow"
          />
        </div>
        <div class="mt-8 flex w-full flex-col items-center justify-between gap-6 sm:flex-row sm:text-left">
          <EditableText v-model="content.hero.subtitle" :editable="editable" multiline tag="p" class="max-w-md text-base leading-relaxed text-ink-600" />
          <EditableLink :to="{ name: 'masters' }" :editable="editable">
            <BaseButton size="lg"><EditableText v-model="content.hero.primary_button" :editable="editable" /> ↗</BaseButton>
          </EditableLink>
        </div>
      </div>
    </section>

    <!-- Hero C — dark asymmetric, type-led -->
    <section v-else class="bg-ink-900">
      <div class="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:grid-cols-[1.4fr_1fr] sm:px-6 sm:py-24">
        <div class="flex flex-col justify-between gap-8">
          <EditableText v-model="content.hero.eyebrow" :editable="editable" class="font-mono text-xs uppercase tracking-[0.16em] text-white/55" />
          <EditableText
            v-model="content.hero.title" :editable="editable" multiline tag="h1"
            class="whitespace-pre-line font-display text-5xl font-black uppercase leading-[0.88] tracking-tight text-stone-50 sm:text-7xl"
          />
          <div class="flex flex-wrap items-center gap-5">
            <EditableLink :to="{ name: 'masters' }" :editable="editable">
              <BaseButton size="lg" class="!border-stone-50 !bg-stone-50 !text-ink-900 hover:!bg-white">
                <EditableText v-model="content.hero.primary_button" :editable="editable" /> ↗
              </BaseButton>
            </EditableLink>
            <EditableLink href="#services" :editable="editable" class="font-mono text-xs uppercase tracking-[0.06em] text-white/55 hover:text-white">
              <EditableText v-model="content.hero.secondary_button" :editable="editable" />
            </EditableLink>
          </div>
        </div>
        <div class="flex flex-col">
          <div class="relative min-h-[220px] flex-1 overflow-hidden" :class="panelBgClass('dark')">
            <Hero3DRoom v-if="content.hero.media_type === '3d'" />
            <template v-else>
              <img v-if="content.hero.photo_url" :src="content.hero.photo_url" alt="" class="absolute inset-0 h-full w-full object-cover" />
              <span v-else class="absolute bottom-4 left-4 bg-ink-900 px-2 py-1.5 font-mono text-[10px] uppercase tracking-wide text-white/45">
                [ портрет мастера ]
              </span>
            </template>
            <div v-if="editable" class="absolute right-3 top-3 flex gap-1">
              <button type="button" class="rounded px-2 py-1 font-mono text-[10px] uppercase tracking-wide shadow" :class="mediaTypeBtnClass('photo')" @click="content.hero.media_type = 'photo'">Фото</button>
              <button type="button" class="rounded px-2 py-1 font-mono text-[10px] uppercase tracking-wide shadow" :class="mediaTypeBtnClass('3d')" @click="content.hero.media_type = '3d'">3D</button>
            </div>
            <EditableText
              v-if="editable && content.hero.media_type !== '3d'" v-model="content.hero.photo_url" editable placeholder="URL фото"
              class="absolute inset-x-3 bottom-3 rounded bg-white/90 px-2.5 py-1.5 font-mono text-[11px] text-ink-900 shadow"
            />
          </div>
          <div class="mt-6 space-y-2 font-mono text-[11px] uppercase tracking-[0.06em] text-white/70">
            <div>{{ avgDurationLabel }} · средняя стрижка</div>
            <div>{{ mastersTotal }} мастеров на смене</div>
            <div>{{ servicesTotal }} услуг в каталоге</div>
          </div>
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
        <EditableText v-model="content.features.eyebrow" :editable="editable" class="font-mono text-xs uppercase tracking-[0.16em] text-ink-600" />
        <EditableText
          v-model="content.features.title" :editable="editable" tag="h2"
          class="mt-3 max-w-xl font-display text-4xl font-extrabold uppercase leading-tight tracking-tight text-ink-900 sm:text-5xl"
        />
        <div class="mt-12 grid gap-10 sm:grid-cols-3">
          <div v-for="(f, i) in content.features.items" :key="i" class="border-t border-ink-900 pt-5">
            <div class="font-mono text-xs text-ink-600">{{ String(i + 1).padStart(2, '0') }}</div>
            <EditableText v-model="f.title" :editable="editable" tag="h3" class="mt-4 font-display text-xl font-bold text-ink-900" />
            <EditableText v-model="f.text" :editable="editable" multiline tag="p" class="mt-2 text-sm leading-relaxed text-ink-600" />
          </div>
        </div>
      </div>
    </section>

    <!-- services & pricing -->
    <section id="services" class="bg-ink-900 px-4 py-20 sm:px-6">
      <div class="mx-auto max-w-6xl">
        <div class="mb-10 flex flex-wrap items-end justify-between gap-4">
          <div>
            <EditableText v-model="content.services.eyebrow" :editable="editable" class="font-mono text-xs uppercase tracking-[0.16em] text-white/50" />
            <EditableText
              v-model="content.services.title" :editable="editable" tag="h2"
              class="mt-3 font-display text-4xl font-extrabold uppercase leading-tight tracking-tight text-stone-50 sm:text-5xl"
            />
          </div>
          <EditableText v-model="content.services.note" :editable="editable" multiline class="whitespace-pre-line font-mono text-xs leading-relaxed text-white/50" />
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
        <EditableText v-model="content.masters.eyebrow" :editable="editable" class="font-mono text-xs uppercase tracking-[0.16em] text-ink-600" />
        <EditableText
          v-model="content.masters.title" :editable="editable" tag="h2"
          class="mt-3 font-display text-4xl font-extrabold uppercase leading-tight tracking-tight text-ink-900 sm:text-5xl"
        />

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
      <EditableText v-model="content.cta.eyebrow" :editable="editable" class="font-mono text-xs uppercase tracking-[0.2em] text-white/50" />
      <EditableText
        v-model="content.cta.title" :editable="editable" tag="h2"
        class="mx-auto mt-5 max-w-2xl font-display text-5xl font-black uppercase leading-[0.95] tracking-tight text-stone-50 sm:text-6xl"
      />
      <EditableText v-model="content.cta.subtitle" :editable="editable" multiline tag="p" class="mx-auto mt-5 max-w-md text-base text-white/60" />
      <EditableLink :to="{ name: 'masters' }" :editable="editable">
        <BaseButton size="lg" class="mt-8 !border-stone-50 !bg-stone-50 !text-ink-900 hover:!bg-white">
          <EditableText v-model="content.cta.button_label" :editable="editable" /> ↗
        </BaseButton>
      </EditableLink>
    </section>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import { mastersApi, servicesApi } from '../api'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'
import BaseButton from './ui/BaseButton.vue'
import Skeleton from './ui/Skeleton.vue'
import EmptyState from './ui/EmptyState.vue'
import EditableText from './ui/EditableText.vue'
import EditableLink from './ui/EditableLink.vue'
import MasterCard from './MasterCard.vue'

// three.js — тяжёлая зависимость, нужна только когда hero.media_type === '3d',
// поэтому грузим отдельным чанком, а не в общий бандл главной страницы.
const Hero3DRoom = defineAsyncComponent(() => import('./Hero3DRoom.vue'))

const props = defineProps({
  content: { type: Object, required: true },
  interactive: { type: Boolean, default: true },
  editable: { type: Boolean, default: false },
})

const toast = useToastStore()

const services = ref([])
const servicesLoading = ref(true)
const servicesTotal = ref('—')
const masters = ref([])
const mastersLoading = ref(true)
const mastersTotal = ref('—')

const heroVariant = computed(() => props.content.hero?.variant || 'split')

function mediaTypeBtnClass(type) {
  return (props.content.hero.media_type || 'photo') === type
    ? 'bg-brand-900 text-stone-50'
    : 'bg-white/90 text-ink-600 hover:bg-white'
}

// В режиме 3D панель не должна показывать штриховку "нет фото" — canvas
// прозрачный (alpha: true), и полосы просвечивали бы сквозь и вокруг модели.
function panelBgClass(scheme) {
  if (props.content.hero.media_type === '3d') {
    return scheme === 'dark' ? 'bg-ink-900' : 'bg-stone-100'
  }
  return scheme === 'dark'
    ? 'bg-[repeating-linear-gradient(135deg,#262626_0_14px,#1c1c1c_14px_28px)]'
    : 'bg-[repeating-linear-gradient(135deg,#e4e2dd_0_14px,#dbd8d2_14px_28px)]'
}

const marqueeText = computed(() =>
  services.value.length
    ? services.value.map((s) => s.name.toUpperCase()).join(' — ') + ' —'
    : 'СТРИЖКА — ФЕЙД — ОФОРМЛЕНИЕ БОРОДЫ — ГОРЯЧЕЕ БРИТЬЕ —'
)

const avgDurationLabel = computed(() => {
  if (!services.value.length) return '—'
  const avg = services.value.reduce((sum, s) => sum + s.duration_min, 0) / services.value.length
  // Округляем до 10 минут — это витринная цифра в hero-блоке, точность до
  // минуты (например "32 мин") выглядит случайной, а не как аккуратная
  // маркетинговая метрика (ISSUES #6).
  return `${Math.round(avg / 10) * 10} мин`
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
