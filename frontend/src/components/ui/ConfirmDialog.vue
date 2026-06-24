<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" @click="close" />
      <div class="relative w-full max-w-md border border-stone-200 bg-white p-6 shadow-lg" role="dialog" aria-modal="true">
        <h2 class="font-display text-lg font-bold text-ink-900">{{ title }}</h2>
        <p class="mt-2 text-sm text-ink-600">{{ message }}</p>
        <div class="mt-6 flex justify-end gap-3">
          <BaseButton variant="ghost" size="sm" @click="close">Отмена</BaseButton>
          <BaseButton :variant="danger ? 'danger' : 'primary'" size="sm" :loading="loading" @click="$emit('confirm')">
            {{ confirmLabel }}
          </BaseButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import BaseButton from './BaseButton.vue'

defineProps({
  open: Boolean,
  title: String,
  message: String,
  confirmLabel: { type: String, default: 'Подтвердить' },
  danger: Boolean,
  loading: Boolean,
})
const emit = defineEmits(['confirm', 'update:open'])

function close() {
  emit('update:open', false)
}
</script>
