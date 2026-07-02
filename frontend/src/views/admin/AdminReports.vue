<template>
  <div class="flex flex-col gap-6">
    <!-- Filter bar -->
    <div class="flex flex-wrap items-end gap-3">
      <div class="flex flex-col gap-1">
        <label for="date-from" class="text-xs font-medium uppercase tracking-wide text-ink-600">С</label>
        <input
          id="date-from"
          v-model="dateFrom"
          type="date"
          :max="dateTo"
          class="rounded-lg border border-stone-200 px-3.5 py-2.5 text-sm focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label for="date-to" class="text-xs font-medium uppercase tracking-wide text-ink-600">По</label>
        <input
          id="date-to"
          v-model="dateTo"
          type="date"
          :min="dateFrom"
          class="rounded-lg border border-stone-200 px-3.5 py-2.5 text-sm focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
        />
      </div>
      <button
        class="rounded-lg bg-brand-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-800 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="loading"
        @click="loadReport"
      >
        Сформировать
      </button>
      <button
        class="ml-auto flex items-center gap-2 rounded-lg border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-ink-900 transition-colors hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="!report || exporting"
        @click="exportToExcel"
      >
        <ArrowDownTrayIcon class="h-4 w-4" aria-hidden="true" />
        {{ exporting ? 'Скачивание…' : 'Экспорт Excel' }}
      </button>
    </div>

    <!-- Loading -->
    <template v-if="loading">
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Skeleton v-for="i in 4" :key="i" height="h-28" />
      </div>
      <div class="grid gap-4 lg:grid-cols-5">
        <Skeleton height="h-72" class="lg:col-span-3" />
        <Skeleton height="h-72" class="lg:col-span-2" />
      </div>
      <Skeleton height="h-64" />
    </template>

    <!-- Empty / initial -->
    <EmptyState
      v-else-if="!report"
      title="Выберите период"
      description="Укажите даты и нажмите «Сформировать», чтобы построить отчёт."
    />

    <!-- Report content -->
    <template v-else>
      <!-- KPI cards -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Общая выручка"
          :value="`${formatMoney(report.total_revenue)} ₽`"
          :icon="BanknotesIcon"
        />
        <KpiCard
          label="Всего записей"
          :value="report.total_appointments"
          :icon="CalendarDaysIcon"
        />
        <KpiCard
          label="Средний чек"
          :value="`${formatMoney(report.avg_check)} ₽`"
          :icon="ReceiptPercentIcon"
        />
        <KpiCard
          label="Повторные клиенты"
          :value="`${report.repeat_clients_pct}%`"
          :icon="ArrowPathIcon"
        />
      </div>

      <!-- Charts row -->
      <div class="grid gap-4 lg:grid-cols-5">
        <!-- Revenue line chart -->
        <BaseCard class="lg:col-span-3">
          <h2 class="mb-4 font-display text-base font-bold uppercase tracking-tight text-ink-900">
            Выручка по времени
          </h2>
          <template v-if="report.revenue_by_day.length">
            <svg
              :viewBox="`0 0 ${chartW} ${chartH}`"
              class="w-full"
              role="img"
              aria-label="Линейный график выручки по дням"
            >
              <!-- Grid lines -->
              <line
                v-for="i in 4"
                :key="i"
                :x1="chartPad"
                :x2="chartW - chartPad"
                :y1="chartPad + (i * chartPlotH) / 4"
                :y2="chartPad + (i * chartPlotH) / 4"
                stroke="#E7DDD0"
                stroke-width="1"
              />
              <!-- Area fill -->
              <path :d="revenueAreaPath" fill="#78350F" fill-opacity="0.07" />
              <!-- Line -->
              <polyline
                :points="revenuePoints"
                fill="none"
                stroke="#78350F"
                stroke-width="2"
                stroke-linejoin="round"
                stroke-linecap="round"
              />
              <!-- Dots -->
              <circle
                v-for="(p, i) in revenueCoords"
                :key="i"
                :cx="p.x"
                :cy="p.y"
                r="3"
                fill="#FBBF24"
                stroke="#78350F"
                stroke-width="1.5"
              />
            </svg>
            <div class="mt-1 flex justify-between text-xs text-ink-600">
              <span>{{ formatDate(report.revenue_by_day[0]?.date) }}</span>
              <span>{{ formatDate(report.revenue_by_day[report.revenue_by_day.length - 1]?.date) }}</span>
            </div>
          </template>
          <EmptyState v-else title="Нет данных за период" />
        </BaseCard>

        <!-- Service bar chart -->
        <BaseCard class="lg:col-span-2">
          <h2 class="mb-4 font-display text-base font-bold uppercase tracking-tight text-ink-900">
            Записи по услугам
          </h2>
          <template v-if="report.appointments_by_service.length">
            <div class="flex flex-col gap-2.5">
              <div
                v-for="row in serviceChartRows"
                :key="row.service_name"
                class="flex flex-col gap-1"
              >
                <div class="flex justify-between text-xs text-ink-600">
                  <span class="truncate pr-2">{{ row.service_name }}</span>
                  <span class="flex-shrink-0 font-medium text-ink-900">{{ row.appointments }}</span>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-stone-100">
                  <div
                    class="h-full rounded-full bg-brand-900 transition-all duration-500"
                    :style="{ width: `${row.pct}%` }"
                  />
                </div>
              </div>
            </div>
          </template>
          <EmptyState v-else title="Нет данных за период" />
        </BaseCard>
      </div>

      <!-- Masters breakdown table -->
      <BaseCard>
        <h2 class="mb-4 font-display text-base font-bold uppercase tracking-tight text-ink-900">
          Детализация по барберам
        </h2>
        <template v-if="report.masters_breakdown.length">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-stone-200 text-left text-xs uppercase tracking-wide text-ink-600">
                  <th class="pb-3 pr-4 font-medium">Барбер</th>
                  <th class="pb-3 pr-4 font-medium">Записей</th>
                  <th class="pb-3 pr-4 font-medium">Выручка</th>
                  <th class="pb-3 pr-4 font-medium">Средний чек</th>
                  <th class="pb-3 font-medium">Рейтинг</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="master in report.masters_breakdown"
                  :key="master.master_name"
                  class="border-b border-stone-100 last:border-0"
                >
                  <td class="py-3 pr-4 font-medium text-ink-900">{{ master.master_name }}</td>
                  <td class="py-3 pr-4 text-ink-600">{{ master.appointments }}</td>
                  <td class="py-3 pr-4 text-ink-900">{{ formatMoney(master.revenue) }} ₽</td>
                  <td class="py-3 pr-4 text-ink-600">{{ formatMoney(master.avg_check) }} ₽</td>
                  <td class="py-3">
                    <span v-if="master.avg_rating !== null" class="flex items-center gap-1">
                      <StarIconSolid class="h-4 w-4 text-accent-400" aria-hidden="true" />
                      {{ master.avg_rating.toFixed(1) }}
                    </span>
                    <span v-else class="text-ink-600">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <EmptyState v-else title="Нет данных за период" />
      </BaseCard>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  BanknotesIcon,
  CalendarDaysIcon,
  ReceiptPercentIcon,
} from '@heroicons/vue/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/vue/24/solid'
import { adminApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import BaseCard from '../../components/ui/BaseCard.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import KpiCard from '../../components/KpiCard.vue'

const toast = useToastStore()

// Отчёты режут сутки по UTC (см. report_repository на бэкенде) —
// дефолтный период строим по UTC-календарю, не смешивая его с локальным.
function todayISO() {
  return new Date().toISOString().slice(0, 10)
}
function firstOfMonthISO() {
  const now = new Date()
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1))
    .toISOString().slice(0, 10)
}

