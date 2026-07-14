<template>
  <div class="mx-auto max-w-3xl px-4 py-10 sm:px-6">
    <div v-if="loading" class="space-y-4">
      <Skeleton height="h-44" />
      <Skeleton height="h-32" />
    </div>

    <template v-else-if="master">
      <BaseCard class="flex flex-col gap-6 sm:flex-row">
        <div class="mx-auto h-40 w-32 flex-shrink-0 overflow-hidden rounded-lg bg-stone-200 sm:mx-0">
          <img v-if="master.photo_url" :src="master.photo_url" :alt="fullName" class="h-full w-full object-cover" />
          <div v-else class="flex h-full w-full items-center justify-center">
            <UserIcon class="h-12 w-12 text-brand-900/20" aria-hidden="true" />
          </div>
        </div>
        <div class="text-center sm:text-left">
          <p class="font-mono text-[11px] font-medium uppercase tracking-wide text-brand-700">{{ master.specialization || 'Барбер' }}</p>
          <h1 class="mt-1 font-display text-3xl font-bold text-ink-900">{{ fullName }}</h1>
          <p v-if="reviewsTotal" class="mt-1 flex items-center justify-center gap-1 text-sm text-ink-600 sm:justify-start">
            <StarIcon class="h-4 w-4 text-accent-400" aria-hidden="true" />
            {{ avgRating }} · {{ reviewsTotal }} {{ reviewsTotal === 1 ? 'отзыв' : 'отзывов' }}
          </p>
          <p class="mt-3 text-sm text-ink-600">Выберите услугу, дату и удобное время</p>
        </div>
      </BaseCard>

      <!-- Шаг 1: услуга -->
      <section class="mt-8">
        <StepTitle n="1" title="Услуга" />
        <EmptyState v-if="masterServices.length === 0" title="У мастера пока нет услуг" />
        <div v-else class="space-y-2">
          <button
            v-for="ms in masterServices"
            :key="ms.service.id"
            class="flex w-full cursor-pointer items-start justify-between gap-3 rounded-lg border px-4 py-3 text-left transition-colors duration-200"
            :class="selectedService?.service.id === ms.service.id
              ? 'border-brand-900 bg-accent-100/60'
              : 'border-stone-200 bg-white hover:border-brand-900/50'"
            @click="selectService(ms)"
          >
            <span>
              <span class="block font-medium text-ink-900">{{ ms.service.name }}</span>
              <span v-if="ms.service.description" class="mt-0.5 block text-sm text-ink-600">{{ ms.service.description }}</span>
            </span>
            <span class="whitespace-nowrap font-mono text-sm text-brand-700">{{ ms.service.duration_min }} мин · {{ ms.final_price }} ₽</span>
          </button>
        </div>
      </section>

      <!-- Шаг 2: дата -->
      <section v-if="selectedService" class="mt-8">
        <StepTitle n="2" title="Дата" />
        <div class="flex flex-wrap gap-2">
          <button
            v-for="d in availableDates"
            :key="d.iso"
            class="flex w-20 flex-shrink-0 cursor-pointer flex-col items-center rounded-lg border px-3 py-2 transition-colors duration-200"
            :class="selectedDate === d.iso ? 'border-brand-900 bg-accent-100/60' : 'border-stone-200 bg-white hover:border-brand-900/50'"
            @click="selectDate(d.iso)"
          >
            <span class="font-mono text-xs uppercase tracking-wide text-brand-700">{{ d.day }}</span>
            <span class="mt-0.5 text-sm text-ink-900">{{ d.label }}</span>
          </button>
        </div>
      </section>

      <!-- Шаг 3: время -->
      <section v-if="selectedDate" class="mt-8">
        <StepTitle n="3" title="Время" />
        <div v-if="slotsLoading" class="flex flex-wrap gap-2">
          <Skeleton v-for="i in 6" :key="i" width="w-20" height="h-10" />
        </div>
        <EmptyState v-else-if="slots.length === 0" title="В этот день нет свободного времени" description="Выберите другую дату" />
        <div v-else class="flex flex-wrap gap-2">
          <button
            v-for="slot in slots"
            :key="slot.start_time"
            class="cursor-pointer rounded-lg border px-4 py-2 font-mono text-sm transition-colors duration-200"
            :class="selectedSlot?.start_time === slot.start_time
              ? 'border-brand-900 bg-brand-900 text-white'
              : 'border-stone-200 bg-white text-ink-900 hover:border-brand-900/50'"
            @click="selectSlot(slot)"
          >
            {{ formatTime(slot.start_time) }}
          </button>
        </div>
      </section>

      <!-- Шаг 4: подтверждение -->
      <section v-if="selectedSlot && !booked" class="mt-8">
        <StepTitle n="4" title="Подтверждение" />

        <BaseCard v-if="!auth.isLoggedIn" class="text-center">
          <p class="text-ink-600">Чтобы записаться, войдите в аккаунт</p>
          <router-link :to="{ path: '/login', query: { redirect: route.fullPath } }">
            <BaseButton class="mt-4">Войти</BaseButton>
          </router-link>
        </BaseCard>

        <BaseCard v-else class="divide-y divide-stone-200">
          <div class="flex justify-between py-3 text-sm"><span class="text-ink-600">Мастер</span><span class="text-ink-900">{{ fullName }}</span></div>
          <div class="flex justify-between py-3 text-sm"><span class="text-ink-600">Услуга</span><span class="text-ink-900">{{ selectedService.service.name }}</span></div>
          <div class="flex justify-between py-3 text-sm">
            <span class="text-ink-600">Дата и время</span>
            <span class="text-ink-900">{{ formatDate(selectedSlot.start_time) }}, {{ formatTime(selectedSlot.start_time) }}</span>
          </div>
          <div class="flex justify-between py-3 text-base font-semibold"><span class="text-ink-900">Итого</span><span class="font-mono text-ink-900">{{ selectedService.final_price }} ₽</span></div>
          <div v-if="!auth.user?.email" class="py-3">
            <BaseInput
              v-model="emailInput"
              type="email"
              label="Email"
              required
              placeholder="you@example.com"
              hint="Нужен для подтверждения записи и напоминаний"
            />
          </div>
          <BaseButton variant="accent" class="mt-4 w-full" :loading="bookingLoading" @click="book">Записаться</BaseButton>
        </BaseCard>
      </section>

      <BaseCard v-if="booked" class="mt-8 text-center">
        <CheckCircleIcon class="mx-auto h-12 w-12 text-success" aria-hidden="true" />
        <h2 class="mt-3 font-display text-2xl font-bold uppercase tracking-tight text-ink-900">Запись оформлена</h2>
        <p class="mt-1 text-ink-600">Ждём вас {{ formatDate(selectedSlot.start_time) }} в {{ formatTime(selectedSlot.start_time) }}</p>
        <router-link to="/profile"><BaseButton class="mt-4">Мои записи</BaseButton></router-link>
      </BaseCard>

      <!-- Отзывы -->
      <section class="mt-12">
        <h2 class="font-display text-xl font-bold uppercase tracking-tight text-ink-900">Отзывы</h2>
        <EmptyState v-if="!reviewsLoading && reviews.length === 0" class="mt-4" title="Пока нет отзывов" />
        <div v-else class="mt-4 space-y-3">
          <BaseCard v-for="r in reviews" :key="r.id">
            <div class="flex items-center gap-1">
              <StarIcon v-for="i in 5" :key="i" class="h-4 w-4" :class="i <= r.rating ? 'text-accent-400' : 'text-stone-200'" aria-hidden="true" />
            </div>
            <p v-if="r.comment" class="mt-2 text-sm text-ink-600">{{ r.comment }}</p>
          </BaseCard>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { UserIcon, StarIcon, CheckCircleIcon } from '@heroicons/vue/24/solid'
