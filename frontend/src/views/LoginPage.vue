<template>
  <div class="flex min-h-[calc(100vh-65px)] items-center justify-center px-4 py-12">
    <BaseCard class="w-full max-w-md">
      <h1 class="text-center font-display text-2xl font-black uppercase tracking-tight text-ink-900">Вход</h1>
      <p class="mt-1 text-center text-sm text-ink-600">Войдите, чтобы записаться к мастеру</p>

      <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
        <BaseInput
          v-model="form.email"
          label="Email"
          type="email"
          autocomplete="email"
          required
          :error="errors.email"
          @blur="validateEmail"
        />
        <BaseInput
          v-model="form.password"
          label="Пароль"
          type="password"
          autocomplete="current-password"
          required
          :error="errors.password"
          @blur="validatePassword"
        />

        <BaseButton type="submit" class="w-full" :loading="loading">Войти</BaseButton>
      </form>

      <p class="mt-4 text-center text-sm">
        <router-link to="/password-reset" class="text-brand-900 hover:underline">Забыли пароль?</router-link>
      </p>
      <p class="mt-2 text-center text-sm text-ink-600">
        Нет аккаунта?
        <router-link to="/register" class="font-medium text-brand-900 hover:underline">Зарегистрироваться</router-link>
      </p>
    </BaseCard>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { useFormErrors } from '../composables/useFormErrors'
import { extractErrorMessage } from '../utils/errors'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseButton from '../components/ui/BaseButton.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()
const { errors, setError, clearError, setFromResponse } = useFormErrors()

const form = reactive({ email: '', password: '' })
const loading = ref(false)

function validateEmail() {
  if (!form.email) return setError('email', 'Укажите email')
  if (!/^\S+@\S+\.\S+$/.test(form.email)) return setError('email', 'Некорректный email')
  clearError('email')
}

function validatePassword() {
  if (!form.password) return setError('password', 'Укажите пароль')
  clearError('password')
}

async function submit() {
  validateEmail()
  validatePassword()
  if (errors.email || errors.password) return

  loading.value = true
  try {
    await auth.login(form)
    toast.success('Добро пожаловать!')
    router.push(route.query.redirect || '/')
  } catch (err) {
    if (!setFromResponse(err)) {
      toast.error(extractErrorMessage(err, 'Неверный email или пароль'))
    }
  } finally {
    loading.value = false
  }
}
</script>
