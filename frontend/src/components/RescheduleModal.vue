<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" @click="close" />
      <div class="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg border border-stone-200 bg-white p-6 shadow-lg" role="dialog" aria-modal="true">
        <h2 class="font-display text-lg font-bold uppercase tracking-tight text-ink-900">Перенести запись</h2>
        <p class="mt-1 text-sm text-ink-600">{{ appointment?.client_name }} · {{ appointment?.service_name }}</p>

        <div class="mt-4">
          <p class="mb-2 text-sm font-medium text-ink-900">Новая дата</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="d in availableDates"
              :key="d.iso"
              type="button"
              class="flex w-20 flex-shrink-0 cursor-pointer flex-col items-center rounded-lg border px-3 py-2 transition-colors duration-200"
              :class="selectedDate === d.iso ? 'border-brand-900 bg-accent-100/60' : 'border-stone-200 bg-white hover:border-brand-900/50'"
              @click="selectDate(d.iso)"
            >
              <span class="font-mono text-xs uppercase tracking-wide text-brand-700">{{ d.day }}</span>
              <span class="mt-0.5 text-sm text-ink-900">{{ d.label }}</span>
            </button>
          </div>
        </div>

        <div v-if="selectedDate" class="mt-4">
          <p class="mb-2 text-sm font-medium text-ink-900">Новое время</p>
          <div v-if="slotsLoading" class="flex flex-wrap gap-2">
            <Skeleton v-for="i in 6" :key="i" width="w-20" height="h-10" />
          </div>
          <EmptyState v-else-if="slots.length === 0" title="Нет свободного времени" description="Выберите другую дату" />
          <div v-else class="flex flex-wrap gap-2">
            <button
              v-for="slot in slots"
              :key="slot.start_time"
              type="button"
              class="cursor-pointer rounded-lg border px-4 py-2 font-mono text-sm transition-colors duration-200"
              :class="selectedSlot?.start_time === slot.start_time
                ? 'border-brand-900 bg-brand-900 text-white'
                : 'border-stone-200 bg-white text-ink-900 hover:border-brand-900/50'"
              @click="selectedSlot = slot"
            >
              {{ formatTime(slot.start_time) }}
            </button>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <BaseButton variant="ghost" size="sm" @click="close">Отмена</BaseButton>
          <BaseButton size="sm" :disabled="!selectedSlot" :loading="loading" @click="confirm">Перенести</BaseButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { appointmentsApi, mastersApi } from '../api'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'
import BaseButton from './ui/BaseButton.vue'
import Skeleton from './ui/Skeleton.vue'
import EmptyState from './ui/EmptyState.vue'

const props = defineProps({
  open: Boolean,
  appointment: Object,
})
const emit = defineEmits(['update:open', 'rescheduled'])

const toast = useToastStore()

const selectedDate = ref(null)
const selectedSlot = ref(null)
const slots = ref([])
const slotsLoading = ref(false)
const loading = ref(false)

// Тот же приём, что и на BookingPage.vue: расписание салона — «настенные
// часы» в UTC, поэтому список дат строится по UTC-календарю.
const availableDates = computed(() => {
  const days = []
  const labels = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
  const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
  for (let i = 0; i < 14; i++) {
    const d = new Date()
    d.setUTCDate(d.getUTCDate() + i)
    days.push({
      iso: d.toISOString().slice(0, 10),
      day: labels[d.getUTCDay()],
      label: `${d.getUTCDate()} ${months[d.getUTCMonth()]}`,
    })
  }
  return days
})

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    selectedDate.value = null
    selectedSlot.value = null
    slots.value = []
  }
})

async function selectDate(iso) {
  selectedDate.value = iso
  selectedSlot.value = null
  slotsLoading.value = true
  try {
    // exclude_appointment_id — текущий слот переносимой записи не должен
    // считаться занятым (иначе мастер не смог бы сдвинуть время в тот же день).
    const { data } = await mastersApi.getSlots(
      props.appointment.master_id, props.appointment.service_id, iso, props.appointment.id
    )
    slots.value = data.slots
  } catch (err) {
    slots.value = []
    toast.error(extractErrorMessage(err, 'Не удалось загрузить свободное время'))
  } finally {
    slotsLoading.value = false
  }
}

function close() {
  emit('update:open', false)
}

async function confirm() {
  loading.value = true
  try {
    await appointmentsApi.reschedule(props.appointment.id, selectedSlot.value.start_time)
    toast.success('Запись перенесена')
    emit('rescheduled', selectedSlot.value.start_time)
    close()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось перенести запись'))
  } finally {
    loading.value = false
  }
}

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })
}
</script>
