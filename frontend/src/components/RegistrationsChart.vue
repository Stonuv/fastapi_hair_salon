<template>
  <div>
    <svg :viewBox="`0 0 ${width} ${height}`" class="w-full" role="img" :aria-label="ariaLabel">
      <line
        v-for="i in 4" :key="i"
        :x1="padding" :x2="width - padding"
        :y1="padding + (i * plotHeight) / 4" :y2="padding + (i * plotHeight) / 4"
        stroke="#E3E1DC" stroke-width="1"
      />
      <polyline :points="points" fill="none" stroke="#111111" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
      <circle v-for="(p, i) in coords" :key="i" :cx="p.x" :cy="p.y" r="3" fill="#FBBF24" stroke="#111111" stroke-width="1.5" />
    </svg>
    <div class="mt-1 flex justify-between text-xs text-ink-600">
      <span>{{ formatDate(data[0]?.date) }}</span>
      <span>{{ formatDate(data[data.length - 1]?.date) }}</span>
    </div>
    <table class="sr-only">
      <caption>Регистрации по дням</caption>
      <tbody>
        <tr v-for="d in data" :key="d.date"><th scope="row">{{ d.date }}</th><td>{{ d.count }}</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: Array, default: () => [] } })

const width = 600
const height = 180
const padding = 8
const plotHeight = height - padding * 2

const ariaLabel = computed(() => `График регистраций: ${props.data.length} дней данных`)

const maxCount = computed(() => Math.max(1, ...props.data.map((d) => d.count)))

const coords = computed(() => {
  const n = props.data.length
  if (n === 0) return []
  const step = (width - padding * 2) / Math.max(1, n - 1)
  return props.data.map((d, i) => ({
    x: padding + i * step,
    y: padding + plotHeight - (d.count / maxCount.value) * plotHeight,
  }))
})

const points = computed(() => coords.value.map((p) => `${p.x},${p.y}`).join(' '))

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'short' })
}
</script>
