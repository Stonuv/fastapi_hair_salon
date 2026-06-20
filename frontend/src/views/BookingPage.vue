<template>
  <div class="page">
    <div v-if="loading" class="state">Загружаем профиль мастера…</div>

    <template v-else-if="master">
      <!-- Профиль -->
      <section class="profile">
        <div class="profile__photo">
          <img v-if="master.photo_url" :src="master.photo_url" :alt="fullName" />
          <div v-else class="profile__photo-placeholder">✂</div>
        </div>
        <div class="profile__info">
          <p class="profile__eyebrow">{{ master.specialization || 'Мастер' }}</p>
          <h1 class="profile__name">{{ fullName }}</h1>
          <div class="scissors-divider">✂</div>

          <!-- Услуги мастера — краткий список -->
          <div class="profile__services" v-if="masterServices.length">
            <span v-for="ms in masterServices" :key="ms.service.id" class="service-tag">
              {{ ms.service.name }} · {{ ms.final_price }} ₽
            </span>
          </div>

          <p class="profile__hint">Выберите услугу, дату и удобное время</p>
        </div>
      </section>

      <!-- Шаг 1: Услуга -->
      <section class="step">
        <h2 class="step__title"><span class="step__num">01</span> Услуга</h2>
        <div v-if="masterServices.length === 0" class="state">
          У мастера пока нет услуг
        </div>
        <div v-else class="services">
          <button
            v-for="ms in masterServices" :key="ms.service.id"
            class="service-btn"
            :class="{ 'service-btn--active': selectedService?.service.id === ms.service.id }"
            @click="selectService(ms)"
          >
            <span class="service-btn__name">{{ ms.service.name }}</span>
            <span class="service-btn__meta">
              {{ ms.service.duration_min }} мин · {{ ms.final_price }} ₽
            </span>
          </button>
        </div>
      </section>

      <!-- Шаг 2: Дата -->
      <section class="step" v-if="selectedService">
        <h2 class="step__title"><span class="step__num">02</span> Дата</h2>
        <div class="dates">
          <button
            v-for="d in availableDates" :key="d.iso"
            class="date-btn"
            :class="{ 'date-btn--active': selectedDate === d.iso }"
            @click="selectDate(d.iso)"
          >
            <span class="date-btn__day">{{ d.day }}</span>
            <span class="date-btn__label">{{ d.label }}</span>
          </button>
        </div>
      </section>

      <!-- Шаг 3: Время -->
      <section class="step" v-if="selectedDate">
        <h2 class="step__title"><span class="step__num">03</span> Время</h2>
        <div v-if="slotsLoading" class="state">Загружаем слоты…</div>
        <div v-else-if="slots.length === 0" class="state">
          В этот день нет свободного времени. Выберите другую дату.
        </div>
        <div v-else class="slots">
          <button
            v-for="slot in slots" :key="slot.start_time"
            class="slot-btn"
            :class="{ 'slot-btn--active': selectedSlot?.start_time === slot.start_time }"
            @click="selectedSlot = slot"
          >
            {{ formatTime(slot.start_time) }}
          </button>
        </div>
      </section>

      <!-- Шаг 4: Подтверждение -->
      <section class="step" v-if="selectedSlot">
        <h2 class="step__title"><span class="step__num">04</span> Подтверждение</h2>

        <div v-if="!auth.isLoggedIn" class="auth-prompt">
          <p>Чтобы записаться, войдите в аккаунт</p>
          <router-link to="/login" class="btn">Войти</router-link>
        </div>

        <div v-else class="summary">
          <div class="summary__row">
            <span>Мастер</span><span>{{ fullName }}</span>
          </div>
          <div class="summary__row">
            <span>Услуга</span><span>{{ selectedService.service.name }}</span>
          </div>
          <div class="summary__row">
            <span>Дата и время</span>
            <span>{{ formatDate(selectedSlot.start_time) }}, {{ formatTime(selectedSlot.start_time) }}</span>
          </div>
          <div class="summary__row summary__row--total">
            <span>Итого</span><span>{{ selectedService.final_price }} ₽</span>
          </div>
          <p v-if="bookingError" class="error">{{ bookingError }}</p>
          <button class="btn btn--full" :disabled="bookingLoading" @click="book">
            {{ bookingLoading ? 'Записываем…' : 'Записаться' }}
          </button>
        </div>
      </section>

      <!-- Успех -->
      <div v-if="booked" class="success">
        <p class="success__icon">✓</p>
        <h2 class="success__title">Запись оформлена</h2>
        <p class="success__sub">
          Ждём вас {{ formatDate(selectedSlot.start_time) }}
          в {{ formatTime(selectedSlot.start_time) }}
        </p>
        <router-link to="/profile" class="btn">Мои записи</router-link>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { mastersApi, appointmentsApi } from '../api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth  = useAuthStore()

