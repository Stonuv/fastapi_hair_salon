<template>
  <router-link :to="`/masters/${master.id}`" class="group block cursor-pointer overflow-hidden border border-stone-200 bg-white transition-colors duration-200 hover:border-brand-900">
    <div class="aspect-[3/4] w-full overflow-hidden bg-stone-200">
      <img v-if="master.photo_url" :src="master.photo_url" :alt="fullName" class="h-full w-full object-cover" loading="lazy" />
      <div v-else class="flex h-full w-full items-center justify-center">
        <UserIcon class="h-16 w-16 text-brand-900/20" aria-hidden="true" />
      </div>
    </div>
    <div class="p-4">
      <p class="font-mono text-[11px] font-medium uppercase tracking-wide text-brand-700">{{ master.specialization || 'Барбер' }}</p>
      <h3 class="mt-1 font-display text-lg font-bold uppercase tracking-tight text-ink-900">{{ fullName }}</h3>
      <p class="mt-3 flex items-center gap-1 font-mono text-xs uppercase tracking-wide text-ink-900 transition-colors group-hover:text-brand-700">
        Записаться
        <ArrowRightIcon class="h-4 w-4" aria-hidden="true" />
      </p>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import { UserIcon, ArrowRightIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  master: { type: Object, required: true },
})

const fullName = computed(() => `${props.master.first_name} ${props.master.last_name}`)
</script>
