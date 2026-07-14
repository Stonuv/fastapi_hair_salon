<template>
  <div v-if="visible" class="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 bg-amber-100 px-4 py-2 text-center font-mono text-[11px] uppercase tracking-wide text-amber-800">
    <span>Подтвердите email {{ auth.user.email }} — мы отправили ссылку на почту</span>
    <button
      type="button" class="cursor-pointer underline hover:no-underline disabled:cursor-not-allowed disabled:opacity-60"
      :disabled="sending" @click="resend"
    >{{ sending ? 'Отправка…' : 'Отправить письмо ещё раз' }}</button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { authApi } from '../api'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'

const auth = useAuthStore()
const toast = useToastStore()
const sending = ref(false)

// Мягкий гейт — неподтверждённый email не блокирует ничего в интерфейсе,
// это просто постоянное напоминание, пока пользователь не перейдёт по
// ссылке из письма (см. AuthService.send_verification_email на бэкенде).
const visible = computed(() => auth.isLoggedIn && !!auth.user?.email && !auth.user?.email_verified)

async function resend() {
  sending.value = true
  try {
    await authApi.resendEmailVerification()
    toast.success('Письмо с подтверждением отправлено')
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось отправить письмо'))
  } finally {
    sending.value = false
  }
}
</script>
