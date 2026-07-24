import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useToastStore } from '../../../src/stores/toast'

describe('useToastStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  it('push добавляет тост и возвращает его id', () => {
    const store = useToastStore()
    const id = store.push('Готово', 'success')
    expect(store.toasts).toHaveLength(1)
    expect(store.toasts[0]).toMatchObject({ id, message: 'Готово', variant: 'success' })
  })

  it('success/error/info проставляют вариант автоматически', () => {
    const store = useToastStore()
    store.success('ok')
    store.error('bad')
    store.info('fyi')
    expect(store.toasts.map((t) => t.variant)).toEqual(['success', 'error', 'info'])
  })

  it('тост исчезает сам по себе после duration', () => {
    const store = useToastStore()
    store.push('Временный', 'info', 1000)
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(999)
    expect(store.toasts).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(store.toasts).toHaveLength(0)
  })

  it('duration=0 — тост остаётся, пока не вызван dismiss явно', () => {
    const store = useToastStore()
    const id = store.push('Постоянный', 'error', 0)
    vi.advanceTimersByTime(10_000)
    expect(store.toasts).toHaveLength(1)
    store.dismiss(id)
    expect(store.toasts).toHaveLength(0)
  })
})
