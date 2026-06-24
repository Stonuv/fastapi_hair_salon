<template>
  <div
    class="border border-stone-200 bg-white p-6"
    :class="{ 'cursor-pointer transition-colors duration-200 hover:border-brand-900': clickable }"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({ clickable: Boolean })
</script>
