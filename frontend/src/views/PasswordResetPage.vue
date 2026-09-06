<template>
  <div class="flex min-h-[calc(100vh-65px)] items-center justify-center px-4 py-12">
    <BaseCard class="w-full max-w-md">
      <template v-if="!token">
        <h1 class="text-center font-display text-2xl font-black uppercase tracking-tight text-ink-900">Восстановление пароля</h1>
        <p class="mt-1 text-center text-sm text-ink-600">
          Укажите email — если он зарегистрирован, мы пришлём ссылку для сброса пароля
        </p>

        <form class="mt-6 space-y-4" novalidate @submit.prevent="submitRequest">
          <BaseInput
            v-model="email"
            label="Email"
            type="email"
            required
            autocomplete="email"
            :error="errors.email"
            @blur="validateEmail"
          />
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
            :error="errors.new_password"
            @blur="validatePassword"
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
import { useFormErrors } from '../composables/useFormErrors'
import { extractErrorMessage } from '../utils/errors'
import { emailError, passwordError } from '../utils/validators'
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
const { errors, setOrClear, setFromResponse } = useFormErrors()

function validateEmail() {
  return setOrClear('email', emailError(email.value))
}

function validatePassword() {
  return setOrClear('new_password', passwordError(newPassword.value))
}

async function submitRequest() {
  if (!validateEmail()) return
  loading.value = true
  try {
    await authApi.requestPasswordReset(email.value)
    requested.value = true
    toast.info('Если этот email зарегистрирован, ссылка для сброса пароля отправлена')
  } catch (err) {
    if (!setFromResponse(err)) toast.error(extractErrorMessage(err))
  } finally {
    loading.value = false
  }
}

async function submitConfirm() {
  if (!validatePassword()) return
  loading.value = true
  try {
    await authApi.confirmPasswordReset(token, newPassword.value)
    toast.success('Пароль изменён, теперь можно войти')
    router.push('/login')
  } catch (err) {
    // 422 по полю new_password (слишком короткий/длинный пароль) ложится под
    // поле; протухший токен приходит строкой detail -- он показывается тостом.
    if (!setFromResponse(err)) toast.error(extractErrorMessage(err, 'Ссылка недействительна или просрочена'))
  } finally {
    loading.value = false
  }
}
</script>
