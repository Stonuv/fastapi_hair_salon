<template>
  <div>
    <label v-if="label" :for="inputId" class="mb-1.5 block text-sm font-medium text-ink-900">
      {{ label }} <span v-if="required" class="text-danger">*</span>
    </label>
    <textarea
      v-if="as === 'textarea'"
      :id="inputId"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :rows="rows"
      :lang="lang"
      class="w-full rounded-lg border px-3.5 py-2.5 text-base transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
      :class="error ? 'border-danger focus:border-danger' : 'border-stone-200 focus:border-brand-900'"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur')"
    />
    <input
      v-else
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :autocomplete="autocomplete"
      :min="min"
      :max="max"
      :step="step"
      :lang="lang"
      class="w-full rounded-lg border px-3.5 py-2.5 text-base transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
      :class="error ? 'border-danger focus:border-danger' : 'border-stone-200 focus:border-brand-900'"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur')"
    />
    <p v-if="error" class="mt-1 text-sm text-danger">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-sm text-ink-600/80">{{ hint }}</p>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: [String, Number],
  label: String,
  type: { type: String, default: 'text' },
  as: { type: String, default: 'input' },
  rows: { type: [String, Number], default: 3 },
  error: String,
  hint: String,
  placeholder: String,
  required: Boolean,
  autocomplete: String,
  id: String,
  min: [String, Number],
  max: [String, Number],
  step: [String, Number],
  lang: { type: String, default: 'ru' },
})
defineEmits(['update:modelValue', 'blur'])

const inputId = props.id || `input-${Math.random().toString(36).slice(2, 9)}`
</script>