const dateFrom = ref(firstOfMonthISO())
const dateTo = ref(todayISO())
const report = ref(null)
const loading = ref(false)
const exporting = ref(false)

async function loadReport() {
  loading.value = true
  try {
    const { data } = await adminApi.getReport({ date_from: dateFrom.value, date_to: dateTo.value })
    report.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить отчёт'))
  } finally {
    loading.value = false
  }
}

async function exportToExcel() {
  exporting.value = true
  try {
    const { data } = await adminApi.exportReport({ date_from: dateFrom.value, date_to: dateTo.value })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${dateFrom.value}_${dateTo.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось экспортировать отчёт'))
  } finally {
    exporting.value = false
  }
}

function formatMoney(value) {
  return Number(value).toLocaleString('ru', { maximumFractionDigits: 0 })
}

function formatDate(iso) {
  if (!iso) return ''
  // Бэкенд отдаёт голую дату ("2026-07-01" = полночь UTC) — без timeZone
  // браузер западнее UTC показал бы предыдущий день.
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'short', timeZone: 'UTC' })
}

// ── Line chart ────────────────────────────────────────────────────
const chartW = 600
const chartH = 200
const chartPad = 8
const chartPlotH = chartH - chartPad * 2

const revenueCoords = computed(() => {
  const data = report.value?.revenue_by_day ?? []
  const n = data.length
  if (n === 0) return []
  const maxVal = Math.max(1, ...data.map((d) => d.revenue))
  const step = (chartW - chartPad * 2) / Math.max(1, n - 1)
  return data.map((d, i) => ({
    x: chartPad + i * step,
    y: chartPad + chartPlotH - (d.revenue / maxVal) * chartPlotH,
  }))
})

const revenuePoints = computed(() => revenueCoords.value.map((p) => `${p.x},${p.y}`).join(' '))

const revenueAreaPath = computed(() => {
  const pts = revenueCoords.value
  if (pts.length < 2) return ''
  const bottom = chartPad + chartPlotH
  const first = pts[0]
  const last = pts[pts.length - 1]
  return `M${first.x},${bottom} L${pts.map((p) => `${p.x},${p.y}`).join(' L')} L${last.x},${bottom} Z`
})

// ── Bar chart ─────────────────────────────────────────────────────
const serviceChartRows = computed(() => {
  const rows = report.value?.appointments_by_service ?? []
  const maxCount = Math.max(1, ...rows.map((r) => r.appointments))
  return rows.slice(0, 8).map((r) => ({
    ...r,
    pct: (r.appointments / maxCount) * 100,
  }))
})
</script>
