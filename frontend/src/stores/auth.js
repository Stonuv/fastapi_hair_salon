import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  // Токен живёт в httpOnly-cookie, а не здесь — из JS он недоступен и не
  // читается (см. README «Осознанные компромиссы безопасности»). Сессия
  // определяется исключительно наличием user: null/не-null.
  const user = ref(null)
  const ready = ref(false)

  const isLoggedIn = computed(() => !!user.value)
  const isClient = computed(() => user.value?.role === 'client')
  const isMaster = computed(() => user.value?.role === 'master')
  // owner — надмножество admin (ROADMAP.md §4.1): отдельного дерева /owner/*
  // нет, панель одна. isAdmin отвечает на «пускать ли в админку», isOwner —
  // на «можно ли трогать сетевые сущности» (настройки сайта, каталог услуг,
  // список точек), которые с Фазы C доступны только владельцу сети.
  const isOwner = computed(() => user.value?.role === 'owner')
  const isAdmin = computed(() => user.value?.role === 'admin' || isOwner.value)
  // Домашняя точка admin'а; у owner её нет — он видит всю сеть.
  const salon = computed(() => user.value?.salon ?? null)

  async function register(data) {
    const res = await authApi.register(data)
    user.value = res.data.user
  }

  async function login(data) {
    const res = await authApi.login(data)
    user.value = res.data.user
  }

  async function fetchMe() {
    // Cookie httpOnly — из JS не видна, поэтому всегда спрашиваем сервер
    // один раз при загрузке; guard в роутере ждёт этого через ready.
    try {
      const res = await authApi.me()
      user.value = res.data
    } catch (err) {
      // Разлогиниваем локально только если токен действительно отвергнут
      // (401). Сетевая ошибка или 500 не повод стирать валидную сессию.
      if (err.response?.status === 401) clearSession()
    } finally {
      ready.value = true
    }
  }

  async function updateMe(data) {
    const res = await authApi.updateMe(data)
    user.value = res.data
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      clearSession()
    }
  }

  function clearSession() {
    user.value = null
  }

  return {
    user, ready,
    isLoggedIn, isClient, isMaster, isAdmin, isOwner, salon,
    register, login, fetchMe, updateMe, logout, clearSession,
  }
})
