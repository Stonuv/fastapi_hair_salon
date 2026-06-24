<template>
  <h2 class="mb-4 flex items-center gap-3 font-display text-lg font-bold uppercase tracking-tight text-ink-900">
    <span class="font-mono text-xs font-medium tracking-widest text-brand-700">0{{ n }}</span>
    {{ title }}
  </h2>
</template>

<script setup>
defineProps({ n: [String, Number], title: String })
</script>
