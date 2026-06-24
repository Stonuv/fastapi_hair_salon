<template>
  <span class="inline-flex items-center rounded-full px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-wide" :class="entry.classes">
    {{ entry.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: { type: String, required: true } })

const map = {
  pending: { label: 'Ожидает подтверждения', classes: 'bg-amber-100 text-amber-800' },
  confirmed: { label: 'Подтверждена', classes: 'bg-sky-100 text-sky-800' },
  done: { label: 'Завершена', classes: 'bg-green-100 text-green-800' },
  cancelled: { label: 'Отменена', classes: 'bg-red-100 text-red-800' },
}

const entry = computed(() => map[props.status] ?? { label: props.status, classes: 'bg-stone-200 text-ink-600' })
</script>
