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

      <!-- Табы -->
      <div class="tabs">
        <button v-for="t in tabs" :key="t.id"
                class="tab" :class="{ 'tab--active': activeTab === t.id }"
                @click="activeTab = t.id">
          {{ t.label }}
        </button>
      </div>

      <!-- ── Таб: Пользователи ── -->
      <div v-if="activeTab === 'users'" class="tab-content">
        <div class="toolbar">
          <h2 class="section-title">Пользователи</h2>
        </div>

        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>Имя</th><th>Email</th><th>Роль</th><th>Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in allUsers" :key="u.id">
                <td>{{ u.first_name }} {{ u.last_name }}</td>
                <td>{{ u.email }}</td>
                <td>
                  <select class="inline-select"
                          :value="u.role"
                          @change="changeRole(u.id, $event.target.value)">
                    <option value="client">client</option>
                    <option value="master">master</option>
                    <option value="admin">admin</option>
                  </select>
                </td>
                <td class="actions">
                  <button class="action-btn action-btn--master"
                          v-if="u.role === 'master' && !hasMasterProfile(u.id)"
                          @click="createMasterProfile(u.id)">
                    + профиль
                  </button>
                  <button class="action-btn action-btn--del"
                          @click="deleteUser(u.id)">
                    Удалить
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── Таб: Мастера ── -->
      <div v-if="activeTab === 'masters'" class="tab-content">
        <h2 class="section-title">Мастера</h2>

        <div class="cards-grid">
          <div v-for="m in masters" :key="m.id" class="master-card">
            <div class="master-card__photo">
              <img v-if="m.photo_url" :src="m.photo_url" />
              <div v-else class="master-card__no-photo">✂</div>
            </div>
            <div class="master-card__body">
              <p class="master-card__name">{{ m.first_name }} {{ m.last_name }}</p>
              <p class="master-card__spec">{{ m.specialization || '—' }}</p>

              <!-- Фото -->
              <div class="inline-form">
                <input v-model="photoInputs[m.id]" class="input input--sm"
                       placeholder="URL фото" />
                <button class="action-btn" @click="updatePhoto(m.id, photoInputs[m.id])">
                  Сохранить
                </button>
              </div>

              <!-- Услуги -->
              <div class="master-services">
                <p class="sub-label">Услуги</p>
                <div v-for="ms in masterServicesMap[m.id] || []" :key="ms.service.id"
                     class="ms-row">
                  <span>{{ ms.service.name }} · {{ ms.final_price }} ₽</span>
                  <button class="action-btn action-btn--del"
                          @click="removeService(m.id, ms.service.id)">×</button>
                </div>
                <div class="inline-form">
                  <select v-model="assignMap[m.id]" class="input input--sm">
                    <option value="" disabled>Добавить услугу</option>
                    <option v-for="s in services" :key="s.id" :value="s.id">
                      {{ s.name }}
                    </option>
                  </select>
                  <button class="action-btn"
                          @click="addService(m.id, assignMap[m.id])">+</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Таб: Услуги ── -->
      <div v-if="activeTab === 'services'" class="tab-content">
        <div class="two-col">

          <!-- Форма создания -->
          <div class="card">
            <h2 class="card__title">Новая услуга</h2>
            <div class="form">
              <input v-model="newService.name" class="input" placeholder="Название" />
              <textarea v-model="newService.description" class="input input--textarea"
                        placeholder="Описание" />
              <div class="form__row">
                <input v-model.number="newService.price" class="input"
                       type="number" placeholder="Цена, ₽" />
                <input v-model.number="newService.duration_min" class="input"
                       type="number" placeholder="Мин." />
              </div>
              <button class="btn" :disabled="serviceLoading" @click="createService">
                {{ serviceLoading ? '…' : 'Создать' }}
              </button>
              <p v-if="serviceMsg" class="msg" :class="serviceMsg.ok ? 'msg--ok' : 'msg--err'">
                {{ serviceMsg.text }}
              </p>
            </div>
          </div>

          <!-- Список услуг -->
          <div class="card">
            <h2 class="card__title">Все услуги</h2>
            <div v-for="s in services" :key="s.id" class="service-row">
              <template v-if="editingService?.id === s.id">
                <div class="form">
                  <input v-model="editingService.name" class="input input--sm" />
                  <div class="form__row">
                    <input v-model.number="editingService.price"
                           class="input input--sm" type="number" placeholder="Цена" />
                    <input v-model.number="editingService.duration_min"
                           class="input input--sm" type="number" placeholder="Мин." />
                  </div>
                  <div class="form__row">
                    <button class="action-btn" @click="saveService">Сохранить</button>
                    <button class="action-btn action-btn--ghost"
                            @click="editingService = null">Отмена</button>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="service-row__info">
                  <span class="service-row__name">{{ s.name }}</span>
                  <span class="service-row__meta">{{ s.duration_min }} мин · {{ s.price }} ₽</span>
                </div>
                <div class="actions">
                  <button class="action-btn" @click="startEdit(s)">Изм.</button>
                  <button class="action-btn action-btn--del"
                          @click="deleteService(s.id)">Удалить</button>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { mastersApi, servicesApi } from '../api'
