<template>
  <div class="page">
    <div v-if="!auth.isLoggedIn" class="empty">
      <p class="empty__text">Войдите чтобы увидеть свои записи</p>
      <router-link to="/login" class="btn">Войти</router-link>
    </div>

    <template v-else>
      <!-- Профиль -->
      <section class="profile">
        <div class="profile__avatar">{{ initials }}</div>
        <div class="profile__info">
          <p class="profile__eyebrow">Личный кабинет</p>
          <h1 class="profile__name">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</h1>
          <p class="profile__email">{{ auth.user?.email }}</p>
          <button class="profile__edit-btn" @click="editOpen = !editOpen">
            {{ editOpen ? 'Закрыть' : 'Редактировать профиль' }}
          </button>
        </div>
      </section>

      <!-- Форма редактирования -->
      <section v-if="editOpen" class="edit-form">
        <div class="form__row">
          <div class="form__field">
            <label class="form__label">Имя</label>
            <input v-model="editData.first_name" class="input" />
          </div>
          <div class="form__field">
            <label class="form__label">Фамилия</label>
            <input v-model="editData.last_name" class="input" />
          </div>
        </div>
        <div class="form__field">
          <label class="form__label">Телефон</label>
          <input v-model="editData.phone" class="input" placeholder="+7 999 000 00 00" />
        </div>
        <div class="form__actions">
          <button class="btn" :disabled="editLoading" @click="saveProfile">
            {{ editLoading ? '…' : 'Сохранить' }}
          </button>
          <p v-if="editMsg" class="msg" :class="editMsg.ok ? 'msg--ok' : 'msg--err'">
            {{ editMsg.text }}
          </p>
        </div>
      </section>

      <div class="scissors-divider">✂</div>

      <!-- Записи -->
      <section class="appointments">
        <h2 class="section-title">Мои записи</h2>

        <div v-if="loading" class="empty">Загружаем записи…</div>

        <div v-else-if="appointments.length === 0" class="empty">
          <p class="empty__text">У вас пока нет записей</p>
          <router-link to="/" class="btn">Записаться</router-link>
        </div>

        <div v-else class="list">
          <div
            v-for="apt in appointments" :key="apt.id"
            class="apt-card" :class="`apt-card--${apt.status}`"
          >
            <div class="apt-card__left">
              <span class="apt-card__status">{{ statusLabel(apt.status) }}</span>
              <p class="apt-card__date">{{ formatDate(apt.start_time) }}</p>
              <p class="apt-card__time">{{ formatTime(apt.start_time) }} — {{ formatTime(apt.end_time) }}</p>
            </div>
            <div class="apt-card__right">
              <p class="apt-card__price">{{ apt.final_price }} ₽</p>
              <button
                v-if="apt.status === 'pending' || apt.status === 'confirmed'"
                class="apt-card__cancel"
                :disabled="cancelling === apt.id"
                @click="cancel(apt.id)"
              >
                {{ cancelling === apt.id ? '…' : 'Отменить' }}
              </button>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { appointmentsApi, userApi } from '../api'

const auth       = useAuthStore()
const loading    = ref(true)
const cancelling = ref(null)
const appointments = ref([])

const initials = computed(() => {
  if (!auth.user) return '?'
  return `${auth.user.first_name[0]}${auth.user.last_name[0]}`.toUpperCase()
})

onMounted(async () => {
  if (!auth.isLoggedIn) return
  try {
    const res = await appointmentsApi.getMy()
    appointments.value = res.data.appointments
  } finally {
    loading.value = false
  }
})

// ── Редактирование ───────────────────────────────────────────────
const editOpen    = ref(false)
const editLoading = ref(false)
const editMsg     = ref(null)
const editData    = reactive({
  first_name: auth.user?.first_name || '',
  last_name:  auth.user?.last_name  || '',
  phone:      auth.user?.phone      || '',
})

async function saveProfile() {
  editLoading.value = true
  editMsg.value     = null
  try {
    const res = await userApi.updateMe(editData)
    auth.user = res.data
    editMsg.value = { ok: true, text: 'Профиль обновлён!' }
  } catch (e) {
    editMsg.value = { ok: false, text: e.response?.data?.detail || 'Ошибка' }
  } finally {
    editLoading.value = false
  }
}

// ── Отмена записи ────────────────────────────────────────────────
async function cancel(id) {
  cancelling.value = id
  try {
    await appointmentsApi.cancel(id)
    const apt = appointments.value.find(a => a.id === id)
    if (apt) apt.status = 'cancelled'
  } catch (e) {
    alert(e.response?.data?.detail || 'Не удалось отменить запись')
  } finally {
    cancelling.value = null
  }
}

const statusMap = {
  pending: 'Ожидает', confirmed: 'Подтверждена',
  cancelled: 'Отменена', done: 'Завершена',
}
function statusLabel(s) { return statusMap[s] || s }
function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })
}
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.page { max-width: 760px; margin: 0 auto; padding: 2.5rem 1.5rem 5rem; }

