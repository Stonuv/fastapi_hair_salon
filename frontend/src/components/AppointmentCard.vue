<template>
  <BaseCard class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <StatusPill :status="appointment.status" />
      <p class="mt-2 font-medium text-ink-900">{{ primaryLabel }}</p>
      <p class="text-sm text-ink-600">{{ secondaryLabel }}</p>
      <p class="text-sm text-ink-600">
        {{ formatDate(appointment.start_time) }} · {{ formatTime(appointment.start_time) }}–{{ formatTime(appointment.end_time) }}
      </p>
    </div>
    <div class="flex flex-shrink-0 flex-wrap items-center gap-3">
      <p class="font-semibold text-brand-900">{{ appointment.final_price }} ₽</p>
      <slot name="actions" />
    </div>
  </BaseCard>
</template>

<script setup>
import BaseCard from './ui/BaseCard.vue'
import StatusPill from './ui/StatusPill.vue'

defineProps({
  appointment: { type: Object, required: true },
  primaryLabel: { type: String, required: true },
  secondaryLabel: { type: String, default: '' },
})

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long' })
}
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
}
</script>
