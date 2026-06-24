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
            <BaseInput
              :model-value="photoEdits[m.id] ?? m.photo_url ?? ''"
              placeholder="URL фото"
              class="w-56"
              @update:model-value="(v) => (photoEdits[m.id] = v)"
            />
            <BaseButton variant="ghost" size="sm" :loading="savingPhoto === m.id" @click="savePhoto(m)">Сохранить фото</BaseButton>
            <BaseButton variant="ghost" size="sm" @click="toggleExpand(m.id)">
              {{ expanded === m.id ? 'Скрыть услуги' : 'Услуги' }}
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

          <form class="mt-3 flex flex-wrap items-end gap-2" @submit.prevent="addService(m)">
            <BaseSelect v-model="newService[m.id]" class="w-52" placeholder="Услуга">
              <option v-for="s in allServices" :key="s.id" :value="s.id">{{ s.name }}</option>
            </BaseSelect>
            <BaseInput v-model="newServicePrice[m.id]" type="number" min="0" step="1" placeholder="Цена (необязательно)" class="w-44" />
            <BaseButton type="submit" size="sm" :disabled="!newService[m.id]">Добавить</BaseButton>
          </form>
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
import Skeleton from '../../components/ui/Skeleton.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import Pagination from '../../components/ui/Pagination.vue'

const toast = useToastStore()

const masters = ref([])
const allServices = ref([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)

const photoEdits = reactive({})
const savingPhoto = ref(null)
const expanded = ref(null)
const masterServices = reactive({})
const newService = reactive({})
const newServicePrice = reactive({})

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

async function savePhoto(master) {
  savingPhoto.value = master.id
  try {
    await adminApi.updateMasterPhoto(master.id, photoEdits[master.id] ?? master.photo_url ?? '')
    master.photo_url = photoEdits[master.id]
    toast.success('Фото обновлено')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  } finally {
    savingPhoto.value = null
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
