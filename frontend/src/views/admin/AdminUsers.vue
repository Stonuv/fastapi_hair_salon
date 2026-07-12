<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div class="grid flex-1 gap-3 sm:grid-cols-[2fr_1fr_1fr]">
        <BaseInput v-model="search" placeholder="Поиск по имени или email…" aria-label="Поиск" />
        <BaseSelect v-model="role" placeholder="Любая роль">
          <option value="client">Клиент</option>
          <option value="master">Мастер</option>
          <option value="admin">Администратор</option>
        </BaseSelect>
        <div class="flex gap-3">
          <BaseSelect v-model="sortBy" class="flex-1">
            <option value="created_at">По дате регистрации</option>
            <option value="email">По email</option>
          </BaseSelect>
          <button
            class="flex w-11 shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-white text-ink-600 transition-colors duration-200 hover:border-brand-900 hover:text-brand-900 cursor-pointer"
            :aria-label="sortOrder === 'asc' ? 'По возрастанию' : 'По убыванию'"
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
          >
            <BarsArrowUpIcon v-if="sortOrder === 'asc'" class="h-5 w-5" aria-hidden="true" />
            <BarsArrowDownIcon v-else class="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
      <BaseButton @click="openCreate">Создать пользователя</BaseButton>
    </div>

    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 5" :key="i" height="h-20" />
    </div>

    <EmptyState v-else-if="users.length === 0" :icon="UsersIcon" title="Пользователи не найдены" />

    <div v-else class="space-y-3">
      <BaseCard v-for="u in users" :key="u.id" class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="font-medium text-ink-900">
            {{ u.first_name }} {{ u.last_name }}
            <span
              v-if="u.is_blocked"
              class="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700"
            >Заблокирован</span>
          </p>
          <p class="text-sm text-ink-600">{{ u.email }}{{ u.phone ? ` · ${u.phone}` : '' }}</p>
          <p class="mt-1 text-xs text-ink-600/70">Регистрация: {{ formatDate(u.created_at) }}</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <BaseSelect :model-value="u.role" class="w-40" @update:model-value="(v) => changeRole(u, v)">
            <option value="client">Клиент</option>
            <option value="master">Мастер</option>
            <option value="admin">Администратор</option>
          </BaseSelect>
          <BaseButton v-if="u.role === 'master'" variant="ghost" size="sm" @click="createMasterProfile(u)">
            Создать профиль мастера
          </BaseButton>
          <BaseButton variant="ghost" size="sm" @click="openEdit(u)">Редактировать</BaseButton>
          <BaseButton variant="ghost" size="sm" @click="toggleBlocked(u)">
            {{ u.is_blocked ? 'Разблокировать' : 'Заблокировать' }}
          </BaseButton>
          <BaseButton variant="danger" size="sm" @click="confirmDelete(u)">Удалить</BaseButton>
        </div>
      </BaseCard>
    </div>

    <Pagination v-model:page="page" :total-pages="totalPages" />

    <Teleport to="body">
      <div v-if="formOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" @click="formOpen = false" />
        <BaseCard class="relative w-full max-w-md">
          <h2 class="font-display text-lg font-bold uppercase tracking-tight text-ink-900">
            {{ editingId ? 'Редактировать пользователя' : 'Новый пользователь' }}
          </h2>
          <form class="mt-4 space-y-4" novalidate @submit.prevent="submitForm">
            <div class="grid grid-cols-2 gap-3">
              <BaseInput v-model="form.first_name" label="Имя" required />
              <BaseInput v-model="form.last_name" label="Фамилия" required />
            </div>
            <BaseInput v-model="form.email" type="email" label="Email" required />
            <BaseInput v-model="form.phone" label="Телефон" hint="Необязательно" />
            <BaseSelect v-if="!editingId" v-model="form.role" label="Роль">
              <option value="client">Клиент</option>
              <option value="master">Мастер</option>
              <option value="admin">Администратор</option>
            </BaseSelect>
            <BaseInput
              v-if="!editingId"
              v-model="form.password"
              type="password"
              label="Пароль"
              hint="Минимум 8 символов"
              required
            />
            <BaseInput
              v-else
              v-model="form.new_password"
              type="password"
              label="Новый пароль"
              hint="Оставьте пустым, чтобы не менять"
            />
            <div class="flex justify-end gap-3">
              <BaseButton variant="ghost" size="sm" type="button" @click="formOpen = false">Отмена</BaseButton>
              <BaseButton size="sm" type="submit" :loading="saving">Сохранить</BaseButton>
            </div>
          </form>
        </BaseCard>
      </div>
    </Teleport>

    <ConfirmDialog
      :open="!!userToDelete"
      title="Удалить пользователя?"
      :message="userToDelete ? `Пользователь ${userToDelete.first_name} ${userToDelete.last_name} будет скрыт из системы.` : ''"
      confirm-label="Удалить"
      danger
      :loading="deleting"
      @update:open="userToDelete = null"
      @confirm="deleteUser"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { UsersIcon, BarsArrowUpIcon, BarsArrowDownIcon } from '@heroicons/vue/24/outline'
