<template>
  <div class="flex min-h-screen items-center justify-center px-4 py-12">
    <BaseCard class="w-full max-w-xl">
      <p class="font-mono text-xs uppercase tracking-widest text-brand-700">Первый запуск · шаг {{ step }} из 3</p>
      <h1 class="mt-1 font-display text-2xl font-black uppercase tracking-tight text-ink-900">Настройка «Сайтама»</h1>
      <p class="mt-1 text-sm text-ink-600">Создайте аккаунт администратора, чтобы начать работу с панелью управления</p>

      <form class="mt-6 space-y-4" novalidate @submit.prevent="onSubmitStep">
        <!-- Шаг 1: аккаунт администратора -->
        <div v-if="step === 1" class="space-y-4">
          <BaseInput
            v-if="setup.requiresToken"
            v-model="setupToken"
            label="Код настройки"
            required
            hint="Значение переменной окружения SETUP_TOKEN, заданной при деплое"
            :error="errors.setup_token"
            @blur="validateSetupToken"
          />

          <div class="grid grid-cols-2 gap-3">
            <BaseInput
              v-model="admin.first_name"
              label="Имя"
              required
              :error="errors.first_name"
              @blur="validateField('first_name', admin.first_name, 'Укажите имя')"
            />
            <BaseInput
              v-model="admin.last_name"
              label="Фамилия"
              required
              :error="errors.last_name"
              @blur="validateField('last_name', admin.last_name, 'Укажите фамилию')"
            />
          </div>

          <BaseInput
            v-model="admin.email"
            label="Email"
            type="email"
            autocomplete="email"
            required
            :error="errors.email"
            @blur="validateEmail"
          />
          <BaseInput
            v-model="admin.phone"
            label="Телефон"
            hint="Необязательно"
            autocomplete="tel"
            :error="errors.phone"
          />
          <BaseInput
            v-model="admin.password"
            label="Пароль"
            type="password"
            autocomplete="new-password"
            required
            hint="Минимум 8 символов"
            :error="errors.password"
            @blur="validatePassword"
          />
          <BaseInput
            v-model="admin.confirm_password"
            label="Повторите пароль"
            type="password"
            autocomplete="new-password"
            required
            :error="errors.confirm_password"
            @blur="validateConfirmPassword"
          />
        </div>

        <!-- Шаг 2: базовые настройки сайта -->
        <div v-else-if="step === 2" class="space-y-4">
          <Skeleton v-if="settingsLoading" height="h-64" />
          <p v-else-if="!siteContent" class="text-sm text-danger">
            Не удалось загрузить настройки сайта. Можно продолжить без них — эти поля можно будет заполнить позже в «Админ → Настройки».
          </p>
          <template v-else>
            <div class="grid gap-4 sm:grid-cols-2">
              <BaseInput v-model="siteContent.header.brand_name" label="Название бренда" required />
              <BaseInput v-model="siteContent.header.brand_tagline" label="Подпись под названием" required />
            </div>
            <BaseInput v-model="siteContent.footer.address" as="textarea" :rows="3" label="Адрес" hint="Каждая строка — перенос строки" />
            <BaseInput v-model="siteContent.footer.hours" as="textarea" :rows="3" label="Часы работы" hint="Каждая строка — перенос строки" />
            <p class="text-sm text-ink-600/80">Остальной контент сайта можно донастроить позже в «Админ → Настройки».</p>
          </template>
        </div>

        <!-- Шаг 3: проверка и завершение -->
        <div v-else class="space-y-3">
          <p class="text-sm text-ink-600">Проверьте данные перед завершением настройки:</p>
          <dl class="space-y-1.5 rounded-lg border border-stone-200 p-4 text-sm">
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Администратор</dt><dd class="font-medium text-ink-900">{{ admin.first_name }} {{ admin.last_name }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Email</dt><dd class="font-medium text-ink-900">{{ admin.email }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Название бренда</dt><dd class="font-medium text-ink-900">{{ siteContent?.header?.brand_name || '—' }}</dd></div>
          </dl>
        </div>

        <div class="flex justify-between pt-2">
          <BaseButton v-if="step > 1" type="button" variant="ghost" @click="step -= 1">Назад</BaseButton>
          <span v-else />
          <BaseButton type="submit" :loading="loading" :disabled="step === 2 && settingsLoading">
            {{ step < 3 ? 'Далее' : 'Завершить настройку' }}
          </BaseButton>
        </div>
      </form>
    </BaseCard>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { setupApi, settingsApi } from '../api'
import { useAuthStore } from '../stores/auth'
import { useSetupStore } from '../stores/setup'
import { useToastStore } from '../stores/toast'
import { useFormErrors } from '../composables/useFormErrors'
import { extractErrorMessage } from '../utils/errors'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import Skeleton from '../components/ui/Skeleton.vue'

const router = useRouter()
const auth = useAuthStore()
const setup = useSetupStore()
const toast = useToastStore()
const { errors, setError, clearError, clearAll, setFromResponse } = useFormErrors()

const step = ref(1)
const loading = ref(false)
const settingsLoading = ref(true)

const admin = reactive({
  first_name: '', last_name: '', email: '', phone: '',
  password: '', confirm_password: '',
})
const setupToken = ref('')
const siteContent = ref(null)

onMounted(async () => {
  try {
    const { data } = await settingsApi.get()
    siteContent.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить настройки сайта'))
  } finally {
    settingsLoading.value = false
  }
})

function validateField(field, value, message) {
  if (!value.trim()) return setError(field, message)
  clearError(field)
}

function validateEmail() {
  if (!admin.email) return setError('email', 'Укажите email')
  if (!/^\S+@\S+\.\S+$/.test(admin.email)) return setError('email', 'Некорректный email')
  clearError('email')
}

function validatePassword() {
  if (admin.password.length < 8) return setError('password', 'Минимум 8 символов')
  clearError('password')
}

function validateConfirmPassword() {
  if (admin.confirm_password !== admin.password) return setError('confirm_password', 'Пароли не совпадают')
  clearError('confirm_password')
}

function validateSetupToken() {
  if (setup.requiresToken && !setupToken.value.trim()) return setError('setup_token', 'Укажите код настройки')
  clearError('setup_token')
}

function validateStep1() {
  validateField('first_name', admin.first_name, 'Укажите имя')
  validateField('last_name', admin.last_name, 'Укажите фамилию')
  validateEmail()
  validatePassword()
  validateConfirmPassword()
  validateSetupToken()
  return !Object.keys(errors).length
}

async function onSubmitStep() {
  if (step.value === 1) {
    if (!validateStep1()) return
    step.value = 2
    return
  }
  if (step.value === 2) {
    step.value = 3
    return
  }
  await finish()
}

async function finish() {
  loading.value = true
  try {
    const res = await setupApi.complete({
      admin: {
        first_name: admin.first_name,
        last_name: admin.last_name,
        email: admin.email,
        phone: admin.phone || null,
        password: admin.password,
      },
      site_content: siteContent.value,
      setup_token: setupToken.value || null,
    })
    auth.user = res.data.user
    setup.markCompleted()
    toast.success('Настройка завершена — добро пожаловать!')
    router.push({ name: 'admin-stats' })
  } catch (err) {
    if (err.response?.status === 409) {
      setup.markCompleted()
      toast.error('Настройка уже была выполнена ранее')
      router.push({ name: 'login' })
      return
    }
    if (err.response?.status === 403) {
      clearAll()
      setError('setup_token', extractErrorMessage(err, 'Неверный код настройки'))
      step.value = 1
      return
    }
    clearAll()
    if (setFromResponse(err)) {
      if ('email' in errors || 'password' in errors || 'first_name' in errors || 'last_name' in errors || 'phone' in errors) {
        step.value = 1
      }
    } else {
      toast.error(extractErrorMessage(err, 'Не удалось завершить настройку'))
    }
  } finally {
    loading.value = false
  }
}
</script>
