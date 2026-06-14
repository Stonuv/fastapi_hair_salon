<template>
  <div class="page">

    <div v-if="!auth.isLoggedIn || auth.user?.role !== 'master'" class="empty">
      <p>Эта страница только для мастеров</p>
    </div>

    <template v-else>
      <section class="profile">
        <div class="profile__avatar">✂</div>
        <div class="profile__info">
          <p class="profile__eyebrow">Кабинет мастера</p>
          <h1 class="profile__name">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</h1>
        </div>
      </section>

      <div class="scissors-divider">✂</div>

      <!-- Расписание -->
      <section class="section">
        <h2 class="section-title">Расписание</h2>

        <div v-if="scheduleLoading" class="empty">Загружаем…</div>

        <div v-else class="schedule">
          <div
            v-for="day in weekDays"
            :key="day.index"
            class="schedule__row"
          >
            <span class="schedule__day">{{ day.label }}</span>
            <template v-if="getSchedule(day.index)">
              <span class="schedule__time">
                {{ getSchedule(day.index).start_time.slice(0,5) }} —
                {{ getSchedule(day.index).end_time.slice(0,5) }}
              </span>
              <span
                class="schedule__badge"
                :class="getSchedule(day.index).is_working ? 'schedule__badge--on' : 'schedule__badge--off'"
              >
                {{ getSchedule(day.index).is_working ? 'Рабочий' : 'Выходной' }}
              </span>
            </template>
            <span v-else class="schedule__empty">— не задано</span>
          </div>
        </div>
      </section>

      <div class="scissors-divider">✂</div>

      <!-- Записи на сегодня -->
      <section class="section">
        <h2 class="section-title">Записи на сегодня</h2>

        <div v-if="aptsLoading" class="empty">Загружаем…</div>

        <div v-else-if="todayApts.length === 0" class="empty">
          <p>На сегодня записей нет</p>
        </div>

        <div v-else class="list">
          <div
            v-for="apt in todayApts"
            :key="apt.id"
            class="apt-card"
            :class="`apt-card--${apt.status}`"
          >
            <div class="apt-card__left">
              <span class="apt-card__status">{{ statusLabel(apt.status) }}</span>
              <p class="apt-card__time">
                {{ formatTime(apt.start_time) }} — {{ formatTime(apt.end_time) }}
              </p>
            </div>
            <div class="apt-card__right">
              <p class="apt-card__price">{{ apt.final_price }} ₽</p>
            </div>
          </div>
        </div>
      </section>
    </template>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { mastersApi, appointmentsApi } from '../api'

const auth = useAuthStore()

// ── Расписание ───────────────────────────────────────────────────
const schedule        = ref([])
const scheduleLoading = ref(true)
const masterId        = ref(null)

const weekDays = [
  { index: 0, label: 'Пн' }, { index: 1, label: 'Вт' },
  { index: 2, label: 'Ср' }, { index: 3, label: 'Чт' },
  { index: 4, label: 'Пт' }, { index: 5, label: 'Сб' },
  { index: 6, label: 'Вс' },
]

function getSchedule(dayIndex) {
  return schedule.value.find(s => s.day_of_week === dayIndex)
}

// ── Записи ───────────────────────────────────────────────────────
const todayApts = ref([])
const aptsLoading = ref(true)

onMounted(async () => {
  if (!auth.isLoggedIn) return

  try {
    // Получаем профиль мастера через /masters?user_id
    const mastersRes = await mastersApi.getAll()
    const me = mastersRes.data.masters.find(
      m => m.first_name === auth.user?.first_name &&
           m.last_name  === auth.user?.last_name
    )
    if (!me) return
    masterId.value = me.id

    // Расписание
    const schedRes = await mastersApi.getSchedule(me.id)
    schedule.value = schedRes.data
  } finally {
    scheduleLoading.value = false
  }

  // Записи на сегодня
  try {
    const today = new Date()
    const from  = new Date(today.setHours(0, 0, 0, 0)).toISOString()
    const to    = new Date(today.setHours(23, 59, 59, 999)).toISOString()
    const res   = await appointmentsApi.getMasterToday(masterId.value, from, to)
    todayApts.value = res.data.appointments
  } finally {
    aptsLoading.value = false
  }
})

const statusMap = {
  pending: 'Ожидает', confirmed: 'Подтверждена',
  cancelled: 'Отменена', done: 'Завершена',
}
function statusLabel(s) { return statusMap[s] || s }
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.page {
  max-width: 760px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem 5rem;
}
.profile {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}
.profile__avatar {
  width: 72px; height: 72px;
  border-radius: 50%;
  background: var(--c-espresso);
  color: var(--c-cream);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; flex-shrink: 0;
}
.profile__eyebrow {
  font-size: 0.75rem; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--c-caramel); margin: 0 0 0.3rem;
}
.profile__name {
  font-family: var(--f-display); font-size: 1.8rem;
  font-weight: 400; color: var(--c-espresso); margin: 0;
}
.scissors-divider {
  text-align: center; font-size: 0.9rem;
  color: var(--c-latte); position: relative; margin: 0 0 2.5rem;
}
.scissors-divider::before, .scissors-divider::after {
  content: ''; position: absolute; top: 50%;
  width: calc(50% - 1.5rem); height: 1px; background: var(--c-latte);
}
.scissors-divider::before { left: 0; }
.scissors-divider::after  { right: 0; }

.section { margin-bottom: 2.5rem; }
.section-title {
  font-family: var(--f-display); font-size: 1.4rem;
  font-weight: 400; color: var(--c-espresso); margin: 0 0 1.25rem;
}

/* Schedule */
.schedule { display: flex; flex-direction: column; gap: 0.5rem; }
.schedule__row {
  display: flex; align-items: center; gap: 1rem;
  padding: 0.7rem 1rem;
  background: var(--c-cream);
  border: 1px solid var(--c-latte); border-radius: 6px;
}
.schedule__day {
  width: 2rem; font-size: 0.8rem; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--c-caramel); font-weight: 500;
}
.schedule__time { font-size: 0.9rem; color: var(--c-espresso); flex: 1; }
.schedule__empty { font-size: 0.85rem; color: #bbb; flex: 1; }
.schedule__badge {
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em;
  padding: 0.2rem 0.6rem; border-radius: 20px;
}
.schedule__badge--on  { background: #e8f2eb; color: var(--c-matcha); }
.schedule__badge--off { background: #f5f0eb; color: #aaa; }

/* Appointments */
.list { display: flex; flex-direction: column; gap: 0.75rem; }
.apt-card {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem 1.25rem;
  background: var(--c-cream);
  border: 1px solid var(--c-latte); border-radius: 8px;
  border-left: 4px solid var(--c-latte);
}
.apt-card--pending   { border-left-color: var(--c-caramel); }
.apt-card--confirmed { border-left-color: var(--c-matcha); }
.apt-card--cancelled { border-left-color: #ccc; opacity: 0.6; }
.apt-card--done      { border-left-color: var(--c-espresso); }
.apt-card__status {
  font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: 0.1em; color: var(--c-caramel); display: block; margin-bottom: 0.2rem;
}
.apt-card__time  { font-size: 0.95rem; color: var(--c-espresso); margin: 0; }
.apt-card__price { font-size: 1rem; font-weight: 600; color: var(--c-caramel); margin: 0; }

.empty { text-align: center; padding: 2rem 0; color: #8a7060; }
</style>
