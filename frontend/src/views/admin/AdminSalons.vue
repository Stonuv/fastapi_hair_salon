<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <p class="text-sm text-ink-600">
        Точки сети. Закрытая точка исчезает с публичного сайта, но её мастера, записи и отчёты сохраняются.
      </p>
      <BaseButton @click="openCreate">Добавить точку</BaseButton>
    </div>

    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 3" :key="i" height="h-24" />
    </div>

    <EmptyState v-else-if="salons.length === 0" :icon="BuildingStorefrontIcon" title="Точек пока нет" />

    <div v-else class="space-y-3">
      <BaseCard v-for="s in salons" :key="s.id" class="flex flex-wrap items-center justify-between gap-4">
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <p class="font-medium text-ink-900">{{ s.name }}</p>
            <span
              class="rounded-full px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide"
              :class="s.is_active ? 'bg-green-100 text-green-800' : 'bg-stone-200 text-ink-600'"
            >
              {{ s.is_active ? 'Открыта' : 'Закрыта' }}
            </span>
          </div>
          <p class="text-sm text-ink-600">{{ s.address }}</p>
          <p class="text-sm text-ink-600">
            {{ s.open_time.slice(0, 5) }}–{{ s.close_time.slice(0, 5) }}<template v-if="s.phone"> · {{ s.phone }}</template>
          </p>
        </div>
        <div class="flex items-center gap-2">
          <BaseButton variant="ghost" size="sm" @click="openEdit(s)">Редактировать</BaseButton>
          <BaseButton
            :variant="s.is_active ? 'danger' : 'ghost'"
            size="sm"
            @click="salonToToggle = s"
          >
            {{ s.is_active ? 'Закрыть' : 'Открыть' }}
          </BaseButton>
        </div>
      </BaseCard>
    </div>

    <Teleport to="body">
      <div v-if="formOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" @click="formOpen = false" />
        <div class="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-stone-200 bg-white p-6 shadow-lg" role="dialog" aria-modal="true">
          <h2 class="font-display text-lg font-bold uppercase tracking-tight text-ink-900">
            {{ editing ? 'Редактировать точку' : 'Новая точка' }}
          </h2>
          <form class="mt-5 space-y-4" novalidate @submit.prevent="save">
            <BaseInput v-model="form.name" label="Название" required :error="errors.name" />
            <BaseInput v-model="form.address" label="Адрес" required :error="errors.address" />
            <BaseInput v-model="form.phone" label="Телефон" hint="Необязательно" :error="errors.phone" />
            <div>
              <p class="mb-1.5 block text-sm font-medium text-ink-900">Время работы</p>
              <div class="flex items-center gap-3">
                <BaseTimeInput v-model="form.open_time" />
                <span class="text-ink-600">—</span>
                <BaseTimeInput v-model="form.close_time" />
              </div>
              <p v-if="errors.hours" class="mt-1 text-sm text-danger">{{ errors.hours }}</p>
            </div>
            <div>
              <p class="mb-1.5 block text-sm font-medium text-ink-900">Фото точки</p>
              <ImageUpload v-model="form.photo_url" />
            </div>
            <div class="flex justify-end gap-2 pt-2">
              <BaseButton variant="ghost" size="sm" type="button" @click="formOpen = false">Отмена</BaseButton>
              <BaseButton size="sm" type="submit" :loading="saving">Сохранить</BaseButton>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <ConfirmDialog
      :open="!!salonToToggle"
      :title="salonToToggle?.is_active ? 'Закрыть точку?' : 'Открыть точку?'"
      :message="salonToToggle?.is_active
        ? `«${salonToToggle?.name}» исчезнет с публичного сайта. Мастера, записи и отчёты сохранятся — точку можно открыть обратно.`
        : `«${salonToToggle?.name}» снова появится на публичном сайте.`"
      @confirm="toggleActive"
      @update:open="salonToToggle = null"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { BuildingStorefrontIcon } from '@heroicons/vue/24/outline'
import { salonsApi } from '../../api'
import { useSalonStore } from '../../stores/salon'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import { useFormErrors } from '../../composables/useFormErrors'
import BaseCard from '../../components/ui/BaseCard.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import BaseTimeInput from '../../components/ui/BaseTimeInput.vue'
import ImageUpload from '../../components/ui/ImageUpload.vue'
import Skeleton from '../../components/ui/Skeleton.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import ConfirmDialog from '../../components/ui/ConfirmDialog.vue'

const salonStore = useSalonStore()
const toast = useToastStore()
const { errors, setError, clearAll, setFromResponse } = useFormErrors()

const salons = ref([])
const loading = ref(true)
const saving = ref(false)
const formOpen = ref(false)
const editing = ref(null)
const salonToToggle = ref(null)

const form = reactive({
  name: '', address: '', phone: '',
  open_time: '09:00', close_time: '20:00', photo_url: null,
})

async function load() {
  loading.value = true
  try {
    // Без is_active — owner видит и закрытые точки (см. routes/salons.py).
    const { data } = await salonsApi.list()
    salons.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить точки'))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  clearAll()
  editing.value = null
  Object.assign(form, {
    name: '', address: '', phone: '',
    open_time: '09:00', close_time: '20:00', photo_url: null,
  })
  formOpen.value = true
}

function openEdit(salon) {
  clearAll()
  editing.value = salon
  Object.assign(form, {
    name: salon.name,
    address: salon.address,
    phone: salon.phone ?? '',
    open_time: salon.open_time.slice(0, 5),
    close_time: salon.close_time.slice(0, 5),
    photo_url: salon.photo_url,
  })
  formOpen.value = true
}

function validate() {
  clearAll()
  if (!form.name.trim()) setError('name', 'Укажите название')
  if (!form.address.trim()) setError('address', 'Укажите адрес')
  // Та же граница, что CHECK ck_salons_close_after_open — ловим до запроса.
  if (form.close_time <= form.open_time) {
    setError('hours', 'Время закрытия должно быть позже времени открытия')
  }
  return !Object.keys(errors).length
}

async function save() {
  if (!validate()) return
  saving.value = true
  const payload = {
    name: form.name,
    address: form.address,
    phone: form.phone || null,
    open_time: `${form.open_time}:00`,
    close_time: `${form.close_time}:00`,
    photo_url: form.photo_url || null,
  }
  try {
    if (editing.value) {
      await salonsApi.update(editing.value.id, payload)
      toast.success('Точка обновлена')
    } else {
      await salonsApi.create(payload)
      toast.success('Точка добавлена')
    }
    formOpen.value = false
    await load()
    // Переключатель точек и футер публичного сайта читают стор — обновляем,
    // иначе они отстанут до перезагрузки страницы.
    await salonStore.refresh()
  } catch (err) {
    if (!setFromResponse(err)) {
      toast.error(extractErrorMessage(err, 'Не удалось сохранить точку'))
    }
  } finally {
    saving.value = false
  }
}

async function toggleActive() {
  const salon = salonToToggle.value
  salonToToggle.value = null
  try {
    // DELETE у точек нет намеренно: masters/appointments ссылаются
    // ondelete=RESTRICT, физическое удаление недостижимо (ROADMAP.md §4.2).
    await salonsApi.update(salon.id, { is_active: !salon.is_active })
    toast.success(salon.is_active ? 'Точка закрыта' : 'Точка открыта')
    await load()
    await salonStore.refresh()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось изменить статус точки'))
  }
}

onMounted(load)
</script>
