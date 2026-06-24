<template>
  <div class="fixed bottom-4 right-4 z-40 flex w-full max-w-sm flex-col gap-2" aria-live="polite">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        role="status"
        class="flex items-start gap-3 rounded-lg border bg-white p-4 shadow-lg"
        :class="variantClasses[toast.variant]"
      >
        <component :is="icon(toast.variant)" class="h-5 w-5 flex-shrink-0" aria-hidden="true" />
        <p class="flex-1 text-sm">{{ toast.message }}</p>
        <button
          class="cursor-pointer opacity-60 hover:opacity-100"
          aria-label="Закрыть уведомление"
          @click="store.dismiss(toast.id)"
        >
          <XMarkIcon class="h-4 w-4" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/solid'
import { useToastStore } from '../../stores/toast'

const store = useToastStore()
const { toasts } = storeToRefs(store)

const variantClasses = {
  success: 'border-success/30 text-success',
  error: 'border-danger/30 text-danger',
  info: 'border-brand-900/20 text-ink-900',
}

function icon(variant) {
  if (variant === 'success') return CheckCircleIcon
  if (variant === 'error') return ExclamationCircleIcon
  return InformationCircleIcon
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 200ms ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
