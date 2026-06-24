<template>
  <div>
    <div class="mb-4 grid gap-3 sm:grid-cols-[2fr_1fr_1fr_auto]">
      <BaseInput v-model="search" placeholder="Поиск по имени или email…" aria-label="Поиск" />
      <BaseSelect v-model="role" placeholder="Любая роль">
        <option value="client">Клиент</option>
        <option value="master">Мастер</option>
        <option value="admin">Администратор</option>
      </BaseSelect>
      <BaseSelect v-model="sortBy">
        <option value="created_at">По дате регистрации</option>
        <option value="email">По email</option>
      </BaseSelect>
      <button
        class="flex items-center justify-center rounded-lg border border-stone-200 bg-white px-3 text-ink-600 transition-colors duration-200 hover:border-brand-900 hover:text-brand-900 cursor-pointer"
        @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
      >
        <BarsArrowUpIcon v-if="sortOrder === 'asc'" class="h-5 w-5" aria-hidden="true" />
        <BarsArrowDownIcon v-else class="h-5 w-5" aria-hidden="true" />
      </button>
    </div>

    <div v-if="loading" class="space-y-3">
      <Skeleton v-for="i in 5" :key="i" height="h-20" />
    </div>

    <EmptyState v-else-if="users.length === 0" :icon="UsersIcon" title="Пользователи не найдены" />

    <div v-else class="space-y-3">
      <BaseCard v-for="u in users" :key="u.id" class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="font-medium text-ink-900">{{ u.first_name }} {{ u.last_name }}</p>
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
          <BaseButton variant="danger" size="sm" @click="confirmDelete(u)">Удалить</BaseButton>
        </div>
      </BaseCard>
    </div>

    <Pagination v-model:page="page" :total-pages="totalPages" />

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
import { onMounted, ref } from 'vue'
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

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })
}

useDebouncedWatch(search, () => { page.value = 1; load() })
useDebouncedWatch([role, sortBy, sortOrder], () => { page.value = 1; load() }, 0)
useDebouncedWatch(page, load, 0)
onMounted(load)
</script>
