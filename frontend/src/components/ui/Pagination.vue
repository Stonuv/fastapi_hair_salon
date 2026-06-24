<template>
  <div v-if="totalPages > 1" class="flex items-center justify-between gap-4 pt-4">
    <p class="text-sm text-ink-600">Страница {{ page }} из {{ totalPages }}</p>
    <div class="flex gap-2">
      <BaseButton variant="ghost" size="sm" :disabled="page <= 1" @click="$emit('update:page', page - 1)">
        Назад
      </BaseButton>
      <BaseButton variant="ghost" size="sm" :disabled="page >= totalPages" @click="$emit('update:page', page + 1)">
        Далее
      </BaseButton>
    </div>
  </div>
</template>

<script setup>
import BaseButton from './BaseButton.vue'

defineProps({
  page: { type: Number, required: true },
  totalPages: { type: Number, required: true },
})
defineEmits(['update:page'])
</script>
