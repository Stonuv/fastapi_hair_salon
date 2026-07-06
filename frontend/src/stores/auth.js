import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)
  const ready = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isClient = computed(() => user.value?.role === 'client')
  const isMaster = computed(() => user.value?.role === 'master')
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function register(data) {
    const res = await authApi.register(data)
    setSession(res.data)
  }

  async function login(data) {
    const res = await authApi.login(data)
    setSession(res.data)
  }

  async function fetchMe() {
    if (!token.value) {
      ready.value = true
      return
    }
    try {
      const res = await authApi.me()
      user.value = res.data
    } catch (err) {
      // Разлогиниваем только если токен действительно отвергнут (401).
      // Сетевая ошибка или 500 не повод стирать валидную сессию.
      if (err.response?.status === 401) logout()
    } finally {
      ready.value = true
    }
  }

  async function updateMe(data) {
    const res = await authApi.updateMe(data)
    user.value = res.data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  function setSession(data) {
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
  }

  return {
    token, user, ready,
    isLoggedIn, isClient, isMaster, isAdmin,
    register, login, fetchMe, updateMe, logout, setSession,
  }
})
