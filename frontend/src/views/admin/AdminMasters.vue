<template>
  <div>
    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 3" :key="i" height="h-24" />
    </div>

    <EmptyState v-else-if="masters.length === 0" :icon="UserGroupIcon" title="Мастера не найдены" />

    <div v-else class="space-y-3">
      <BaseCard v-for="m in masters" :key="m.id">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p class="font-medium text-ink-900">{{ m.first_name }} {{ m.last_name }}</p>
            <p class="text-sm text-ink-600">{{ m.specialization || 'Без специализации' }}</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <ImageUpload :model-value="m.photo_url" @update:model-value="(url) => updatePhoto(m, url)" />
            <BaseButton variant="ghost" size="sm" @click="toggleExpand(m.id)">
              {{ expanded === m.id ? 'Скрыть услуги' : 'Услуги' }}
            </BaseButton>
            <BaseButton variant="ghost" size="sm" @click="toggleSchedule(m.id)">
              {{ expandedSchedule === m.id ? 'Скрыть расписание' : 'Расписание' }}
            </BaseButton>
          </div>
        </div>

        <div v-if="expanded === m.id" class="mt-4 border-t border-stone-200 pt-4">
          <div v-if="masterServices[m.id]?.loading" class="space-y-2">
            <Skeleton height="h-10" />
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="ms in masterServices[m.id]?.items ?? []"
              :key="ms.service.id"
              class="flex items-center justify-between rounded-lg border border-stone-200 px-3 py-2"
            >
              <span class="text-sm text-ink-900">{{ ms.service.name }} — {{ ms.final_price }} ₽</span>
              <button class="cursor-pointer text-danger hover:opacity-80" aria-label="Убрать услугу" @click="removeService(m, ms.service.id)">
                <XMarkIcon class="h-4 w-4" />
              </button>
            </div>
            <p v-if="!masterServices[m.id]?.items?.length" class="text-sm text-ink-600">Нет услуг</p>
          </div>

          <form class="mt-3 flex flex-wrap items-end gap-2" novalidate @submit.prevent="addService(m)">
            <BaseSelect v-model="newService[m.id]" class="w-52" placeholder="Услуга">
              <option v-for="s in allServices" :key="s.id" :value="s.id">{{ s.name }}</option>
            </BaseSelect>
            <BaseInput v-model="newServicePrice[m.id]" type="number" min="0" step="1" placeholder="Цена (необязательно)" class="w-44" />
            <BaseButton type="submit" size="sm" :disabled="!newService[m.id]">Добавить</BaseButton>
          </form>
        </div>

        <div v-if="expandedSchedule === m.id" class="mt-4 border-t border-stone-200 pt-4">
          <div v-if="schedules[m.id]?.loading" class="space-y-2">
            <Skeleton height="h-10" />
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="day in schedules[m.id]?.days ?? []"
              :key="day.value"
              class="flex flex-wrap items-center gap-3 rounded-lg border border-stone-200 px-3 py-2"
            >
              <BaseCheckbox v-model="day.is_working" class="w-32 flex-shrink-0 text-sm font-medium text-ink-900">
                {{ day.label }}
              </BaseCheckbox>
              <template v-if="day.is_working">
                <BaseTimeInput v-model="day.start_time" />
                <span class="text-ink-600">—</span>
                <BaseTimeInput v-model="day.end_time" />
              </template>
              <span v-else class="text-sm text-ink-600">Выходной</span>
              <BaseButton
                size="sm"
                variant="ghost"
                class="ml-auto"
                :loading="savingScheduleDay === `${m.id}-${day.value}`"
                @click="saveScheduleDay(m, day)"
              >
                Сохранить
              </BaseButton>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>

    <Pagination v-model:page="page" :total-pages="totalPages" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { UserGroupIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { adminApi, mastersApi, servicesApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import { useDebouncedWatch } from '../../composables/useDebouncedWatch'
import BaseCard from '../../components/ui/BaseCard.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseSelect from '../../components/ui/BaseSelect.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseCheckbox from '../../components/ui/BaseCheckbox.vue'
import BaseTimeInput from '../../components/ui/BaseTimeInput.vue'
import ImageUpload from '../../components/ui/ImageUpload.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import Pagination from '../../components/ui/Pagination.vue'

const toast = useToastStore()

const masters = ref([])
const allServices = ref([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)

const expanded = ref(null)
const masterServices = reactive({})
const newService = reactive({})
const newServicePrice = reactive({})

const expandedSchedule = ref(null)
const schedules = reactive({})
const savingScheduleDay = ref(null)
const dayLabels = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

async function load() {
  loading.value = true
  try {
    const { data } = await mastersApi.list({ page: page.value, page_size: 10 })
    masters.value = data.items
    totalPages.value = data.total_pages
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить мастеров'))
  } finally {
    loading.value = false
  }
}

async function updatePhoto(master, url) {
  try {
    await adminApi.updateMasterPhoto(master.id, url)
    master.photo_url = url
    toast.success(url ? 'Фото обновлено' : 'Фото убрано')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  }
}

async function toggleExpand(masterId) {
  expanded.value = expanded.value === masterId ? null : masterId
  if (expanded.value && !masterServices[masterId]) {
    masterServices[masterId] = { loading: true, items: [] }
    try {
      const { data } = await mastersApi.getServices(masterId)
      masterServices[masterId] = { loading: false, items: data }
    } catch {
      masterServices[masterId] = { loading: false, items: [] }
    }
  }
}

async function addService(master) {
  try {
    await mastersApi.addService(master.id, newService[master.id], newServicePrice[master.id] || undefined)
    toast.success('Услуга добавлена')
    newService[master.id] = ''
    newServicePrice[master.id] = ''
    const { data } = await mastersApi.getServices(master.id)
    masterServices[master.id] = { loading: false, items: data }
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось добавить услугу'))
  }
}

async function removeService(master, serviceId) {
  try {
    await mastersApi.removeService(master.id, serviceId)
    masterServices[master.id].items = masterServices[master.id].items.filter((ms) => ms.service.id !== serviceId)
    toast.success('Услуга убрана')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  }
}

async function toggleSchedule(masterId) {
  expandedSchedule.value = expandedSchedule.value === masterId ? null : masterId
  if (expandedSchedule.value && !schedules[masterId]) {
    schedules[masterId] = {
      loading: true,
      days: dayLabels.map((label, value) => ({ value, label, is_working: false, start_time: '09:00', end_time: '18:00' })),
    }
    try {
      const { data } = await mastersApi.getSchedule(masterId)
      for (const entry of data) {
        const day = schedules[masterId].days[entry.day_of_week]
        day.is_working = entry.is_working
        day.start_time = entry.start_time.slice(0, 5)
        day.end_time = entry.end_time.slice(0, 5)
      }
    } catch (err) {
      toast.error(extractErrorMessage(err, 'Не удалось загрузить расписание'))
    } finally {
      schedules[masterId].loading = false
    }
  }
}

async function saveScheduleDay(master, day) {
  savingScheduleDay.value = `${master.id}-${day.value}`
  try {
    await mastersApi.setSchedule(master.id, {
      day_of_week: day.value,
      start_time: `${day.start_time}:00`,
      end_time: `${day.end_time}:00`,
      is_working: day.is_working,
    })
    toast.success(`Расписание на ${day.label.toLowerCase()} сохранено`)
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось сохранить расписание'))
  } finally {
    savingScheduleDay.value = null
  }
}

useDebouncedWatch(page, load, 0)
onMounted(async () => {
  load()
  try {
    const { data } = await servicesApi.list({ page: 1, page_size: 20, is_active: true })
    allServices.value = data.items
  } catch {
    // форма добавления услуги просто останется пустой
  }
})
</script>
