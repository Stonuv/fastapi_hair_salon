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
  <!-- На /500 тостов нет: страница уже целиком об этой ошибке, а
       перехватчик (api/client.js) уводит сюда до того, как экран-источник
       успевает показать свой тост — иначе одно и то же сообщение висело бы
       поверх страницы, которая его же и повторяет. -->
  <ToastContainer v-if="route.name !== 'server-error'" />
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import EmailVerificationBanner from './components/EmailVerificationBanner.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
import { useSiteContentStore } from './stores/siteContent'
import { useSalonStore } from './stores/salon'

const route = useRoute()
onMounted(() => {
  useSiteContentStore().load()
  // Точки нужны публичным экранам (футер, секция «Наши салоны», фильтр
  // каталога), поэтому грузятся здесь же, а не только в админке.
  useSalonStore().load()
})
</script>
