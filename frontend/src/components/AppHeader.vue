<template>
  <header class="sticky top-0 z-20 border-b border-stone-200 bg-white/90 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
      <router-link to="/" class="font-display text-xl font-bold text-brand-900">Сайтама</router-link>

      <nav class="hidden items-center gap-6 sm:flex">
        <router-link
          to="/"
          class="text-sm font-medium text-ink-600 transition-colors duration-200 hover:text-brand-900"
          active-class="text-brand-900"
        >Мастера</router-link>
        <router-link
          v-if="auth.isAdmin"
          to="/admin"
          class="text-sm font-medium text-ink-600 transition-colors duration-200 hover:text-brand-900"
          active-class="text-brand-900"
        >Админ-панель</router-link>
        <router-link
          v-if="auth.isMaster"
          to="/dashboard"
          class="text-sm font-medium text-ink-600 transition-colors duration-200 hover:text-brand-900"
          active-class="text-brand-900"
        >Кабинет мастера</router-link>
      </nav>

      <div class="flex items-center gap-3">
        <template v-if="auth.isLoggedIn">
          <router-link
            to="/profile"
            class="flex items-center gap-2 text-sm font-medium text-ink-900 transition-colors duration-200 hover:text-brand-900"
          >
            <UserCircleIcon class="h-6 w-6 text-brand-900" aria-hidden="true" />
            <span class="hidden sm:inline">{{ auth.user?.first_name }}</span>
          </router-link>
          <BaseButton variant="ghost" size="sm" @click="handleLogout">Выйти</BaseButton>
        </template>
        <template v-else>
          <router-link to="/login" class="text-sm font-medium text-ink-600 hover:text-brand-900">Войти</router-link>
          <router-link to="/register">
            <BaseButton variant="primary" size="sm">Регистрация</BaseButton>
          </router-link>
        </template>
      </div>
    </div>

    <nav class="flex items-center gap-4 overflow-x-auto border-t border-stone-200 px-4 py-2 sm:hidden">
      <router-link to="/" class="whitespace-nowrap text-sm font-medium text-ink-600" active-class="text-brand-900">Мастера</router-link>
      <router-link v-if="auth.isAdmin" to="/admin" class="whitespace-nowrap text-sm font-medium text-ink-600" active-class="text-brand-900">Админ</router-link>
      <router-link v-if="auth.isMaster" to="/dashboard" class="whitespace-nowrap text-sm font-medium text-ink-600" active-class="text-brand-900">Кабинет</router-link>
    </nav>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { UserCircleIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '../stores/auth'
import BaseButton from './ui/BaseButton.vue'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
