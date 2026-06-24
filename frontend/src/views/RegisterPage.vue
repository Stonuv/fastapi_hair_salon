<template>
  <div class="flex min-h-[calc(100vh-65px)] items-center justify-center px-4 py-12">
    <BaseCard class="w-full max-w-md">
      <h1 class="text-center font-display text-2xl font-black uppercase tracking-tight text-ink-900">Регистрация</h1>
      <p class="mt-1 text-center text-sm text-ink-600">Создайте аккаунт, чтобы записываться онлайн</p>

      <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
        <div class="grid grid-cols-2 gap-3">
          <BaseInput
            v-model="form.first_name"
            label="Имя"
            required
            :error="errors.first_name"
            @blur="validateField('first_name', form.first_name, 'Укажите имя')"
          />
          <BaseInput
            v-model="form.last_name"
            label="Фамилия"
            required
            :error="errors.last_name"
            @blur="validateField('last_name', form.last_name, 'Укажите фамилию')"
          />
        </div>

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
          v-model="form.phone"
          label="Телефон"
          hint="Необязательно"
          autocomplete="tel"
          :error="errors.phone"
        />
        <BaseInput
          v-model="form.password"
          label="Пароль"
          type="password"
          autocomplete="new-password"
          required
          hint="Минимум 8 символов"
          :error="errors.password"
          @blur="validatePassword"
        />

        <BaseButton type="submit" class="w-full" :loading="loading">Зарегистрироваться</BaseButton>
      </form>

      <p class="mt-4 text-center text-sm text-ink-600">
        Уже есть аккаунт?
        <router-link to="/login" class="font-medium text-brand-900 hover:underline">Войти</router-link>
      </p>
    </BaseCard>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { useFormErrors } from '../composables/useFormErrors'
import { extractErrorMessage } from '../utils/errors'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseButton from '../components/ui/BaseButton.vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()
const { errors, setError, clearError, setFromResponse } = useFormErrors()

const form = reactive({ first_name: '', last_name: '', email: '', phone: '', password: '' })
const loading = ref(false)

function validateField(field, value, message) {
  if (!value.trim()) return setError(field, message)
  clearError(field)
}

function validateEmail() {
  if (!form.email) return setError('email', 'Укажите email')
  if (!/^\S+@\S+\.\S+$/.test(form.email)) return setError('email', 'Некорректный email')
  clearError('email')
}

function validatePassword() {
  if (form.password.length < 8) return setError('password', 'Минимум 8 символов')
  clearError('password')
}

function validateAll() {
  validateField('first_name', form.first_name, 'Укажите имя')
  validateField('last_name', form.last_name, 'Укажите фамилию')
  validateEmail()
  validatePassword()
  return !Object.keys(errors).length
}

async function submit() {
  if (!validateAll()) return

  loading.value = true
  try {
    await auth.register({ ...form, phone: form.phone || null })
    toast.success('Регистрация прошла успешно!')
    router.push('/')
  } catch (err) {
    if (!setFromResponse(err)) {
      toast.error(extractErrorMessage(err, 'Не удалось зарегистрироваться'))
    }
  } finally {
    loading.value = false
  }
}
</script>
