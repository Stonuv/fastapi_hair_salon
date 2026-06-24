<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium transition-colors duration-200 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
    :class="[variants[variant] ?? variants.primary, sizes[size] ?? sizes.md]"
  >
    <svg v-if="loading" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  loading: Boolean,
  disabled: Boolean,
  type: { type: String, default: 'button' },
})

const variants = {
  primary: 'bg-brand-900 text-white hover:bg-brand-800',
  accent: 'bg-accent-400 text-ink-900 hover:brightness-95',
  ghost: 'bg-transparent text-brand-900 border border-brand-900/30 hover:bg-brand-900/5',
  danger: 'bg-danger text-white hover:brightness-90',
}
const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2.5 text-base',
}
</script>
