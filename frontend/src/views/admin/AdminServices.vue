<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap gap-3">
        <BaseInput v-model="search" placeholder="Поиск по названию…" aria-label="Поиск" />
        <BaseSelect v-model="isActive" placeholder="Любой статус">
          <option value="true">Активные</option>
          <option value="false">Неактивные</option>
        </BaseSelect>
      </div>
      <BaseButton @click="openCreate">Создать услугу</BaseButton>
    </div>

    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 4" :key="i" height="h-20" />
    </div>

    <EmptyState v-else-if="services.length === 0" :icon="ScissorsIcon" title="Услуги не найдены" />

    <div v-else class="space-y-3">
      <BaseCard v-for="s in services" :key="s.id" class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <p class="font-medium text-ink-900">{{ s.name }}</p>
            <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="s.is_active ? 'bg-green-100 text-green-800' : 'bg-stone-200 text-ink-600'">
              {{ s.is_active ? 'Активна' : 'Скрыта' }}
            </span>
          </div>
          <p class="text-sm text-ink-600">{{ s.duration_min }} мин · {{ s.price }} ₽</p>
        </div>
        <div class="flex items-center gap-2">
          <BaseButton variant="ghost" size="sm" @click="openEdit(s)">Редактировать</BaseButton>
          <BaseButton variant="danger" size="sm" @click="serviceToDelete = s">Удалить</BaseButton>
        </div>
      </BaseCard>
    </div>

    <Pagination v-model:page="page" :total-pages="totalPages" />

    <Teleport to="body">
      <div v-if="formOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" @click="formOpen = false" />
        <BaseCard class="relative w-full max-w-md">
          <h2 class="text-lg font-semibold text-ink-900">{{ editingId ? 'Редактировать услугу' : 'Новая услуга' }}</h2>
          <form class="mt-4 space-y-4" novalidate @submit.prevent="submitForm">
            <BaseInput v-model="form.name" label="Название" required />
            <BaseInput v-model="form.description" as="textarea" label="Описание" hint="Необязательно" />
            <div class="grid grid-cols-2 gap-3">
              <BaseInput v-model="form.price" type="number" min="1" step="1" label="Цена, ₽" required />
              <BaseInput v-model="form.duration_min" type="number" min="5" step="5" label="Длительность, мин" required />
            </div>
            <label v-if="editingId" class="flex items-center gap-2 text-sm text-ink-900">
              <input v-model="form.is_active" type="checkbox" class="h-5 w-5 cursor-pointer rounded border-stone-200 text-brand-900" />
              Активна в каталоге
            </label>
            <div class="flex justify-end gap-3">
              <BaseButton variant="ghost" size="sm" type="button" @click="formOpen = false">Отмена</BaseButton>
              <BaseButton size="sm" type="submit" :loading="saving">Сохранить</BaseButton>
            </div>
          </form>
        </BaseCard>
      </div>
    </Teleport>

    <ConfirmDialog
      :open="!!serviceToDelete"
      title="Скрыть услугу?"
      :message="serviceToDelete ? `Услуга «${serviceToDelete.name}» будет скрыта из каталога.` : ''"
      confirm-label="Скрыть"
      danger
      :loading="deleting"
      @update:open="serviceToDelete = null"
      @confirm="deleteService"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ScissorsIcon } from '@heroicons/vue/24/outline'
import { adminApi, servicesApi } from '../../api'
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
import ConfirmDialog from '../../components/ui/ConfirmDialog.vue'

const toast = useToastStore()

const services = ref([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)
const search = ref('')
const isActive = ref('')

async function load() {
  loading.value = true
  try {
    const { data } = await servicesApi.list({
      page: page.value, page_size: 10,
      search: search.value || undefined,
      is_active: isActive.value === '' ? undefined : isActive.value === 'true',
    })
    services.value = data.items
    totalPages.value = data.total_pages
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить услуги'))
  } finally {
    loading.value = false
  }
}

// ── Форма создания/редактирования ─────────────────────────────────
const formOpen = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = reactive({ name: '', description: '', price: '', duration_min: '', is_active: true })

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', description: '', price: '', duration_min: '', is_active: true })
  formOpen.value = true
}

function openEdit(service) {
  editingId.value = service.id
  Object.assign(form, {
    name: service.name,
    description: service.description || '',
    price: service.price,
    duration_min: service.duration_min,
    is_active: service.is_active,
  })
  formOpen.value = true
}

async function submitForm() {
  saving.value = true
  try {
    const payload = {
      name: form.name,
      description: form.description || null,
      price: Number(form.price),
      duration_min: Number(form.duration_min),
    }
    if (editingId.value) {
      await servicesApi.update(editingId.value, { ...payload, is_active: form.is_active })
      toast.success('Услуга обновлена')
    } else {
      await servicesApi.create(payload)
      toast.success('Услуга создана')
    }
    formOpen.value = false
    load()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось сохранить услугу'))
  } finally {
    saving.value = false
  }
}

// ── Удаление ───────────────────────────────────────────────────────
const serviceToDelete = ref(null)
const deleting = ref(false)

async function deleteService() {
  deleting.value = true
  try {
    await adminApi.deleteService(serviceToDelete.value.id)
    services.value = services.value.filter((s) => s.id !== serviceToDelete.value.id)
    toast.success('Услуга скрыта из каталога')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  } finally {
    deleting.value = false
    serviceToDelete.value = null
  }
}

useDebouncedWatch(search, () => { page.value = 1; load() })
useDebouncedWatch(isActive, () => { page.value = 1; load() }, 0)
useDebouncedWatch(page, load, 0)
onMounted(load)
</script>
