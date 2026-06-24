<template>
  <div class="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-stone-200 bg-white/60 p-10 text-center">
    <component :is="icon" v-if="icon" class="h-10 w-10 text-ink-600/40" aria-hidden="true" />
    <p class="font-medium text-ink-900">{{ title }}</p>
    <p v-if="description" class="max-w-sm text-sm text-ink-600">{{ description }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: String,
  description: String,
  icon: [Object, Function],
})
</script>