import adminApi from '../api/admin'

const auth = useAuthStore()

const tabs = [
  { id: 'users',    label: 'Пользователи' },
  { id: 'masters',  label: 'Мастера'      },
  { id: 'services', label: 'Услуги'       },
]
const activeTab = ref('users')

// ── Данные ───────────────────────────────────────────────────────
const allUsers       = ref([])
const masters        = ref([])
const services       = ref([])
const masterServicesMap = ref({})
const photoInputs    = reactive({})
const assignMap      = reactive({})

onMounted(async () => {
  if (auth.user?.role !== 'admin') return
  await reload()
})

async function reload() {
  const [uRes, mRes, sRes] = await Promise.all([
    adminApi.getUsers(),
    mastersApi.getAll(),
    servicesApi.getAll(),
  ])
  allUsers.value  = uRes.data
  masters.value   = mRes.data.masters
  services.value  = sRes.data.services

  // Загружаем услуги каждого мастера
  for (const m of masters.value) {
    photoInputs[m.id] = m.photo_url || ''
    assignMap[m.id]   = ''
    try {
      const res = await mastersApi.getServices(m.id)
      masterServicesMap.value[m.id] = res.data
    } catch {
      masterServicesMap.value[m.id] = []
    }
  }
}

function hasMasterProfile(userId) {
  return masters.value.some(m => m.id === userId)
}

// ── Пользователи ─────────────────────────────────────────────────
async function changeRole(userId, role) {
  try {
    await adminApi.changeRole(userId, role)
    const u = allUsers.value.find(u => u.id === userId)
    if (u) u.role = role
  } catch (e) { alert(e.response?.data?.detail || 'Ошибка') }
}

async function createMasterProfile(userId) {
  try {
    await adminApi.createMasterProfile(userId)
    const mRes = await mastersApi.getAll()
    masters.value = mRes.data.masters
    alert('Профиль мастера создан!')
  } catch (e) { alert(e.response?.data?.detail || 'Ошибка') }
}

async function deleteUser(userId) {
  if (!confirm('Удалить пользователя? Это действие необратимо.')) return
  try {
    await adminApi.deleteUser(userId)
    allUsers.value = allUsers.value.filter(u => u.id !== userId)
  } catch (e) { alert(e.response?.data?.detail || 'Ошибка') }
}

// ── Мастера ──────────────────────────────────────────────────────
async function updatePhoto(masterId, url) {
  try {
    await adminApi.updateMasterPhoto(masterId, url)
    const m = masters.value.find(m => m.id === masterId)
    if (m) m.photo_url = url
  } catch (e) { alert(e.response?.data?.detail || 'Ошибка') }
}

