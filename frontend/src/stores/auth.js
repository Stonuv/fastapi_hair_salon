import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user  = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isClient   = computed(() => user.value?.role === 'client')

  async function register(data) {
    const res = await authApi.register(data)
    _setSession(res.data)
  }

  async function login(data) {
    const res = await authApi.login(data)
    _setSession(res.data)
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await authApi.me()
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value  = null
    localStorage.removeItem('token')
  }

  function _setSession(data) {
    token.value = data.access_token
    user.value  = data.user
    localStorage.setItem('token', data.access_token)
  }

  return { token, user, isLoggedIn, isClient, register, login, fetchMe, logout }
})
