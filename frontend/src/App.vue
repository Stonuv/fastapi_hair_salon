<template>
  <EmailVerificationBanner />
  <AppHeader v-if="!route.meta.hideHeader" />
  <!-- hideHeader-страницы (setup/dashboard/admin) управляют собственным
       landmark-разметкой (напр. DashboardLayout.vue уже содержит <main>) —
       обернуть их ещё раз означало бы вложенные <main>, invalid HTML. -->
  <main v-if="!route.meta.hideHeader">
    <router-view />
  </main>
  <router-view v-else />
  <AppFooter v-if="!route.meta.hideHeader" />
  <ToastContainer />
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import EmailVerificationBanner from './components/EmailVerificationBanner.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
import { useSiteContentStore } from './stores/siteContent'

const route = useRoute()
onMounted(() => useSiteContentStore().load())
</script>