const master         = ref(null)
const masterServices = ref([])
const loading        = ref(true)

onMounted(async () => {
  try {
    const [mRes, sRes] = await Promise.all([
      mastersApi.getById(route.params.id),
      mastersApi.getServices(route.params.id),
    ])
    master.value         = mRes.data
    masterServices.value = sRes.data
  } finally {
    loading.value = false
  }
})

const fullName = computed(() =>
  master.value
    ? `${master.value.user.first_name} ${master.value.user.last_name}`
    : ''
)

const selectedService = ref(null)
function selectService(ms) {
  selectedService.value = ms
  selectedDate.value    = null
  selectedSlot.value    = null
  slots.value           = []
}

const selectedDate    = ref(null)
const availableDates  = computed(() => {
  const days   = []
  const labels = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб']
  const months = ['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек']
  for (let i = 0; i < 14; i++) {
    const d = new Date()
    d.setDate(d.getDate() + i)
    days.push({
      iso:   d.toISOString().slice(0, 10),
      day:   labels[d.getDay()],
      label: `${d.getDate()} ${months[d.getMonth()]}`,
    })
  }
  return days
})

const slots        = ref([])
const slotsLoading = ref(false)

async function selectDate(iso) {
  selectedDate.value = iso
  selectedSlot.value = null
  slotsLoading.value = true
  try {
    const res = await mastersApi.getSlots(route.params.id, {
      service_id:  selectedService.value.service.id,
      target_date: iso,
    })
    slots.value = res.data.slots
  } catch {
    slots.value = []
  } finally {
    slotsLoading.value = false
  }
}

const selectedSlot   = ref(null)
const bookingLoading = ref(false)
const bookingError   = ref('')
const booked         = ref(false)

async function book() {
  bookingLoading.value = true
  bookingError.value   = ''
  try {
    await appointmentsApi.create({
      master_id:  route.params.id,
      service_id: selectedService.value.service.id,
      start_time: selectedSlot.value.start_time,
    })
    booked.value = true
  } catch (e) {
    bookingError.value = e.response?.data?.detail || 'Произошла ошибка. Попробуйте ещё раз.'
  } finally {
    bookingLoading.value = false
  }
}

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
}
function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long' })
}
</script>

<style scoped>
.page { max-width: 760px; margin: 0 auto; padding: 2.5rem 1.5rem 5rem; }

