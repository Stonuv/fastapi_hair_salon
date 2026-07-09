<template>
  <span v-if="editable" v-bind="$attrs"><slot /></span>
  <router-link v-else-if="to" :to="to" v-bind="$attrs"><slot /></router-link>
  <a v-else :href="href" v-bind="$attrs"><slot /></a>
</template>

<script setup>
defineOptions({ inheritAttrs: false })
defineProps({
  to: { type: [String, Object], default: null },
  href: { type: String, default: null },
  editable: { type: Boolean, default: false },
})
</script>
