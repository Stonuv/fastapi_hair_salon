<template>
  <h2 class="mb-4 flex items-center gap-3 font-display text-lg font-bold text-ink-900">
    <span class="font-sans text-xs font-semibold tracking-widest text-brand-700">0{{ n }}</span>
    {{ title }}
  </h2>
</template>

<script setup>
defineProps({ n: [String, Number], title: String })
</script>
