<template>
  <div class="animate-pulse rounded bg-stone-200" :class="[width, height]" aria-hidden="true" />
</template>

<script setup>
defineProps({
  width: { type: String, default: 'w-full' },
  height: { type: String, default: 'h-4' },
})
</script>
