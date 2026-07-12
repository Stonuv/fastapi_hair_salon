<template>
  <div class="flex gap-1.5">
    <div class="relative flex-[0_0_4rem]">
      <select
        :value="day ?? ''"
        class="w-full cursor-pointer appearance-none rounded-lg border border-stone-200 bg-white py-2.5 pl-2.5 pr-6 text-base transition-colors duration-200 focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
        aria-label="День"
        @change="onDayChange"
      >
        <option value="">—</option>
        <option v-for="d in dayOptions" :key="d" :value="d">{{ d }}</option>
      </select>
      <ChevronDownIcon class="pointer-events-none absolute right-1.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-600" aria-hidden="true" />
    </div>
    <div class="relative flex-1">
      <select
        :value="month ?? ''"
        class="w-full cursor-pointer appearance-none rounded-lg border border-stone-200 bg-white py-2.5 pl-2.5 pr-6 text-base transition-colors duration-200 focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
        aria-label="Месяц"
        @change="onMonthChange"
      >
        <option value="">Месяц</option>
        <option v-for="(name, idx) in MONTHS" :key="idx" :value="idx + 1">{{ name }}</option>
      </select>
      <ChevronDownIcon class="pointer-events-none absolute right-1.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-600" aria-hidden="true" />
    </div>
    <div class="relative flex-[0_0_5rem]">
      <select
        :value="year ?? ''"
        class="w-full cursor-pointer appearance-none rounded-lg border border-stone-200 bg-white py-2.5 pl-2.5 pr-6 text-base transition-colors duration-200 focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
        aria-label="Год"
        @change="onYearChange"
      >
        <option value="">Год</option>
        <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
      </select>
      <ChevronDownIcon class="pointer-events-none absolute right-1.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-600" aria-hidden="true" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

// Замена нативного <input type="date"> — тот всегда следует локали
// браузера/ОС (даже с lang="ru" на элементе, см. BaseInput), а не языку
// страницы, и может показывать mm/dd/yyyy вместо дд.мм.гггг (ISSUES #38).
// Три select гарантируют русский язык и порядок день/месяц/год независимо
// от локали пользователя. modelValue — "YYYY-MM-DD" или "" (не выбрано),
// как и у нативного input[type=date], чтобы быть прямой заменой.
const props = defineProps({
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const MONTHS = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']

const currentYear = new Date().getFullYear()
const yearOptions = []
for (let y = currentYear - 5; y <= currentYear + 1; y++) yearOptions.push(y)

const parsed = computed(() => {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(props.modelValue || '')
  if (!match) return { day: null, month: null, year: null }
  return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) }
})

const day = computed(() => parsed.value.day)
const month = computed(() => parsed.value.month)
const year = computed(() => parsed.value.year)

function daysInMonth(y, m) {
  if (!y || !m) return 31
  return new Date(y, m, 0).getDate()
}

const dayOptions = computed(() => {
  const max = daysInMonth(year.value, month.value)
  return Array.from({ length: max }, (_, i) => i + 1)
})

function pad(n) {
  return String(n).padStart(2, '0')
}

function emitDate(d, m, y) {
  if (!d || !m || !y) {
    emit('update:modelValue', '')
    return
  }
  const clampedDay = Math.min(d, daysInMonth(y, m))
  emit('update:modelValue', `${y}-${pad(m)}-${pad(clampedDay)}`)
}

function onDayChange(event) {
  emitDate(event.target.value ? Number(event.target.value) : null, month.value, year.value)
}
function onMonthChange(event) {
  emitDate(day.value, event.target.value ? Number(event.target.value) : null, year.value)
}
function onYearChange(event) {
  emitDate(day.value, month.value, event.target.value ? Number(event.target.value) : null)
}
</script>
