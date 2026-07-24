import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../../src/api', () => ({
  authApi: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
    updateMe: vi.fn(),
  },
}))

import { authApi } from '../../../src/api'
import { useAuthStore } from '../../../src/stores/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('изначально пользователь не залогинен', () => {
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(false)
    expect(store.ready).toBe(false)
  })

  it('login сохраняет пользователя из ответа сервера', async () => {
    authApi.login.mockResolvedValue({ data: { user: { id: '1', role: 'client' } } })
    const store = useAuthStore()
    await store.login({ email: 'a@b.com', password: 'x' })
    expect(store.isLoggedIn).toBe(true)
    expect(store.isClient).toBe(true)
  })

  it('роль вычисляется через isClient/isMaster/isAdmin', async () => {
    authApi.login.mockResolvedValue({ data: { user: { id: '1', role: 'master' } } })
    const store = useAuthStore()
    await store.login({})
    expect(store.isMaster).toBe(true)
    expect(store.isClient).toBe(false)
    expect(store.isAdmin).toBe(false)
  })

  it('fetchMe при 401 очищает сессию, но проставляет ready', async () => {
    authApi.me.mockRejectedValue({ response: { status: 401 } })
    const store = useAuthStore()
    store.user = { id: '1', role: 'client' }
    await store.fetchMe()
    expect(store.user).toBeNull()
    expect(store.ready).toBe(true)
  })

  it('fetchMe при сетевой ошибке (без response) не стирает валидную сессию', async () => {
    authApi.me.mockRejectedValue(new Error('Network Error'))
    const store = useAuthStore()
    store.user = { id: '1', role: 'client' }
    await store.fetchMe()
    expect(store.user).toEqual({ id: '1', role: 'client' })
    expect(store.ready).toBe(true)
  })

  it('logout очищает сессию даже если запрос на сервер упал', async () => {
    authApi.logout.mockRejectedValue(new Error('offline'))
    const store = useAuthStore()
    store.user = { id: '1', role: 'client' }
    // logout() не глотает ошибку сервера (нет catch, только finally) — она
    // должна долететь до вызывающего кода, но сессия обязана очиститься.
    await expect(store.logout()).rejects.toThrow('offline')
    expect(store.user).toBeNull()
  })
})