.profile { display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.5rem; }
.profile__avatar {
  width: 72px; height: 72px; border-radius: 50%;
  background: var(--c-espresso); color: var(--c-cream);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--f-display); font-size: 1.5rem; flex-shrink: 0;
}
.profile__eyebrow {
  font-size: 0.75rem; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--c-caramel); margin: 0 0 0.3rem;
}
.profile__name {
  font-family: var(--f-display); font-size: 1.8rem;
  font-weight: 400; color: var(--c-espresso); margin: 0;
}
.profile__email { font-size: 0.875rem; color: #8a7060; margin: 0.2rem 0 0.5rem; }
.profile__edit-btn {
  background: none; border: 1px solid var(--c-latte); border-radius: 4px;
  padding: 0.3rem 0.8rem; font-size: 0.8rem; color: #8a7060;
  cursor: pointer; transition: border-color 0.2s;
}
.profile__edit-btn:hover { border-color: var(--c-matcha); color: var(--c-matcha); }

/* Edit form */
.edit-form {
  background: var(--c-cream); border: 1px solid var(--c-latte);
  border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem;
  display: flex; flex-direction: column; gap: 0.75rem;
}
.form__row   { display: flex; gap: 0.75rem; }
.form__field { display: flex; flex-direction: column; gap: 0.3rem; flex: 1; }
.form__label { font-size: 0.8rem; color: #8a7060; text-transform: uppercase; letter-spacing: 0.06em; }
.form__actions { display: flex; align-items: center; gap: 1rem; margin-top: 0.25rem; }

.input {
  padding: 0.65rem 0.9rem; border: 1px solid var(--c-latte);
  border-radius: 5px; background: #fff; font-size: 0.9rem;
  color: var(--c-espresso); outline: none; font-family: var(--f-body);
  transition: border-color 0.2s; width: 100%; box-sizing: border-box;
}
.input:focus { border-color: var(--c-matcha); }

.msg { font-size: 0.875rem; margin: 0; }
.msg--ok  { color: var(--c-matcha); }
.msg--err { color: #b05050; }

/* Divider */
.scissors-divider {
  text-align: center; font-size: 0.9rem; color: var(--c-latte);
  position: relative; margin: 0 0 2.5rem;
}
.scissors-divider::before, .scissors-divider::after {
  content: ''; position: absolute; top: 50%;
  width: calc(50% - 1.5rem); height: 1px; background: var(--c-latte);
}
.scissors-divider::before { left: 0; }
.scissors-divider::after  { right: 0; }

.section-title {
  font-family: var(--f-display); font-size: 1.4rem;
  font-weight: 400; color: var(--c-espresso); margin: 0 0 1.25rem;
}
.list { display: flex; flex-direction: column; gap: 0.75rem; }
.apt-card {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1.1rem 1.25rem; background: var(--c-cream);
  border: 1px solid var(--c-latte); border-radius: 8px;
  border-left: 4px solid var(--c-latte);
}
.apt-card--pending   { border-left-color: var(--c-caramel); }
.apt-card--confirmed { border-left-color: var(--c-matcha); }
.apt-card--cancelled { border-left-color: #ccc; opacity: 0.6; }
.apt-card--done      { border-left-color: var(--c-espresso); }
.apt-card__status {
  font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: 0.1em; color: var(--c-caramel); display: block; margin-bottom: 0.3rem;
}
.apt-card--confirmed .apt-card__status { color: var(--c-matcha); }
.apt-card--cancelled .apt-card__status { color: #999; }
.apt-card__date  { font-size: 0.95rem; color: var(--c-espresso); margin: 0; font-weight: 500; }
.apt-card__time  { font-size: 0.85rem; color: #8a7060; margin: 0.2rem 0 0; }
.apt-card__right { text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem; }
.apt-card__price { font-size: 1.05rem; font-weight: 600; color: var(--c-caramel); margin: 0; }
.apt-card__cancel {
  font-size: 0.8rem; color: #b05050; background: none;
  border: 1px solid #e0b0b0; border-radius: 4px;
  padding: 0.25rem 0.7rem; cursor: pointer; transition: background 0.2s;
}
.apt-card__cancel:hover    { background: #fdf0f0; }
.apt-card__cancel:disabled { opacity: 0.5; cursor: not-allowed; }

.empty { text-align: center; padding: 4rem 0; }
.empty__text { color: #8a7060; margin: 0 0 1.25rem; }
.btn {
  display: inline-block; padding: 0.7rem 1.75rem;
  background: var(--c-matcha); color: #fff; border: none;
  border-radius: 5px; text-decoration: none; font-size: 0.9rem;
  cursor: pointer; transition: opacity 0.2s;
}
.btn:hover    { opacity: 0.85; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
