<template>
  <header class="sticky top-0 z-20 border-b border-stone-200 bg-stone-50/50 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
      <router-link to="/" class="flex items-baseline gap-2.5">
        <span class="font-display text-xl font-black uppercase tracking-tight text-ink-900">{{ content.header.brand_name }}</span>
        <span class="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-600">{{ content.header.brand_tagline }}</span>
      </router-link>

      <nav class="hidden items-center gap-8 sm:flex">
        <router-link
          :to="{ name: 'masters' }"
          class="font-mono text-xs uppercase tracking-wide text-ink-900 transition-colors duration-200 hover:text-brand-700"
          active-class="text-brand-700"
        >Мастера</router-link>
        <router-link
          v-if="auth.isAdmin"
          to="/admin"
          class="font-mono text-xs uppercase tracking-wide text-ink-900 transition-colors duration-200 hover:text-brand-700"
          active-class="text-brand-700"
        >Админ-панель</router-link>
        <router-link
          v-if="auth.isMaster"
          to="/dashboard"
          class="font-mono text-xs uppercase tracking-wide text-ink-900 transition-colors duration-200 hover:text-brand-700"
          active-class="text-brand-700"
        >Кабинет мастера</router-link>
      </nav>

      <div class="flex items-center gap-3">
        <template v-if="auth.isLoggedIn">
          <router-link
            to="/profile"
            class="flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-ink-900 transition-colors duration-200 hover:text-brand-700"
          >
            <UserCircleIcon class="h-6 w-6 text-ink-900" aria-hidden="true" />
            <span class="hidden sm:inline">{{ auth.user?.first_name }}</span>
          </router-link>
          <BaseButton variant="ghost" size="sm" @click="handleLogout">Выйти</BaseButton>
        </template>
        <template v-else>
          <router-link to="/login" class="font-mono text-xs uppercase tracking-wide text-ink-900 hover:text-brand-700">Войти</router-link>
          <router-link to="/register">
            <BaseButton variant="primary" size="sm">Записаться ↗</BaseButton>
          </router-link>
        </template>
      </div>
    </div>

    <nav class="flex items-center gap-4 overflow-x-auto border-t border-stone-200 px-4 py-2 sm:hidden">
      <router-link :to="{ name: 'masters' }" class="whitespace-nowrap font-mono text-xs uppercase tracking-wide text-ink-900" active-class="text-brand-700">Мастера</router-link>
      <router-link v-if="auth.isAdmin" to="/admin" class="whitespace-nowrap font-mono text-xs uppercase tracking-wide text-ink-900" active-class="text-brand-700">Админ</router-link>
      <router-link v-if="auth.isMaster" to="/dashboard" class="whitespace-nowrap font-mono text-xs uppercase tracking-wide text-ink-900" active-class="text-brand-700">Кабинет</router-link>
    </nav>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { UserCircleIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '../stores/auth'
import { useSiteContentStore } from '../stores/siteContent'
import BaseButton from './ui/BaseButton.vue'

const auth = useAuthStore()
const router = useRouter()
const { content } = storeToRefs(useSiteContentStore())

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
