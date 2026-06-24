<template>
  <AppHeader v-if="!route.meta.hideHeader" />
  <router-view />
  <AppFooter v-if="!route.meta.hideHeader" />
  <ToastContainer />
</template>

<script setup>
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import ToastContainer from './components/ui/ToastContainer.vue'

const route = useRoute()
</script>
