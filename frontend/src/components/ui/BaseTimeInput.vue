<template>
  <div class="flex items-center gap-1">
    <div class="relative">
      <select
        :value="hour"
        class="w-[4.25rem] cursor-pointer appearance-none rounded-lg border border-stone-200 bg-white py-2.5 pl-3 pr-6 text-center text-base transition-colors duration-200 focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
        aria-label="Часы"
        @change="onHourChange"
      >
        <option v-for="h in 24" :key="h" :value="pad(h - 1)">{{ pad(h - 1) }}</option>
      </select>
      <ChevronDownIcon class="pointer-events-none absolute right-1.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-600" aria-hidden="true" />
    </div>
    <span class="text-ink-600">:</span>
    <div class="relative">
      <select
        :value="minute"
        class="w-[4.25rem] cursor-pointer appearance-none rounded-lg border border-stone-200 bg-white py-2.5 pl-3 pr-6 text-center text-base transition-colors duration-200 focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
        aria-label="Минуты"
        @change="onMinuteChange"
      >
        <option v-for="m in 60" :key="m" :value="pad(m - 1)">{{ pad(m - 1) }}</option>
      </select>
      <ChevronDownIcon class="pointer-events-none absolute right-1.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-600" aria-hidden="true" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

// Замена нативного <input type="time"> — тот всегда следует локали
// браузера/ОС (даже с lang="ru" на элементе, см. BaseInput), а не языку
// страницы, и может показывать AM/PM (ISSUES #35). Два select гарантируют
// 24-часовой формат независимо от локали пользователя.
const props = defineProps({
  modelValue: { type: String, default: '00:00' }, // "HH:MM"
})
const emit = defineEmits(['update:modelValue'])

function pad(n) {
  return String(n).padStart(2, '0')
}

const parts = computed(() => (props.modelValue || '00:00').split(':'))
const hour = computed(() => parts.value[0] ?? '00')
const minute = computed(() => parts.value[1] ?? '00')

function onHourChange(event) {
  emit('update:modelValue', `${event.target.value}:${minute.value}`)
}
function onMinuteChange(event) {
  emit('update:modelValue', `${hour.value}:${event.target.value}`)
}
</script>
