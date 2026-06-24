<template>
  <router-link
    :to="to"
    class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-white/80 transition-colors duration-200 hover:bg-white/10 hover:text-white"
    active-class="bg-white/15 text-white"
  >
    <component :is="icon" class="h-5 w-5" aria-hidden="true" />
    <span>{{ label }}</span>
  </router-link>
</template>

<script setup>
defineProps({
  to: [String, Object],
  label: String,
  icon: [Object, Function],
})
</script>
