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

      <!-- aria-live=polite, а не assertive: экранный диктор дочитает текущую
           фразу и только потом сообщит об обновлении — числа на экране не
           настолько срочны, чтобы перебивать пользователя каждые 30 секунд. -->
      <p class="mt-4 font-mono text-[11px] uppercase tracking-wide text-ink-600" aria-live="polite">
        <template v-if="staleSince">
          Данные от {{ updatedAtLabel }} — обновить не удалось, следующая попытка через {{ REFRESH_SECONDS }} с
        </template>
        <template v-else>
          Обновлено в {{ updatedAtLabel }} · автообновление каждые {{ REFRESH_SECONDS }} с
        </template>
      </p>
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
import { usePolling } from '../../composables/usePolling'
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
const updatedAt = ref(null)
// Момент последней УДАЧНОЙ загрузки остаётся в updatedAt, а staleSince
// отмечает, что с тех пор попытка провалилась: показывать нечего, кроме
// прежних чисел, но выдавать их за свежие нельзя.
const staleSince = ref(false)

// 30 секунд: статистика админки — это регистрации и записи за месяц, они не
// меняются чаще; интервал заметно короче сделал бы из KPI-плиток источник
// постоянной нагрузки на /admin/stats без пользы для читателя.
const REFRESH_SECONDS = 30

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

const updatedAtLabel = computed(() =>
  updatedAt.value?.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) ?? '',
)

/**
 * background=true — тик автообновления: числа заменяются на месте, без
 * скелетонов (иначе панель мигала бы пустыми плитками каждые 30 секунд) и
 * без тоста на ошибку (иначе к утру экран был бы завален одинаковыми
 * сообщениями). Провал фонового тика виден строкой «данные от ...» под
 * графиком, а сам запрос помечен для перехватчика в api/client.js, чтобы
 * 5xx в фоне не уводил админа с открытой панели на страницу /500.
 */
async function load({ background = false } = {}) {
  if (!background) loading.value = true
  try {
    const { data } = await adminApi.getStats(
      { salon_id: viewingSalonId.value ?? undefined },
      { background },
    )
    stats.value = data
    updatedAt.value = new Date()
    staleSince.value = false
  } catch (err) {
    if (background) staleSince.value = true
    else toast.error(extractErrorMessage(err, 'Не удалось загрузить статистику'))
  } finally {
    if (!background) loading.value = false
  }
}

// Смена точки сети — это другой набор данных, а не обновление текущего:
// здесь скелетоны уместны, показывать чужие числа под новым заголовком нельзя.
watch(viewingSalonId, () => load())
onMounted(() => load())
usePolling(() => load({ background: true }), REFRESH_SECONDS * 1000)
</script>