import { mastersApi, appointmentsApi, reviewsApi } from '../api'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import Skeleton from '../components/ui/Skeleton.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import StepTitle from '../components/ui/StepTitle.vue'

const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const master = ref(null)
const masterServices = ref([])
const loading = ref(true)

const reviews = ref([])
const reviewsTotal = ref(0)
const reviewsLoading = ref(true)
// Средний рейтинг приходит с бэкенда (по всем опубликованным отзывам) —
// среднее по одной загруженной странице выдавало бы неверное число.
const avgRating = computed(() =>
  master.value?.rating != null ? master.value.rating.toFixed(1) : '—'
)

async function loadReviews() {
  reviewsLoading.value = true
  try {
    const { data } = await reviewsApi.listForMaster(route.params.id, { page: 1, page_size: 20 })
    reviews.value = data.items
    reviewsTotal.value = data.total
  } catch {
    // отзывы необязательны для отображения страницы
  } finally {
    reviewsLoading.value = false
  }
}

onMounted(async () => {
  try {
    const [mRes, sRes] = await Promise.all([
      mastersApi.getById(route.params.id),
      mastersApi.getServices(route.params.id),
    ])
    master.value = mRes.data
    masterServices.value = sRes.data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить профиль мастера'))
  } finally {
    loading.value = false
  }
  loadReviews()
})