async function addService(masterId, serviceId) {
  if (!serviceId) return
  try {
    await adminApi.addServiceToMaster(masterId, serviceId)
    const res = await mastersApi.getServices(masterId)
    masterServicesMap.value[masterId] = res.data
    assignMap[masterId] = ''
  } catch (e) { alert(e.response?.data?.detail || 'Ошибка') }
}

async function removeService(masterId, serviceId) {
  if (!confirm('Убрать услугу у мастера?')) return
  try {
    await adminApi.removeServiceFromMaster(masterId, serviceId)
    masterServicesMap.value[masterId] =
      masterServicesMap.value[masterId].filter(ms => ms.service.id !== serviceId)
  } catch (e) { alert(e.response?.data?.detail || 'Ошибка') }
}

// ── Услуги ───────────────────────────────────────────────────────
const newService    = reactive({ name: '', description: '', price: null, duration_min: null })
const serviceLoading = ref(false)
const serviceMsg     = ref(null)
const editingService = ref(null)

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

function startEdit(s) {
  editingService.value = { ...s }
}

async function saveService() {
  try {
    await adminApi.updateService(editingService.value.id, {
      name:         editingService.value.name,
      price:        editingService.value.price,
      duration_min: editingService.value.duration_min,
    })
    const idx = services.value.findIndex(s => s.id === editingService.value.id)
    if (idx !== -1) services.value[idx] = { ...services.value[idx], ...editingService.value }
    editingService.value = null
  } catch (e) { alert(e.response?.data?.detail || 'Ошибка') }
}

async function deleteService(serviceId) {
  if (!confirm('Удалить услугу?')) return
  try {
    await adminApi.deleteService(serviceId)
    services.value = services.value.filter(s => s.id !== serviceId)
  } catch (e) { alert(e.response?.data?.detail || 'Ошибка') }
}
</script>

<style scoped>
.page { max-width: 1100px; margin: 0 auto; padding: 2.5rem 1.5rem 5rem; }
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
  text-align: center; font-size: 0.9rem; color: var(--c-latte);
  position: relative; margin: 0 0 2rem;
}
.scissors-divider::before, .scissors-divider::after {
  content: ''; position: absolute; top: 50%;
  width: calc(50% - 1.5rem); height: 1px; background: var(--c-latte);
}
.scissors-divider::before { left: 0; }
.scissors-divider::after  { right: 0; }

/* Tabs */
.tabs { display: flex; gap: 0.5rem; margin-bottom: 2rem; border-bottom: 1px solid var(--c-latte); }
.tab {
  padding: 0.6rem 1.25rem; background: none; border: none;
  border-bottom: 2px solid transparent; font-size: 0.9rem;
  color: #8a7060; cursor: pointer; margin-bottom: -1px;
  transition: color 0.2s, border-color 0.2s;
}
.tab:hover      { color: var(--c-espresso); }
.tab--active    { color: var(--c-espresso); border-bottom-color: var(--c-matcha); font-weight: 500; }

.tab-content { }
.section-title {
  font-family: var(--f-display); font-size: 1.4rem;
  font-weight: 400; color: var(--c-espresso); margin: 0 0 1.25rem;
}

