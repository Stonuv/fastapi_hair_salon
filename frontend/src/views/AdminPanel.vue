<template>
  <div class="page">

    <div v-if="auth.user?.role !== 'admin'" class="empty">
      <p>Доступ только для администратора</p>
    </div>

    <template v-else>
      <section class="hero">
        <p class="hero__eyebrow">Администратор</p>
        <h1 class="hero__title">Панель управления</h1>
      </section>

      <div class="scissors-divider">✂</div>

      <div class="grid">

        <!-- Создать мастера -->
        <div class="card">
          <h2 class="card__title">Создать мастера</h2>
          <p class="card__hint">
            1. Зарегистрируйте пользователя<br>
            2. Введите его UUID ниже
          </p>

          <div class="form">
            <input v-model="newMaster.userId" class="input"
                   placeholder="UUID пользователя" />
            <div class="form__row">
              <button class="btn" :disabled="masterLoading" @click="promoteToMaster">
                {{ masterLoading ? '…' : 'Назначить мастером' }}
              </button>
            </div>
            <p v-if="masterMsg" class="msg" :class="masterMsg.ok ? 'msg--ok' : 'msg--err'">
              {{ masterMsg.text }}
            </p>
          </div>

          <!-- Список пользователей -->
          <div class="users-list" v-if="users.length">
            <p class="users-list__label">Пользователи в системе:</p>
            <div
              v-for="u in users"
              :key="u.id"
              class="user-row"
              @click="newMaster.userId = u.id"
            >
              <span class="user-row__name">{{ u.first_name }} {{ u.last_name }}</span>
              <span class="user-row__role" :class="`user-row__role--${u.role}`">
                {{ u.role }}
              </span>
            </div>
          </div>
        </div>

        <!-- Создать услугу -->
        <div class="card">
          <h2 class="card__title">Добавить услугу</h2>

          <div class="form">
            <input v-model="newService.name" class="input" placeholder="Название" />
            <textarea v-model="newService.description" class="input input--textarea"
                      placeholder="Описание (необязательно)" />
            <div class="form__row">
              <input v-model.number="newService.price" class="input"
                     type="number" placeholder="Цена, ₽" />
              <input v-model.number="newService.duration_min" class="input"
                     type="number" placeholder="Длительность, мин" />
            </div>
            <button class="btn" :disabled="serviceLoading" @click="createService">
              {{ serviceLoading ? '…' : 'Создать услугу' }}
            </button>
            <p v-if="serviceMsg" class="msg" :class="serviceMsg.ok ? 'msg--ok' : 'msg--err'">
              {{ serviceMsg.text }}
            </p>
          </div>

          <!-- Список услуг -->
          <div class="users-list" v-if="services.length">
            <p class="users-list__label">Услуги в системе:</p>
            <div v-for="s in services" :key="s.id" class="user-row">
              <span class="user-row__name">{{ s.name }}</span>
              <span class="user-row__role">{{ s.duration_min }} мин · {{ s.price }} ₽</span>
            </div>
          </div>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { mastersApi, servicesApi } from '../api'
import adminApi from '../api/admin'

const auth = useAuthStore()

// ── Данные ───────────────────────────────────────────────────────
const users    = ref([])
const services = ref([])

onMounted(async () => {
  if (auth.user?.role !== 'admin') return
  try {
    const sRes = await servicesApi.getAll()
    services.value = sRes.data.services
  } catch {}
})

// ── Создание мастера ─────────────────────────────────────────────
const newMaster    = reactive({ userId: '' })
const masterLoading = ref(false)
const masterMsg     = ref(null)

async function promoteToMaster() {
  if (!newMaster.userId.trim()) return
  masterLoading.value = true
  masterMsg.value     = null
  try {
    // Шаг 1: назначить роль master
    await adminApi.changeRole(newMaster.userId, 'master')
    // Шаг 2: создать профиль мастера
    await adminApi.createMasterProfile(newMaster.userId)
    masterMsg.value  = { ok: true, text: 'Мастер создан успешно!' }
    newMaster.userId = ''
    // Обновляем список мастеров
    const mRes = await mastersApi.getAll()
  } catch (e) {
    masterMsg.value = { ok: false, text: e.response?.data?.detail || 'Ошибка' }
  } finally {
    masterLoading.value = false
  }
}

// ── Создание услуги ──────────────────────────────────────────────
const newService = reactive({
  name: '', description: '', price: null, duration_min: null
})
const serviceLoading = ref(false)
const serviceMsg     = ref(null)

async function createService() {
  if (!newService.name || !newService.price || !newService.duration_min) return
  serviceLoading.value = true
  serviceMsg.value     = null
  try {
    await adminApi.createService(newService)
    serviceMsg.value = { ok: true, text: 'Услуга создана!' }
    const sRes = await servicesApi.getAll()
    services.value = sRes.data.services
    Object.assign(newService, { name: '', description: '', price: null, duration_min: null })
  } catch (e) {
    serviceMsg.value = { ok: false, text: e.response?.data?.detail || 'Ошибка' }
  } finally {
    serviceLoading.value = false
  }
}
</script>

<style scoped>
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem 5rem;
}
.hero { padding: 3rem 0 2rem; }
.hero__eyebrow {
  font-size: 0.8rem; text-transform: uppercase;
  letter-spacing: 0.15em; color: var(--c-caramel); margin: 0 0 0.5rem;
}
.hero__title {
  font-family: var(--f-display); font-size: 2.5rem;
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

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1.5rem;
}
.card {
  background: var(--c-cream);
  border: 1px solid var(--c-latte);
  border-radius: 10px;
  padding: 1.75rem;
}
.card__title {
  font-family: var(--f-display); font-size: 1.3rem;
  font-weight: 400; color: var(--c-espresso); margin: 0 0 0.5rem;
}
.card__hint {
  font-size: 0.85rem; color: #8a7060;
  margin: 0 0 1.25rem; line-height: 1.6;
}

.form { display: flex; flex-direction: column; gap: 0.65rem; }
.form__row { display: flex; gap: 0.65rem; }

.input {
  width: 100%; padding: 0.65rem 0.9rem;
  border: 1px solid var(--c-latte); border-radius: 5px;
  background: #fff; font-size: 0.9rem; color: var(--c-espresso);
  outline: none; font-family: var(--f-body);
  transition: border-color 0.2s; box-sizing: border-box;
}
.input:focus { border-color: var(--c-matcha); }
.input--textarea { resize: vertical; min-height: 72px; }

.btn {
  padding: 0.65rem 1.5rem;
  background: var(--c-matcha); color: #fff;
  border: none; border-radius: 5px;
  font-size: 0.9rem; cursor: pointer;
  transition: opacity 0.2s; width: 100%;
}
.btn:hover    { opacity: 0.85; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.msg { font-size: 0.875rem; margin: 0; }
.msg--ok  { color: var(--c-matcha); }
.msg--err { color: #b05050; }

.users-list { margin-top: 1.25rem; border-top: 1px solid var(--c-latte); padding-top: 1rem; }
.users-list__label {
  font-size: 0.75rem; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--c-caramel); margin: 0 0 0.75rem;
}
.user-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 0.75rem; border-radius: 5px; cursor: pointer;
  transition: background 0.15s;
}
.user-row:hover { background: #ede7de; }
.user-row__name { font-size: 0.9rem; color: var(--c-espresso); }
.user-row__role {
  font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--c-caramel);
}
.user-row__role--master { color: var(--c-matcha); }
.user-row__role--admin  { color: var(--c-espresso); }

.empty { text-align: center; padding: 4rem 0; color: #8a7060; }
</style>