import { adminApi } from '../../api'
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

const users = ref([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)
const search = ref('')
const role = ref('')
const sortBy = ref('created_at')
const sortOrder = ref('desc')

const userToDelete = ref(null)
const deleting = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await adminApi.listUsers({
      page: page.value, page_size: 10,
      search: search.value || undefined,
      role: role.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    })
    users.value = data.items
    totalPages.value = data.total_pages
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить пользователей'))
  } finally {
    loading.value = false
  }
}

async function changeRole(user, newRole) {
  try {
    await adminApi.changeUserRole(user.id, newRole)
    user.role = newRole
    toast.success('Роль обновлена')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  }
}

async function toggleBlocked(user) {
  try {
    const { data } = await adminApi.setUserBlocked(user.id, !user.is_blocked)
    user.is_blocked = data.is_blocked
    toast.success(data.is_blocked ? 'Пользователь заблокирован' : 'Пользователь разблокирован')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  }
}

async function createMasterProfile(user) {
  try {
    await adminApi.createMasterProfile(user.id)
    toast.success('Профиль мастера создан')
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Профиль мастера уже существует'))
  }
}

function confirmDelete(user) {
  userToDelete.value = user
}

async function deleteUser() {
  deleting.value = true
  try {
    await adminApi.deleteUser(userToDelete.value.id)
    users.value = users.value.filter((u) => u.id !== userToDelete.value.id)
    toast.success('Пользователь удалён')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  } finally {
    deleting.value = false
    userToDelete.value = null
  }
}

// ── Создание / редактирование ─────────────────────────────────────
const formOpen = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = reactive({ first_name: '', last_name: '', email: '', phone: '', password: '', new_password: '', role: 'client' })

function openCreate() {
  editingId.value = null
  Object.assign(form, { first_name: '', last_name: '', email: '', phone: '', password: '', new_password: '', role: 'client' })
  formOpen.value = true
}

function openEdit(user) {
  editingId.value = user.id
  Object.assign(form, {
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    phone: user.phone || '',
    password: '',
    new_password: '',
    role: user.role,
  })
  formOpen.value = true
}

async function submitForm() {
  saving.value = true
  try {
    if (editingId.value) {
      const { data } = await adminApi.updateUser(editingId.value, {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        phone: form.phone || null,
        new_password: form.new_password || undefined,
      })
      const idx = users.value.findIndex((u) => u.id === editingId.value)
      if (idx !== -1) users.value[idx] = data
      toast.success('Пользователь обновлён')
    } else {
      await adminApi.createUser({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        phone: form.phone || null,
        password: form.password,
        role: form.role,
      })
      toast.success('Пользователь создан')
      page.value = 1
      load()
    }
    formOpen.value = false
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось сохранить пользователя'))
  } finally {
    saving.value = false
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })
}

useDebouncedWatch(search, () => { page.value = 1; load() })
useDebouncedWatch([role, sortBy, sortOrder], () => { page.value = 1; load() }, 0)
useDebouncedWatch(page, load, 0)
onMounted(load)
</script>
