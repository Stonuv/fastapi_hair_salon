<template>
  <div class="flex items-center gap-1" role="radiogroup" aria-label="Оценка">
    <button
      v-for="i in 5"
      :key="i"
      type="button"
      class="cursor-pointer"
      role="radio"
      :aria-checked="modelValue === i"
      :aria-label="`${i} из 5`"
      @click="$emit('update:modelValue', i)"
    >
      <StarIcon class="h-7 w-7" :class="i <= modelValue ? 'text-accent-400' : 'text-stone-200'" aria-hidden="true" />
    </button>
  </div>
</template>

<script setup>
import { StarIcon } from '@heroicons/vue/24/solid'

defineProps({ modelValue: { type: Number, default: 0 } })
defineEmits(['update:modelValue'])
</script>
