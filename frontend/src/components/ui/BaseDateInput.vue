<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="flex w-full cursor-pointer items-center justify-between gap-2 rounded-lg border border-stone-200 bg-white px-3.5 py-2.5 text-left text-base transition-colors duration-200 focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
      :class="open ? 'border-brand-900 ring-2 ring-brand-900/30' : ''"
      @click="open = !open"
    >
      <span :class="selected ? 'text-ink-900' : 'text-ink-600/70'">{{ label }}</span>
      <CalendarDaysIcon class="h-4 w-4 shrink-0 text-ink-600" aria-hidden="true" />
    </button>

    <div v-if="open" class="absolute left-0 top-full z-50 mt-2 w-72 rounded-lg border border-stone-200 bg-white p-3 shadow-lg">
      <div class="mb-2 flex items-center justify-between">
        <button type="button" class="cursor-pointer rounded p-1 text-ink-600 hover:bg-stone-100 hover:text-ink-900" aria-label="Предыдущий месяц" @click="shiftMonth(-1)">
          <ChevronLeftIcon class="h-4 w-4" aria-hidden="true" />
        </button>
        <span class="font-mono text-xs uppercase tracking-wide text-ink-900">{{ MONTHS[view.month - 1] }} {{ view.year }}</span>
        <button type="button" class="cursor-pointer rounded p-1 text-ink-600 hover:bg-stone-100 hover:text-ink-900" aria-label="Следующий месяц" @click="shiftMonth(1)">
          <ChevronRightIcon class="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      <div class="grid grid-cols-7 gap-y-1 text-center">
        <span v-for="w in WEEKDAYS" :key="w" class="font-mono text-[10px] uppercase tracking-wide text-ink-600/70">{{ w }}</span>
        <button
          v-for="cell in cells" :key="`${cell.year}-${cell.month}-${cell.day}`"
          type="button"
          class="mx-auto flex h-8 w-8 cursor-pointer items-center justify-center rounded-full text-sm transition-colors duration-150"
          :class="cellClass(cell)"
          @click="selectCell(cell)"
        >{{ cell.day }}</button>
      </div>

      <div class="mt-2 flex items-center justify-between border-t border-stone-200 pt-2">
        <button type="button" class="cursor-pointer font-mono text-[11px] uppercase tracking-wide text-brand-700 hover:underline" @click="goToday">Сегодня</button>
        <button v-if="selected" type="button" class="cursor-pointer font-mono text-[11px] uppercase tracking-wide text-ink-600 hover:underline" @click="clear">Очистить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { CalendarDaysIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

// Замена нативного <input type="date"> — тот всегда следует локали
// браузера/ОС (даже с lang="ru" на элементе, см. BaseInput), а не языку
// страницы, и может показывать mm/dd/yyyy вместо дд.мм.гггг (ISSUES #38).
// Настоящий календарь (сетка дней с навигацией по месяцам), а не три
// select — тексты и порядок недели жёстко на русском независимо от
// локали пользователя. modelValue — "YYYY-MM-DD" или "" (не выбрано),
// как и у нативного input[type=date], чтобы быть прямой заменой.
const props = defineProps({
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const root = ref(null)
const open = ref(false)

const today = new Date()

const parsed = computed(() => {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(props.modelValue || '')
  if (!match) return null
  return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) }
})
const selected = computed(() => parsed.value)

const view = reactive({
  year: parsed.value?.year ?? today.getFullYear(),
  month: parsed.value?.month ?? today.getMonth() + 1,
})

const label = computed(() => {
  if (!selected.value) return 'Выберите дату'
  const { year, month, day } = selected.value
  return new Date(year, month - 1, day).toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })
})

function daysInMonth(y, m) {
  return new Date(y, m, 0).getDate()
}

// Понедельник = 0 ... Воскресенье = 6 (JS Date.getDay() даёт 0 = воскресенье).
function mondayIndex(y, m, d) {
  return (new Date(y, m - 1, d).getDay() + 6) % 7
}

const cells = computed(() => {
  const { year, month } = view
  const leading = mondayIndex(year, month, 1)
  const total = daysInMonth(year, month)
  const prevYear = month === 1 ? year - 1 : year
  const prevMonth = month === 1 ? 12 : month - 1
  const prevTotal = daysInMonth(prevYear, prevMonth)
  const nextYear = month === 12 ? year + 1 : year
  const nextMonth = month === 12 ? 1 : month + 1

  const result = []
  for (let i = leading - 1; i >= 0; i--) {
    result.push({ year: prevYear, month: prevMonth, day: prevTotal - i, otherMonth: true })
  }
  for (let d = 1; d <= total; d++) {
    result.push({ year, month, day: d, otherMonth: false })
  }
  let nextDay = 1
  while (result.length < 42) {
    result.push({ year: nextYear, month: nextMonth, day: nextDay++, otherMonth: true })
  }
  return result
})

function isSameDate(a, b) {
  return !!a && !!b && a.year === b.year && a.month === b.month && a.day === b.day
}

function cellClass(cell) {
  const isSelected = isSameDate(cell, selected.value)
  const isToday = isSameDate(cell, { year: today.getFullYear(), month: today.getMonth() + 1, day: today.getDate() })
  if (isSelected) return 'bg-brand-900 text-white font-medium'
  if (cell.otherMonth) return 'text-ink-600/40 hover:bg-stone-100'
  if (isToday) return 'border border-brand-900 text-ink-900 hover:bg-stone-100'
  return 'text-ink-900 hover:bg-stone-100'
}

function pad(n) {
  return String(n).padStart(2, '0')
}

function shiftMonth(delta) {
  let m = view.month + delta
  let y = view.year
  if (m < 1) { m = 12; y -= 1 }
  if (m > 12) { m = 1; y += 1 }
  view.month = m
  view.year = y
}

function selectCell(cell) {
  view.year = cell.year
  view.month = cell.month
  emit('update:modelValue', `${cell.year}-${pad(cell.month)}-${pad(cell.day)}`)
  open.value = false
}

function goToday() {
  view.year = today.getFullYear()
  view.month = today.getMonth() + 1
  emit('update:modelValue', `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`)
  open.value = false
}

function clear() {
  emit('update:modelValue', '')
  open.value = false
}

function onDocumentMousedown(event) {
  if (open.value && root.value && !root.value.contains(event.target)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', onDocumentMousedown))
onBeforeUnmount(() => document.removeEventListener('mousedown', onDocumentMousedown))
</script>
