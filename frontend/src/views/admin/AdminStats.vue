<template>
  <div>
    <div v-if="loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Skeleton v-for="i in 4" :key="i" height="h-28" />
    </div>

    <template v-else-if="stats">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <!-- Клиенты и услуги — сетевые всегда: аккаунт один на всю сеть
             (§4.5), каталог общий (§4.3). Скоупятся только мастера, записи и
             выручка. Пометки появляются, только когда выбрана конкретная
             точка: при просмотре всей сети они верны, но бессмысленны —
             область уже написана в переключателе над таблицей. -->
        <KpiCard :label="network('Пользователей всего')" :value="stats.total_users" :icon="UsersIcon" />
        <KpiCard :label="network('Клиентов')" :value="stats.total_clients" :icon="UserIcon" />
        <KpiCard :label="scoped('Активных мастеров')" :value="stats.total_masters" :icon="UserGroupIcon" />
        <KpiCard :label="network('Активных услуг')" :value="stats.total_services" :icon="ScissorsIcon" />
      </div>

      <div class="mt-4 grid gap-4 sm:grid-cols-2">
        <KpiCard :label="scoped('Записей в этом месяце')" :value="stats.appointments_this_month" :icon="CalendarDaysIcon" />
        <KpiCard :label="scoped('Выручка в этом месяце')" :value="`${stats.revenue_this_month} ₽`" :icon="BanknotesIcon" />
      </div>

      <BaseCard class="mt-6">
        <h2 class="mb-4 font-display text-lg font-bold uppercase tracking-tight text-ink-900">
          {{ network('Регистрации за последние 30 дней') }}
        </h2>
        <RegistrationsChart v-if="stats.registrations_last_30_days.length" :data="stats.registrations_last_30_days" />
        <EmptyState v-else title="Пока нет данных" />
      </BaseCard>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  UsersIcon, UserIcon, UserGroupIcon, ScissorsIcon, CalendarDaysIcon, BanknotesIcon,
} from '@heroicons/vue/24/outline'
import { storeToRefs } from 'pinia'
import { adminApi } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { useSalonStore } from '../../stores/salon'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import BaseCard from '../../components/ui/BaseCard.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import KpiCard from '../../components/KpiCard.vue'
import RegistrationsChart from '../../components/RegistrationsChart.vue'

const auth = useAuthStore()
const salonStore = useSalonStore()
const { viewingSalonId, viewingSalon } = storeToRefs(salonStore)
const toast = useToastStore()
const stats = ref(null)
const loading = ref(true)

// Для admin переключателя нет — он и так всегда видит свою точку (бэкенд
// сузит сам), поэтому подпись берём из его собственного салона.
const scopeName = computed(() => (auth.isOwner ? viewingSalon.value?.name : auth.salon?.name))
// Суженные метрики названием точки НЕ подписываем: она и так написана в
// переключателе над таблицей, а дублирование в каждой плитке разносит их по
// высоте на 2–4 строки. Помечаем наоборот — исключения, которые остаются
// сетевыми при выбранной точке; без пометки соседние числа противоречили бы
// друг другу («мастеров 0» рядом с «пользователей 3»).
const scoped = (label) => label
const network = (label) => (scopeName.value ? `${label} (вся сеть)` : label)

async function load() {
  loading.value = true
  try {
    const { data } = await adminApi.getStats({ salon_id: viewingSalonId.value ?? undefined })
    stats.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить статистику'))
  } finally {
    loading.value = false
  }
}

watch(viewingSalonId, load)
onMounted(load)
</script>
