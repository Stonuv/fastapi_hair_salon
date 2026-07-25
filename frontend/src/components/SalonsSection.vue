<template>
  <!-- Точки сети. В отличие от остальных секций главной, содержимое НЕ
       редактируется инлайн: салоны живут в своей таблице и правятся в
       «Админ → Точки сети», а не в контенте сайта — поэтому здесь нет
       EditableText даже в режиме редактора. -->
  <section v-if="salons.length" class="bg-white px-4 py-20 sm:px-6">
    <div class="mx-auto max-w-6xl">
      <p class="font-mono text-xs uppercase tracking-[0.16em] text-ink-600">
        {{ salons.length > 1 ? 'Наши салоны' : 'Где нас найти' }}
      </p>
      <h2 class="mt-3 font-display text-4xl font-extrabold uppercase leading-tight tracking-tight text-ink-900 sm:text-5xl">
        {{ salons.length > 1 ? `${salons.length} точки в городе.` : 'Адрес и часы.' }}
      </h2>

      <div class="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <component
          :is="interactive ? RouterLink : 'div'"
          v-for="salon in salons"
          :key="salon.id"
          :to="interactive ? { name: 'masters', query: { salon_id: salon.id } } : undefined"
          class="group block overflow-hidden rounded-xl border border-stone-200 bg-stone-50 transition-colors duration-200"
          :class="interactive ? 'hover:border-brand-900' : ''"
        >
          <div v-if="salon.photo_url" class="aspect-[3/2] overflow-hidden">
            <img
              :src="salon.photo_url" :alt="salon.name"
              class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          </div>
          <div class="p-5">
            <p class="font-display text-xl font-bold uppercase tracking-tight text-ink-900">{{ salon.name }}</p>
            <p class="mt-2 whitespace-pre-line text-sm leading-relaxed text-ink-600">{{ salon.address }}</p>
            <p class="mt-2 font-mono text-xs uppercase tracking-wide text-ink-600">
              Ежедневно {{ salon.open_time.slice(0, 5) }}–{{ salon.close_time.slice(0, 5) }}
            </p>
            <p v-if="salon.phone" class="mt-1 font-mono text-xs uppercase tracking-wide text-ink-600">
              {{ salon.phone }}
            </p>
            <p v-if="interactive" class="mt-4 font-mono text-[11px] uppercase tracking-wide text-brand-700">
              Мастера точки ↗
            </p>
          </div>
        </component>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useSalonStore } from '../stores/salon'

// interactive=false — превью в редакторе главной: карточки не должны уводить
// со страницы редактирования (тот же приём, что у остальных секций).
defineProps({
  interactive: { type: Boolean, default: true },
})

const salonStore = useSalonStore()
// Закрытые точки на публичном сайте не показываем: в сторе может лежать
// расширенный список, если владелец до этого заходил в админку.
const salons = computed(() => salonStore.activeSalons)
</script>
