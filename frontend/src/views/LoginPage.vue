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

        <!-- Второй фактор админ-панели: поле появляется, только если на
             сервере задан ADMIN_LOGIN_TOKEN. Клиенту оно не нужно -- он
             оставляет его пустым, сервер спрашивает код лишь у владельца и
             администратора. -->
        <BaseInput
          v-if="adminTokenRequired"
          v-model="form.admin_token"
          label="Код администратора"
          type="password"
          autocomplete="one-time-code"
          hint="Только для владельца и администратора — клиенту заполнять не нужно"
        />

        <BaseButton type="submit" class="w-full" :loading="loading">Войти</BaseButton>
      </form>

      <VkLoginButton />

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
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { authApi } from '../api'
import { useFormErrors } from '../composables/useFormErrors'
import { extractErrorMessage } from '../utils/errors'
import { emailError } from '../utils/validators'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import VkLoginButton from '../components/ui/VkLoginButton.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()
const { errors, setOrClear, validateAll, setFromResponse } = useFormErrors()

const form = reactive({ email: '', password: '', admin_token: '' })
const loading = ref(false)
const adminTokenRequired = ref(false)

// Ошибки OAuth-редиректа приходят query-параметром (см. routes/auth.py
// vk_callback: fail() редиректит на /login?error=<код>, а не 4xx/5xx —
// пользователь в этот момент уже в браузере посреди редиректа с VK).
const VK_ERROR_MESSAGES = {
  vk_not_configured: 'Вход через VK временно недоступен',
  vk_auth_cancelled: 'Вход через VK отменён',
  vk_auth_failed: 'Не удалось войти через VK. Попробуйте ещё раз',
  vk_token_exchange_failed: 'Не удалось войти через VK. Попробуйте ещё раз',
  vk_user_info_failed: 'Не удалось получить данные профиля VK',
  account_blocked: 'Аккаунт заблокирован. Обратитесь к администратору',
  admin_token_required:
    'Владельцу и администратору вход через VK недоступен, пока включён код администратора. '
    + 'Войдите по email и паролю, указав код.',
}

onMounted(async () => {
  const code = route.query.error
  if (code) toast.error(VK_ERROR_MESSAGES[code] || 'Не удалось войти через VK')
  try {
    const { data } = await authApi.adminTokenRequired()
    adminTokenRequired.value = data.required
  } catch {
    // Флаг — не повод ронять форму входа: клиентам поле всё равно не нужно,
    // а администратор при недоступном флаге увидит «Неверный код
    // администратора» и перезагрузит страницу.
  }
})

const validateEmail = () => setOrClear('email', emailError(form.email))
// На входе пароль проверяется только на «не пустой»: длину задаёт
// PasswordStr при регистрации, а на форме входа требование «минимум 8»
// ничего не даёт -- пароль всё равно сверяется с хешем на сервере.
const validatePassword = () => setOrClear('password', form.password ? '' : 'Укажите пароль')

async function submit() {
  if (!validateAll(validateEmail, validatePassword)) return

  loading.value = true
  try {
    // Пустой код не отправляем: полю в схеме соответствует str | None, и
    // сервер не должен отличать «клиент не заполнял» от «админ стёр».
    await auth.login({
      email: form.email,
      password: form.password,
      admin_token: form.admin_token || undefined,
    })
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
