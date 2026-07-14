<template>
  <div class="flex min-h-[calc(100vh-65px)] items-center justify-center px-4 py-12">
    <BaseCard class="w-full max-w-md text-center">
      <template v-if="status === 'loading'">
        <h1 class="font-display text-2xl font-black uppercase tracking-tight text-ink-900">Подтверждение email</h1>
        <Skeleton height="h-4" class="mt-6" />
        <Skeleton height="h-4" class="mt-3 w-2/3 mx-auto" />
      </template>

      <template v-else-if="status === 'success'">
        <CheckCircleIcon class="mx-auto h-12 w-12 text-success" aria-hidden="true" />
        <h1 class="mt-4 font-display text-2xl font-black uppercase tracking-tight text-ink-900">Email подтверждён</h1>
        <p class="mt-2 text-sm text-ink-600">Спасибо — теперь всё готово к записи.</p>
        <BaseButton class="mt-6 w-full" @click="router.push('/')">На главную</BaseButton>
      </template>

      <template v-else>
        <XCircleIcon class="mx-auto h-12 w-12 text-danger" aria-hidden="true" />
        <h1 class="mt-4 font-display text-2xl font-black uppercase tracking-tight text-ink-900">Ссылка недействительна</h1>
        <p class="mt-2 text-sm text-ink-600">{{ errorMessage }}</p>
        <BaseButton class="mt-6 w-full" @click="router.push('/profile')">В личный кабинет</BaseButton>
      </template>
    </BaseCard>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/vue/24/outline'
import { authApi } from '../api'
import { useAuthStore } from '../stores/auth'
import { extractErrorMessage } from '../utils/errors'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import Skeleton from '../components/ui/Skeleton.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const status = ref('loading')
const errorMessage = ref('')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    status.value = 'error'
    errorMessage.value = 'Ссылка неполная — токен подтверждения отсутствует.'
    return
  }
  try {
    await authApi.confirmEmailVerification(token)
    status.value = 'success'
    // Если ссылку открыли в той же сессии, где залогинены — освежаем user,
    // чтобы баннер "подтвердите email" пропал сразу, без ручного обновления.
    if (auth.isLoggedIn) await auth.fetchMe()
  } catch (err) {
    status.value = 'error'
    errorMessage.value = extractErrorMessage(err, 'Ссылка недействительна или уже была использована.')
  }
})
</script>
