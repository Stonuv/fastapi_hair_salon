<template>
  <template v-if="enabled">
    <div class="my-4 flex items-center gap-3 text-xs uppercase tracking-wider text-ink-400">
      <span class="h-px flex-1 bg-ink-200" />
      или
      <span class="h-px flex-1 bg-ink-200" />
    </div>
    <BaseButton variant="ghost" class="w-full" type="button" @click="goToVk">
      <span class="flex h-4 w-4 items-center justify-center rounded-sm bg-[#0077FF] text-[10px] font-bold text-white">VK</span>
      Войти через VK
    </BaseButton>
  </template>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { authApi } from '../../api'
import { useToastStore } from '../../stores/toast'
import BaseButton from './BaseButton.vue'

// requireConsent/consented — на /register нужно согласие на обработку ПДн
// до ухода на VK (клик сразу же уводит браузер на id.vk.com, отдельного
// шага подтверждения внутри приложения после этого уже не будет). На
// /login эти пропсы не передаются — там это не первичный сбор данных.
const props = defineProps({
  requireConsent: { type: Boolean, default: false },
  consented: { type: Boolean, default: true },
})

const enabled = ref(false)
const toast = useToastStore()

onMounted(async () => {
  try {
    const res = await authApi.vkEnabled()
    enabled.value = !!res.data?.enabled
  } catch {
    enabled.value = false
  }
})

function goToVk() {
  if (props.requireConsent && !props.consented) {
    toast.error('Подтвердите согласие на обработку персональных данных')
    return
  }
  // Полная навигация, а не axios-запрос: серверу нужно поставить httpOnly
  // cookie (state/verifier) и сделать редирект на id.vk.com — это должен
  // делать сам браузер, а не fetch/XHR.
  window.location.href = '/api/auth/vk/login'
}
</script>
