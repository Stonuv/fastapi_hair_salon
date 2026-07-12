<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <BaseSelect v-model="statusFilter" class="w-full sm:w-48">
        <option value="">Все статусы</option>
        <option value="pending">Ожидают</option>
        <option value="confirmed">Подтверждены</option>
        <option value="done">Завершены</option>
        <option value="cancelled">Отменены</option>
      </BaseSelect>
      <BaseInput v-model="dateFrom" type="date" class="w-[calc(50%-0.375rem)] sm:w-44" />
      <BaseInput v-model="dateTo" type="date" class="w-[calc(50%-0.375rem)] sm:w-44" />
    </div>

    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 4" :key="i" height="h-24" />
    </div>

    <EmptyState v-else-if="appointments.length === 0" :icon="CalendarDaysIcon" title="Записей не найдено" />

    <div v-else class="space-y-3">
      <AppointmentCard
        v-for="apt in appointments"
        :key="apt.id"
        :appointment="apt"
        :primary-label="apt.client_name"
        :secondary-label="apt.service_name"
      >
        <template #actions>
          <BaseButton
            v-if="RESCHEDULABLE_STATUSES.includes(apt.status)"
            variant="ghost"
            size="sm"
            @click="openReschedule(apt)"
          >
            Перенести
          </BaseButton>
          <BaseButton
            v-for="action in ALLOWED_TRANSITIONS[apt.status]"
            :key="action"
            :variant="action === 'cancelled' ? 'ghost' : 'primary'"
            size="sm"
            :loading="updating === apt.id"
            @click="updateStatus(apt, action)"
          >
            {{ STATUS_ACTION_LABELS[action] }}
          </BaseButton>
        </template>
      </AppointmentCard>
    </div>

    <Pagination v-model:page="page" :total-pages="totalPages" />

    <RescheduleModal v-model:open="rescheduleOpen" :appointment="rescheduleTarget" @rescheduled="load" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { CalendarDaysIcon } from '@heroicons/vue/24/outline'
import { appointmentsApi } from '../../api'
import { useMasterProfileStore } from '../../stores/masterProfile'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import { useDebouncedWatch } from '../../composables/useDebouncedWatch'
import { ALLOWED_TRANSITIONS, RESCHEDULABLE_STATUSES, STATUS_ACTION_LABELS } from '../../utils/appointmentStatus'
import AppointmentCard from '../../components/AppointmentCard.vue'
import RescheduleModal from '../../components/RescheduleModal.vue'
import BaseSelect from '../../components/ui/BaseSelect.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import Pagination from '../../components/ui/Pagination.vue'

const profileStore = useMasterProfileStore()
const toast = useToastStore()

const appointments = ref([])
const loading = ref(true)
const updating = ref(null)
const page = ref(1)
const totalPages = ref(1)
const statusFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')

const rescheduleOpen = ref(false)
const rescheduleTarget = ref(null)

function openReschedule(apt) {
  rescheduleTarget.value = apt
  rescheduleOpen.value = true
}

async function load() {
  loading.value = true
  try {
    const { data } = await appointmentsApi.listForMaster(profileStore.profile.id, {
      page: page.value, page_size: 10,
      status_filter: statusFilter.value || undefined,
      date_from: dateFrom.value ? `${dateFrom.value}T00:00:00` : undefined,
      date_to: dateTo.value ? `${dateTo.value}T23:59:59` : undefined,
    })
    appointments.value = data.items
    totalPages.value = data.total_pages
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить записи'))
  } finally {
    loading.value = false
  }
}

async function updateStatus(apt, newStatus) {
  updating.value = apt.id
  try {
    await appointmentsApi.updateStatus(apt.id, newStatus)
    apt.status = newStatus
    toast.success('Статус записи обновлён')
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось обновить статус'))
  } finally {
    updating.value = null
  }
}

useDebouncedWatch(statusFilter, () => { page.value = 1; load() }, 0)
useDebouncedWatch(dateFrom, () => { page.value = 1; load() }, 300)
useDebouncedWatch(dateTo, () => { page.value = 1; load() }, 300)
useDebouncedWatch(page, load, 0)
onMounted(load)
</script>