const fullName = computed(() => (master.value ? `${master.value.user.first_name} ${master.value.user.last_name}` : ''))

const selectedService = ref(null)
function selectService(ms) {
  selectedService.value = ms
  selectedDate.value = null
  selectedSlot.value = null
  slots.value = []
  booked.value = false
}

const selectedDate = ref(null)
const availableDates = computed(() => {
  const days = []
  const labels = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
  const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
  // Конвенция: расписание салона живёт в UTC («настенные часы» салона),
  // поэтому и список дат, и подписи к ним строятся по UTC-календарю —
  // иначе iso (UTC) и подпись (локальная) расходились бы на день.
  for (let i = 0; i < 14; i++) {
    const d = new Date()
    d.setUTCDate(d.getUTCDate() + i)
    days.push({
      iso: d.toISOString().slice(0, 10),
      day: labels[d.getUTCDay()],
      label: `${d.getUTCDate()} ${months[d.getUTCMonth()]}`,
    })
  }
  return days
})

const slots = ref([])
const slotsLoading = ref(false)

async function selectDate(iso) {
  selectedDate.value = iso
  selectedSlot.value = null
  booked.value = false
  slotsLoading.value = true
  try {
    const { data } = await mastersApi.getSlots(route.params.id, selectedService.value.service.id, iso)
    slots.value = data.slots
  } catch (err) {
    slots.value = []
    toast.error(extractErrorMessage(err, 'Не удалось загрузить свободное время'))
  } finally {
    slotsLoading.value = false
  }
}

const selectedSlot = ref(null)
const bookingLoading = ref(false)
const booked = ref(false)
// Только для клиентов, зарегистрированных через VK без email (VK ID не
// всегда его отдаёт) — просим указать его здесь, перед первой записью.
const emailInput = ref('')

function selectSlot(slot) {
  selectedSlot.value = slot
  booked.value = false
}

async function book() {
  if (!auth.user?.email && !emailInput.value) {
    toast.error('Укажите email, чтобы оформить запись')
    return
  }
  bookingLoading.value = true
  try {
    const emailJustAdded = !auth.user?.email
    if (emailJustAdded) {
      await auth.updateMe({ email: emailInput.value })
    }
    await appointmentsApi.create({
      master_id: route.params.id,
      service_id: selectedService.value.service.id,
      start_time: selectedSlot.value.start_time,
    })
    booked.value = true
    toast.success(
      emailJustAdded
        ? 'Запись успешно создана. Мы отправили ссылку для подтверждения email'
        : 'Запись успешно создана'
    )
  } catch (err) {
    toast.error(extractErrorMessage(err))
  } finally {
    bookingLoading.value = false
  }
}

// timeZone: 'UTC' — слоты и записи показываем как «настенные часы» салона,
// а не в таймзоне браузера (иначе расписание 09:00–20:00 в Москве
// отображалось бы как 12:00–23:00).
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })
}
function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long', timeZone: 'UTC' })
}
</script>
