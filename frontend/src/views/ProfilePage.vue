<template>
  <div class="mx-auto max-w-3xl px-4 py-10 sm:px-6">
    <BaseCard class="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
      <div class="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-full bg-brand-900 font-display text-xl font-bold text-white">
        {{ initials }}
      </div>
      <div class="flex-1">
        <p class="text-xs font-medium uppercase tracking-wide text-brand-700">Личный кабинет</p>
        <h1 class="font-display text-2xl font-bold text-ink-900">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</h1>
        <p class="text-sm text-ink-600">{{ auth.user?.email }}</p>
      </div>
      <BaseButton variant="ghost" size="sm" @click="editOpen = !editOpen">
        {{ editOpen ? 'Закрыть' : 'Редактировать' }}
      </BaseButton>
    </BaseCard>

    <BaseCard v-if="editOpen" class="mt-4">
      <form class="grid gap-4 sm:grid-cols-2" novalidate @submit.prevent="saveProfile">
        <BaseInput v-model="editData.first_name" label="Имя" required />
        <BaseInput v-model="editData.last_name" label="Фамилия" required />
        <BaseInput v-model="editData.phone" label="Телефон" class="sm:col-span-2" placeholder="+7 999 000 00 00" />
        <BaseButton type="submit" class="sm:col-span-2" :loading="editLoading">Сохранить</BaseButton>
      </form>
    </BaseCard>

    <section class="mt-10">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 class="font-display text-xl font-bold text-ink-900">Мои записи</h2>
        <BaseSelect v-model="statusFilter" class="w-48">
          <option value="">Все статусы</option>
          <option value="pending">Ожидают</option>
          <option value="confirmed">Подтверждены</option>
          <option value="done">Завершены</option>
          <option value="cancelled">Отменены</option>
        </BaseSelect>
      </div>

      <div v-if="loading" class="space-y-3">
        <Skeleton v-for="i in 3" :key="i" height="h-24" />
      </div>

      <EmptyState
        v-else-if="appointments.length === 0"
        :icon="CalendarIcon"
        title="У вас пока нет записей"
        description="Выберите мастера и запишитесь онлайн"
      >
        <router-link to="/"><BaseButton class="mt-2" size="sm">Записаться</BaseButton></router-link>
      </EmptyState>

      <div v-else class="space-y-3">
        <AppointmentCard
          v-for="apt in appointments"
          :key="apt.id"
          :appointment="apt"
          :primary-label="apt.master_name"
          :secondary-label="apt.service_name"
        >
          <template #actions>
            <BaseButton
              v-if="apt.status === 'pending' || apt.status === 'confirmed'"
              variant="ghost"
              size="sm"
              :loading="cancelling === apt.id"
              @click="cancel(apt.id)"
            >Отменить</BaseButton>
            <BaseButton
              v-else-if="apt.status === 'done' && !apt.review_id"
              variant="ghost"
              size="sm"
              @click="openReview(apt)"
            >Оставить отзыв</BaseButton>
            <span v-else-if="apt.status === 'done' && apt.review_id" class="flex items-center gap-1 text-sm text-success">
              <CheckCircleIcon class="h-4 w-4" aria-hidden="true" /> Отзыв оставлен
            </span>
          </template>
        </AppointmentCard>
      </div>

      <Pagination v-model:page="page" :total-pages="totalPages" />
    </section>

    <Teleport to="body">
      <div v-if="reviewTarget" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" @click="reviewTarget = null" />
        <BaseCard class="relative w-full max-w-md">
          <h2 class="text-lg font-semibold text-ink-900">Оставить отзыв</h2>
          <p class="mt-1 text-sm text-ink-600">{{ reviewTarget.master_name }} · {{ reviewTarget.service_name }}</p>
          <div class="mt-4">
            <StarRatingInput v-model="reviewForm.rating" />
          </div>
          <BaseInput
            v-model="reviewForm.comment"
            class="mt-4"
            as="textarea"
            label="Комментарий"
            hint="Необязательно"
          />
          <div class="mt-6 flex justify-end gap-3">
            <BaseButton variant="ghost" size="sm" @click="reviewTarget = null">Отмена</BaseButton>
            <BaseButton size="sm" :loading="reviewLoading" :disabled="!reviewForm.rating" @click="submitReview">
              Отправить
            </BaseButton>
          </div>
        </BaseCard>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { CalendarIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { appointmentsApi, reviewsApi } from '../api'
import { extractErrorMessage } from '../utils/errors'
import { useDebouncedWatch } from '../composables/useDebouncedWatch'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseSelect from '../components/ui/BaseSelect.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import Skeleton from '../components/ui/Skeleton.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import Pagination from '../components/ui/Pagination.vue'
import AppointmentCard from '../components/AppointmentCard.vue'
import StarRatingInput from '../components/ui/StarRatingInput.vue'

const auth = useAuthStore()
const toast = useToastStore()

const initials = computed(() => {
  if (!auth.user) return '?'
  return `${auth.user.first_name[0]}${auth.user.last_name[0]}`.toUpperCase()
})

// ── Редактирование профиля ────────────────────────────────────────
const editOpen = ref(false)
const editLoading = ref(false)
const editData = reactive({
  first_name: auth.user?.first_name || '',
  last_name: auth.user?.last_name || '',
  phone: auth.user?.phone || '',
})

async function saveProfile() {
  editLoading.value = true
  try {
    await auth.updateMe(editData)
    toast.success('Профиль обновлён')
    editOpen.value = false
  } catch (err) {
    toast.error(extractErrorMessage(err))
  } finally {
    editLoading.value = false
  }
}

// ── Список записей ────────────────────────────────────────────────
const appointments = ref([])
const loading = ref(true)
const cancelling = ref(null)
const page = ref(1)
const totalPages = ref(1)
const statusFilter = ref('')

async function loadAppointments() {
  loading.value = true
  try {
    const { data } = await appointmentsApi.listMy({
      page: page.value, page_size: 10,
      status_filter: statusFilter.value || undefined,
    })
    appointments.value = data.items
    totalPages.value = data.total_pages
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить записи'))
  } finally {
    loading.value = false
  }
}

async function cancel(id) {
  cancelling.value = id
  try {
    await appointmentsApi.cancel(id)
    const apt = appointments.value.find((a) => a.id === id)
    if (apt) apt.status = 'cancelled'
    toast.success('Запись отменена')
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось отменить запись'))
  } finally {
    cancelling.value = null
  }
}

useDebouncedWatch(statusFilter, () => { page.value = 1; loadAppointments() }, 0)
useDebouncedWatch(page, loadAppointments, 0)
onMounted(loadAppointments)

// ── Отзыв ──────────────────────────────────────────────────────────
const reviewTarget = ref(null)
const reviewForm = reactive({ rating: 0, comment: '' })
const reviewLoading = ref(false)

function openReview(apt) {
  reviewTarget.value = apt
  reviewForm.rating = 0
  reviewForm.comment = ''
}

async function submitReview() {
  reviewLoading.value = true
  try {
    const { data } = await reviewsApi.create({
      appointment_id: reviewTarget.value.id,
      rating: reviewForm.rating,
      comment: reviewForm.comment || null,
    })
    const apt = appointments.value.find((a) => a.id === reviewTarget.value.id)
    if (apt) apt.review_id = data.id
    toast.success('Спасибо за отзыв!')
    reviewTarget.value = null
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось отправить отзыв'))
  } finally {
    reviewLoading.value = false
  }
}
</script>