.profile {
  display: flex; gap: 2rem; align-items: flex-start; margin-bottom: 3rem;
}
.profile__photo {
  flex-shrink: 0; width: 140px; height: 180px; border-radius: 6px;
  overflow: hidden; background: var(--c-latte);
  display: flex; align-items: center; justify-content: center;
}
.profile__photo img { width: 100%; height: 100%; object-fit: cover; }
.profile__photo-placeholder { font-size: 2.5rem; opacity: 0.3; color: var(--c-espresso); }
.profile__info { flex: 1; padding-top: 0.5rem; }
.profile__eyebrow {
  font-size: 0.75rem; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--c-caramel); margin: 0 0 0.4rem;
}
.profile__name {
  font-family: var(--f-display); font-size: 2.2rem;
  font-weight: 400; color: var(--c-espresso); margin: 0;
}
.profile__hint { color: #8a7060; font-size: 0.95rem; margin: 0; }
.profile__services { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.75rem; }
.service-tag {
  font-size: 0.75rem; padding: 0.25rem 0.6rem;
  background: #ede7de; border-radius: 20px; color: var(--c-espresso);
}

.scissors-divider {
  text-align: center; font-size: 0.9rem; color: var(--c-latte);
  position: relative; margin: 1rem 0;
}
.scissors-divider::before, .scissors-divider::after {
  content: ''; position: absolute; top: 50%;
  width: calc(50% - 1.5rem); height: 1px; background: var(--c-latte);
}
.scissors-divider::before { left: 0; }
.scissors-divider::after  { right: 0; }

.step { margin-bottom: 2.5rem; }
.step__title {
  display: flex; align-items: center; gap: 0.75rem;
  font-family: var(--f-display); font-size: 1.3rem;
  font-weight: 400; color: var(--c-espresso); margin: 0 0 1.25rem;
}
.step__num {
  font-size: 0.7rem; letter-spacing: 0.1em;
  color: var(--c-caramel); font-family: var(--f-body); font-weight: 500;
}

.services { display: flex; flex-direction: column; gap: 0.6rem; }
.service-btn {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.9rem 1.1rem; background: var(--c-cream);
  border: 1px solid var(--c-latte); border-radius: 6px;
  cursor: pointer; transition: border-color 0.2s; text-align: left;
}
.service-btn:hover         { border-color: var(--c-matcha); }
.service-btn--active       { border-color: var(--c-matcha); background: #f0f5f1; }
.service-btn__name         { font-size: 0.95rem; color: var(--c-espresso); }
.service-btn__meta         { font-size: 0.85rem; color: var(--c-caramel); white-space: nowrap; margin-left: 1rem; }

.dates { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.date-btn {
  display: flex; flex-direction: column; align-items: center;
  padding: 0.6rem 0.9rem; background: var(--c-cream);
  border: 1px solid var(--c-latte); border-radius: 6px;
  cursor: pointer; min-width: 60px; transition: border-color 0.2s;
}
.date-btn:hover      { border-color: var(--c-matcha); }
.date-btn--active    { border-color: var(--c-matcha); background: #f0f5f1; }
.date-btn__day       { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--c-caramel); }
.date-btn__label     { font-size: 0.85rem; color: var(--c-espresso); margin-top: 0.2rem; }

.slots { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.slot-btn {
  padding: 0.5rem 1rem; background: var(--c-cream);
  border: 1px solid var(--c-latte); border-radius: 4px;
  cursor: pointer; font-size: 0.9rem; color: var(--c-espresso);
  transition: border-color 0.2s;
}
.slot-btn:hover    { border-color: var(--c-matcha); }
.slot-btn--active  { background: var(--c-matcha); border-color: var(--c-matcha); color: #fff; }

.summary {
  background: var(--c-cream); border: 1px solid var(--c-latte);
  border-radius: 8px; padding: 1.5rem;
}
.summary__row {
  display: flex; justify-content: space-between;
  padding: 0.6rem 0; border-bottom: 1px solid var(--c-latte);
  font-size: 0.95rem; color: var(--c-espresso);
}
.summary__row span:first-child { color: #8a7060; }
.summary__row--total {
  border-bottom: none; font-weight: 600;
  font-size: 1.05rem; padding-top: 0.9rem;
}
.summary__row--total span:last-child { color: var(--c-caramel); }

.auth-prompt {
  text-align: center; padding: 2rem;
  background: var(--c-cream); border: 1px solid var(--c-latte); border-radius: 8px;
}
.auth-prompt p { color: #8a7060; margin: 0 0 1rem; }

.btn {
  display: inline-block; margin-top: 1.25rem;
  padding: 0.75rem 2rem; background: var(--c-matcha); color: #fff;
  border: none; border-radius: 5px; font-size: 0.95rem;
  cursor: pointer; text-decoration: none; transition: opacity 0.2s;
}
.btn:hover    { opacity: 0.85; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn--full    { width: 100%; text-align: center; }

.success {
  text-align: center; padding: 4rem 2rem;
  background: var(--c-cream); border: 1px solid var(--c-latte);
  border-radius: 8px; margin-top: 2rem;
}
.success__icon  { font-size: 2.5rem; color: var(--c-matcha); margin: 0 0 0.75rem; }
.success__title { font-family: var(--f-display); font-size: 1.8rem; font-weight: 400; color: var(--c-espresso); margin: 0 0 0.5rem; }
.success__sub   { color: #8a7060; margin: 0 0 1.5rem; }
.error          { color: #b05050; font-size: 0.9rem; margin: 0.75rem 0 0; }
.state          { text-align: center; padding: 3rem 0; color: #8a7060; }

@media (max-width: 600px) {
  .profile { flex-direction: column; }
  .profile__photo { width: 100%; height: 220px; }
}
</style>