/* Table */
.table-wrap { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.table th {
  text-align: left; padding: 0.6rem 0.75rem;
  font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--c-caramel); border-bottom: 1px solid var(--c-latte);
}
.table td {
  padding: 0.75rem; border-bottom: 1px solid #ede7de; color: var(--c-espresso);
}
.table tr:hover td { background: #faf7f3; }

.inline-select {
  padding: 0.3rem 0.5rem; border: 1px solid var(--c-latte);
  border-radius: 4px; font-size: 0.85rem; background: #fff;
  color: var(--c-espresso); cursor: pointer;
}
.actions { display: flex; gap: 0.4rem; flex-wrap: wrap; }

/* Action buttons */
.action-btn {
  padding: 0.25rem 0.65rem; font-size: 0.8rem;
  border-radius: 4px; cursor: pointer; border: 1px solid var(--c-latte);
  background: #fff; color: var(--c-espresso); transition: background 0.15s;
}
.action-btn:hover       { background: #ede7de; }
.action-btn--del        { border-color: #e0b0b0; color: #b05050; }
.action-btn--del:hover  { background: #fdf0f0; }
.action-btn--master     { border-color: var(--c-matcha); color: var(--c-matcha); }
.action-btn--ghost      { background: transparent; }

/* Master cards */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.25rem; }
.master-card { background: var(--c-cream); border: 1px solid var(--c-latte); border-radius: 8px; overflow: hidden; }
.master-card__photo { width: 100%; height: 160px; background: var(--c-latte); overflow: hidden; display: flex; align-items: center; justify-content: center; }
.master-card__photo img { width: 100%; height: 100%; object-fit: cover; }
.master-card__no-photo { font-size: 2rem; opacity: 0.3; }
.master-card__body { padding: 1rem; }
.master-card__name { font-family: var(--f-display); font-size: 1.1rem; color: var(--c-espresso); margin: 0; }
.master-card__spec { font-size: 0.8rem; color: #8a7060; margin: 0.2rem 0 0.75rem; }

.inline-form { display: flex; gap: 0.4rem; margin-top: 0.5rem; }
.master-services { margin-top: 0.75rem; border-top: 1px solid var(--c-latte); padding-top: 0.75rem; }
.sub-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--c-caramel); margin: 0 0 0.4rem; }
.ms-row { display: flex; justify-content: space-between; align-items: center; padding: 0.25rem 0; font-size: 0.85rem; color: var(--c-espresso); }

/* Two col */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
@media (max-width: 700px) { .two-col { grid-template-columns: 1fr; } }

/* Card */
.card { background: var(--c-cream); border: 1px solid var(--c-latte); border-radius: 10px; padding: 1.5rem; }
.card__title { font-family: var(--f-display); font-size: 1.2rem; font-weight: 400; color: var(--c-espresso); margin: 0 0 1rem; }

/* Form */
.form { display: flex; flex-direction: column; gap: 0.6rem; }
.form__row { display: flex; gap: 0.6rem; }

.input {
  width: 100%; padding: 0.6rem 0.85rem; border: 1px solid var(--c-latte);
  border-radius: 5px; background: #fff; font-size: 0.9rem; color: var(--c-espresso);
  outline: none; font-family: var(--f-body); transition: border-color 0.2s; box-sizing: border-box;
}
.input:focus    { border-color: var(--c-matcha); }
.input--sm      { padding: 0.4rem 0.65rem; font-size: 0.85rem; }
.input--textarea { resize: vertical; min-height: 70px; }

.btn {
  padding: 0.65rem; background: var(--c-matcha); color: #fff;
  border: none; border-radius: 5px; font-size: 0.9rem;
  cursor: pointer; transition: opacity 0.2s; width: 100%;
}
.btn:hover    { opacity: 0.85; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.msg { font-size: 0.875rem; margin: 0; }
.msg--ok  { color: var(--c-matcha); }
.msg--err { color: #b05050; }

/* Service rows */
.service-row {
  padding: 0.75rem 0; border-bottom: 1px solid #ede7de;
  display: flex; justify-content: space-between; align-items: center; gap: 0.5rem;
}
.service-row:last-child { border-bottom: none; }
.service-row__info { display: flex; flex-direction: column; gap: 0.2rem; }
.service-row__name { font-size: 0.9rem; color: var(--c-espresso); }
.service-row__meta { font-size: 0.8rem; color: #8a7060; }

.empty { text-align: center; padding: 4rem 0; color: #8a7060; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
</style>
