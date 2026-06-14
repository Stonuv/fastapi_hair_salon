<template>
  <AppHeader />
  <main>
    <router-view />
  </main>
</template>

<script setup>
import { onMounted } from 'vue'
import AppHeader from './components/AppHeader.vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
onMounted(() => auth.fetchMe())
</script>
