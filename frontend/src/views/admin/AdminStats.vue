<template>
  <div>
    <div v-if="loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Skeleton v-for="i in 4" :key="i" height="h-28" />
    </div>

    <template v-else-if="stats">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Пользователей всего" :value="stats.total_users" :icon="UsersIcon" />
        <KpiCard label="Клиентов" :value="stats.total_clients" :icon="UserIcon" />
        <KpiCard label="Активных мастеров" :value="stats.total_masters" :icon="UserGroupIcon" />
        <KpiCard label="Активных услуг" :value="stats.total_services" :icon="ScissorsIcon" />
      </div>

      <div class="mt-4 grid gap-4 sm:grid-cols-2">
        <KpiCard label="Записей в этом месяце" :value="stats.appointments_this_month" :icon="CalendarDaysIcon" />
        <KpiCard label="Выручка в этом месяце" :value="`${stats.revenue_this_month} ₽`" :icon="BanknotesIcon" />
      </div>

      <BaseCard class="mt-6">
        <h2 class="mb-4 font-display text-lg font-bold uppercase tracking-tight text-ink-900">Регистрации за последние 30 дней</h2>
        <RegistrationsChart v-if="stats.registrations_last_30_days.length" :data="stats.registrations_last_30_days" />
        <EmptyState v-else title="Пока нет данных" />
      </BaseCard>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import {
  UsersIcon, UserIcon, UserGroupIcon, ScissorsIcon, CalendarDaysIcon, BanknotesIcon,
} from '@heroicons/vue/24/outline'
import { adminApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import BaseCard from '../../components/ui/BaseCard.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import KpiCard from '../../components/KpiCard.vue'
import RegistrationsChart from '../../components/RegistrationsChart.vue'

const toast = useToastStore()
const stats = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await adminApi.getStats()
    stats.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить статистику'))
  } finally {
    loading.value = false
  }
})
</script>
