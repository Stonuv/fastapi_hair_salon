<template>
  <label class="inline-flex cursor-pointer items-center gap-2 select-none">
    <span class="relative inline-flex h-5 w-5 flex-shrink-0 items-center justify-center">
      <input
        :id="inputId"
        type="checkbox"
        class="peer h-5 w-5 shrink-0 cursor-pointer appearance-none rounded border border-stone-300 bg-white transition-colors duration-150 checked:border-brand-900 checked:bg-brand-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900/50"
        :checked="modelValue"
        @change="$emit('update:modelValue', $event.target.checked)"
      />
      <CheckIcon
        class="pointer-events-none absolute h-3.5 w-3.5 text-white opacity-0 peer-checked:opacity-100"
        aria-hidden="true"
      />
    </span>
    <span v-if="$slots.default"><slot /></span>
  </label>
</template>

<script setup>
import { CheckIcon } from '@heroicons/vue/24/solid'

const props = defineProps({
  modelValue: Boolean,
  id: String,
})
defineEmits(['update:modelValue'])

const inputId = props.id || `checkbox-${Math.random().toString(36).slice(2, 9)}`
</script>
