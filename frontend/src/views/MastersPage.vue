<template>
  <div>
    <section class="border-b border-stone-200 bg-white px-4 py-16 text-center sm:px-6">
      <p class="text-sm font-medium uppercase tracking-widest text-brand-700">Барбершоп «Сайтама»</p>
      <h1 class="mt-3 font-display text-4xl font-bold text-ink-900 sm:text-5xl">
        Мастера, которым доверяют
      </h1>
      <p class="mx-auto mt-3 max-w-md text-ink-600">
        Выберите мастера и запишитесь онлайн за 30 секунд
      </p>
    </section>

    <section class="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div class="mb-8 grid gap-3 sm:grid-cols-[2fr_1.5fr_1fr_auto]">
        <BaseInput v-model="filters.specialization" placeholder="Поиск по специализации…" aria-label="Поиск по специализации" />
        <BaseSelect v-model="filters.service_id" placeholder="Любая услуга">
          <option v-for="s in services" :key="s.id" :value="s.id">{{ s.name }}</option>
        </BaseSelect>
        <BaseSelect v-model="filters.sort_by">
          <option value="name">По имени</option>
          <option value="coefficient">По коэффициенту</option>
        </BaseSelect>
        <button
          class="flex items-center justify-center rounded-lg border border-stone-200 bg-white px-3 text-ink-600 transition-colors duration-200 hover:border-brand-900 hover:text-brand-900 cursor-pointer"
          :aria-label="filters.sort_order === 'asc' ? 'По возрастанию' : 'По убыванию'"
          @click="filters.sort_order = filters.sort_order === 'asc' ? 'desc' : 'asc'"
        >
          <BarsArrowUpIcon v-if="filters.sort_order === 'asc'" class="h-5 w-5" aria-hidden="true" />
          <BarsArrowDownIcon v-else class="h-5 w-5" aria-hidden="true" />
        </button>
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
import { onMounted, reactive, ref } from 'vue'
import { UserGroupIcon, BarsArrowUpIcon, BarsArrowDownIcon } from '@heroicons/vue/24/outline'
import { mastersApi, servicesApi } from '../api'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'
import { useDebouncedWatch } from '../composables/useDebouncedWatch'
import MasterCard from '../components/MasterCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseSelect from '../components/ui/BaseSelect.vue'
import Skeleton from '../components/ui/Skeleton.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import Pagination from '../components/ui/Pagination.vue'

const toast = useToastStore()

const masters = ref([])
const services = ref([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)

const filters = reactive({
  specialization: '',
  service_id: '',
  sort_by: 'name',
  sort_order: 'asc',
})

async function loadMasters() {
  loading.value = true
  try {
    const { data } = await mastersApi.list({
      page: page.value,
      page_size: 12,
      specialization: filters.specialization || undefined,
      service_id: filters.service_id || undefined,
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
useDebouncedWatch(() => [filters.service_id, filters.sort_by, filters.sort_order], () => { page.value = 1; loadMasters() }, 0)
useDebouncedWatch(page, loadMasters, 0)

onMounted(() => {
  loadMasters()
  loadServices()
})
</script>
