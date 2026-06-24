<template>
  <div class="flex min-h-[calc(100vh-65px)] items-center justify-center px-4 py-12">
    <BaseCard class="w-full max-w-md">
      <template v-if="!token">
        <h1 class="text-center font-display text-2xl font-black uppercase tracking-tight text-ink-900">Восстановление пароля</h1>
        <p class="mt-1 text-center text-sm text-ink-600">
          Укажите email — если он зарегистрирован, мы пришлём ссылку для сброса пароля
        </p>

        <form class="mt-6 space-y-4" novalidate @submit.prevent="submitRequest">
          <BaseInput v-model="email" label="Email" type="email" required autocomplete="email" :error="error" />
          <BaseButton type="submit" class="w-full" :loading="loading" :disabled="requested">
            {{ requested ? 'Ссылка отправлена' : 'Отправить ссылку' }}
          </BaseButton>
        </form>
      </template>

      <template v-else>
        <h1 class="text-center font-display text-2xl font-black uppercase tracking-tight text-ink-900">Новый пароль</h1>
        <p class="mt-1 text-center text-sm text-ink-600">Введите новый пароль для своего аккаунта</p>

        <form class="mt-6 space-y-4" novalidate @submit.prevent="submitConfirm">
          <BaseInput
            v-model="newPassword"
            label="Новый пароль"
            type="password"
            autocomplete="new-password"
            required
            hint="Минимум 8 символов"
            :error="error"
          />
          <BaseButton type="submit" class="w-full" :loading="loading">Сохранить пароль</BaseButton>
        </form>
      </template>

      <p class="mt-4 text-center text-sm">
        <router-link to="/login" class="text-brand-900 hover:underline">Вернуться ко входу</router-link>
      </p>
    </BaseCard>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '../api'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseButton from '../components/ui/BaseButton.vue'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const token = route.query.token ?? ''
const email = ref('')
const newPassword = ref('')
const loading = ref(false)
const requested = ref(false)
const error = ref('')

async function submitRequest() {
  if (!email.value) {
    error.value = 'Укажите email'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await authApi.requestPasswordReset(email.value)
    requested.value = true
    toast.info('Если этот email зарегистрирован, ссылка для сброса пароля отправлена')
  } catch (err) {
    toast.error(extractErrorMessage(err))
  } finally {
    loading.value = false
  }
}

async function submitConfirm() {
  if (newPassword.value.length < 8) {
    error.value = 'Минимум 8 символов'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await authApi.confirmPasswordReset(token, newPassword.value)
    toast.success('Пароль изменён, теперь можно войти')
    router.push('/login')
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Ссылка недействительна или просрочена'))
  } finally {
    loading.value = false
  }
}
</script>
