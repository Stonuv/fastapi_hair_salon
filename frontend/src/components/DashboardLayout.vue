<template>
  <div class="flex min-h-screen bg-stone-50">
    <aside class="hidden w-64 flex-col bg-brand-900 text-white lg:flex">
      <div class="px-6 py-5">
        <router-link to="/" class="font-display text-lg font-black uppercase tracking-tight">Сайтама</router-link>
      </div>
      <nav class="flex-1 space-y-1 px-3">
        <slot name="nav" />
      </nav>
      <div class="border-t border-white/10 p-3">
        <button
          class="flex w-full cursor-pointer items-center gap-2 px-3 py-2 font-mono text-xs uppercase tracking-wide text-white/80 transition-colors duration-200 hover:bg-white/10"
          @click="handleLogout"
        >
          <ArrowLeftOnRectangleIcon class="h-5 w-5" aria-hidden="true" />
          Выйти
        </button>
      </div>
    </aside>

    <Teleport to="body">
      <div v-if="mobileOpen" class="fixed inset-0 z-30 lg:hidden">
        <div class="absolute inset-0 bg-ink-900/40" @click="mobileOpen = false" />
        <aside class="absolute inset-y-0 left-0 flex w-64 flex-col bg-brand-900 text-white">
          <div class="flex items-center justify-between px-6 py-5">
            <span class="font-display text-lg font-black uppercase tracking-tight">Сайтама</span>
            <button class="cursor-pointer" aria-label="Закрыть меню" @click="mobileOpen = false">
              <XMarkIcon class="h-6 w-6" aria-hidden="true" />
            </button>
          </div>
          <nav class="flex-1 space-y-1 px-3" @click="mobileOpen = false">
            <slot name="nav" />
          </nav>
        </aside>
      </div>
    </Teleport>

    <div class="flex flex-1 flex-col">
      <header class="flex items-center justify-between border-b border-stone-200 bg-white px-4 py-4 sm:px-6">
        <div class="flex items-center gap-3">
          <button class="cursor-pointer text-ink-900 lg:hidden" aria-label="Открыть меню" @click="mobileOpen = true">
            <Bars3Icon class="h-6 w-6" aria-hidden="true" />
          </button>
          <h1 class="font-display text-xl font-bold uppercase tracking-tight text-ink-900">{{ title }}</h1>
        </div>
        <router-link to="/profile" class="flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-ink-900 hover:text-brand-700">
          <UserCircleIcon class="h-6 w-6 text-ink-900" aria-hidden="true" />
          <span class="hidden sm:inline">{{ auth.user?.first_name }}</span>
        </router-link>
      </header>
      <main class="flex-1 p-4 sm:p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bars3Icon, XMarkIcon, UserCircleIcon, ArrowLeftOnRectangleIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '../stores/auth'

defineProps({ title: String })

const mobileOpen = ref(false)
const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
