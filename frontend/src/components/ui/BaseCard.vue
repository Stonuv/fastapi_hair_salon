<template>
  <div
    class="rounded-xl border border-stone-200 bg-white p-6 shadow-sm"
    :class="{ 'cursor-pointer transition-shadow duration-200 hover:shadow-md': clickable }"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({ clickable: Boolean })
</script>
