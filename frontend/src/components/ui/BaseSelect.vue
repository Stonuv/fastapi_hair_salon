<template>
  <div>
    <label v-if="label" :for="inputId" class="mb-1.5 block text-sm font-medium text-ink-900">{{ label }}</label>
    <select
      :id="inputId"
      :value="modelValue"
      class="w-full cursor-pointer rounded-lg border border-stone-200 bg-white px-3.5 py-2.5 text-base transition-colors duration-200 focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <slot />
    </select>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: [String, Number],
  label: String,
  placeholder: String,
  id: String,
})
defineEmits(['update:modelValue'])
const inputId = props.id || `select-${Math.random().toString(36).slice(2, 9)}`
</script>
