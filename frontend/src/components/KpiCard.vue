<template>
  <BaseCard class="flex items-center gap-4">
    <div class="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg bg-accent-100 text-brand-900">
      <component :is="icon" class="h-6 w-6" aria-hidden="true" />
    </div>
    <div>
      <p class="font-mono text-[11px] uppercase tracking-wide text-ink-600">{{ label }}</p>
      <p class="font-display text-2xl font-bold text-ink-900">{{ value }}</p>
    </div>
  </BaseCard>
</template>

<script setup>
import BaseCard from './ui/BaseCard.vue'

defineProps({
  label: String,
  value: [String, Number],
  icon: [Object, Function],
})
</script>
