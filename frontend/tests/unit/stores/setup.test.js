import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../../src/api', () => ({
  setupApi: { status: vi.fn() },
}))

import { setupApi } from '../../../src/api'
import { useSetupStore } from '../../../src/stores/setup'

describe('useSetupStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('completed по умолчанию true — fail-open до первой проверки', () => {
    const store = useSetupStore()
    expect(store.completed).toBe(true)
    expect(store.checked).toBe(false)
  })

  it('checkStatus применяет ответ сервера', async () => {
    setupApi.status.mockResolvedValue({ data: { completed: false, requires_token: true } })
    const store = useSetupStore()
    await store.checkStatus()
    expect(store.completed).toBe(false)
    expect(store.requiresToken).toBe(true)
    expect(store.checked).toBe(true)
  })

  it('сетевая ошибка при проверке — fail-open, completed остаётся true', async () => {
    setupApi.status.mockRejectedValue(new Error('offline'))
    const store = useSetupStore()
    await store.checkStatus()
    expect(store.completed).toBe(true)
    expect(store.checked).toBe(true)
  })

  it('markCompleted принудительно закрывает визард', () => {
    const store = useSetupStore()
    store.completed = false
    store.markCompleted()
    expect(store.completed).toBe(true)
  })
})
