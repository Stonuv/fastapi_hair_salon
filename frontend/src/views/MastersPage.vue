<template>
  <div>
    <section class="border-b border-stone-200 bg-white px-4 py-16 text-center sm:px-6">
      <p class="font-mono text-xs uppercase tracking-[0.16em] text-brand-700">Барбершоп «Сайтама»</p>
      <h1 class="mt-3 font-display text-4xl font-black uppercase tracking-tight text-ink-900 sm:text-5xl">
        Мастера, которым доверяют
      </h1>
      <p class="mx-auto mt-3 max-w-md text-ink-600">
        Выберите мастера и запишитесь онлайн за 30 секунд
      </p>
    </section>

    <section class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <!-- Четвёртая колонка (сортировка + кнопка направления) шире 1fr:
           при 4 колонках «По имени» иначе обрезается стрелкой селекта. -->
      <div class="mb-8 grid gap-3" :class="showSalonFilter ? 'sm:grid-cols-2 lg:grid-cols-[2fr_1.4fr_1.4fr_1.3fr]' : 'sm:grid-cols-[2fr_1.5fr_1fr]'">
        <BaseInput v-model="filters.specialization" placeholder="Поиск по специализации…" aria-label="Поиск по специализации" />
        <BaseSelect v-model="filters.service_id" placeholder="Любая услуга" aria-label="Фильтр по услуге">
          <option v-for="s in services" :key="s.id" :value="s.id">{{ s.name }}</option>
        </BaseSelect>
        <!-- Единственную точку фильтровать незачем — показываем, только когда
             в сети реально несколько салонов. -->
        <BaseSelect
          v-if="showSalonFilter"
          v-model="filters.salon_id"
          placeholder="Любая точка"
          aria-label="Фильтр по точке"
        >
          <option v-for="s in salonStore.activeSalons" :key="s.id" :value="s.id">{{ s.name }}</option>
        </BaseSelect>
        <div class="flex gap-3">
          <BaseSelect v-model="filters.sort_by" class="flex-1" aria-label="Сортировка">
            <option value="name">По имени</option>
            <option value="price">По цене</option>
          </BaseSelect>
          <button
            class="flex w-11 shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-white text-ink-600 transition-colors duration-200 hover:border-brand-900 hover:text-brand-900 cursor-pointer"
            :aria-label="filters.sort_order === 'asc' ? 'По возрастанию' : 'По убыванию'"
            @click="filters.sort_order = filters.sort_order === 'asc' ? 'desc' : 'asc'"
          >
            <BarsArrowUpIcon v-if="filters.sort_order === 'asc'" class="h-5 w-5" aria-hidden="true" />
            <BarsArrowDownIcon v-else class="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div v-if="loading" class="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4">
        <div v-for="i in 8" :key="i" class="overflow-hidden rounded-xl border border-stone-200 bg-white">
          <Skeleton height="aspect-[3/4] w-full rounded-none" />
          <div class="space-y-2 p-4">
            <Skeleton width="w-1/2" />
            <Skeleton width="w-3/4" height="h-5" />
          </div>
        </div>
      </div>

      <EmptyState
        v-else-if="masters.length === 0"
        :icon="UserGroupIcon"
        title="Мастера не найдены"
        description="Попробуйте изменить параметры поиска"
      />

      <div v-else class="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4">
        <MasterCard v-for="master in masters" :key="master.id" :master="master" />
      </div>

      <Pagination v-model:page="page" :total-pages="totalPages" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { UserGroupIcon, BarsArrowUpIcon, BarsArrowDownIcon } from '@heroicons/vue/24/outline'
import { mastersApi, servicesApi } from '../api'
import { useSalonStore } from '../stores/salon'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'
import { useDebouncedWatch } from '../composables/useDebouncedWatch'
import MasterCard from '../components/MasterCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseSelect from '../components/ui/BaseSelect.vue'
import Skeleton from '../components/ui/Skeleton.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import Pagination from '../components/ui/Pagination.vue'

const route = useRoute()
const router = useRouter()
const salonStore = useSalonStore()
const toast = useToastStore()

const masters = ref([])
const services = ref([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)

const filters = reactive({
  specialization: '',
  // Приходит из ссылок секции «Наши салоны» на главной (/masters?salon_id=…),
  // поэтому начальное значение берём из query, а не из пустой строки.
  salon_id: typeof route.query.salon_id === 'string' ? route.query.salon_id : '',
  service_id: '',
  sort_by: 'name',
  sort_order: 'asc',
})

const showSalonFilter = computed(() => salonStore.activeSalons.length > 1)

async function loadMasters() {
  loading.value = true
  try {
    const { data } = await mastersApi.list({
      page: page.value,
      page_size: 12,
      specialization: filters.specialization || undefined,
      service_id: filters.service_id || undefined,
      salon_id: filters.salon_id || undefined,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    })
    masters.value = data.items
    totalPages.value = data.total_pages
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить мастеров'))
  } finally {
    loading.value = false
  }
}

async function loadServices() {
  try {
    const { data } = await servicesApi.list({ page: 1, page_size: 20, is_active: true })
    services.value = data.items
  } catch {
    // фильтр по услуге необязателен — тихо игнорируем
  }
}

useDebouncedWatch(() => filters.specialization, () => { page.value = 1; loadMasters() })
useDebouncedWatch(() => [filters.service_id, filters.salon_id, filters.sort_by, filters.sort_order], () => { page.value = 1; loadMasters() }, 0)
useDebouncedWatch(page, loadMasters, 0)

// Держим ?salon_id= в адресе в такт с фильтром: ссылка на конкретную точку
// должна оставаться копируемой, а «назад» из карточки мастера — возвращать
// к тому же отфильтрованному списку. replace, не push — промежуточные
// состояния фильтра не должны копиться в истории браузера.
watch(() => filters.salon_id, (salonId) => {
  const query = { ...route.query }
  if (salonId) query.salon_id = salonId
  else delete query.salon_id
  router.replace({ query })
})

// Навигация на /masters?salon_id=… уже находясь на этой странице (переход из
// секции «Наши салоны») меняет только query — компонент не пересоздаётся.
watch(() => route.query.salon_id, (salonId) => {
  const next = typeof salonId === 'string' ? salonId : ''
  if (next !== filters.salon_id) filters.salon_id = next
})

onMounted(() => {
  loadMasters()
  loadServices()
})
</script>
