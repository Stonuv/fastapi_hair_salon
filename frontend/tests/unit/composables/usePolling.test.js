import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { usePolling } from '../../../src/composables/usePolling'

// usePolling живёт на onMounted/onUnmounted — вызывать его вне компонента
// нельзя, поэтому каждый тест монтирует пустышку с нужным callback.
function mountWithPolling(callback, intervalMs = 1000) {
  const component = defineComponent({
    setup() {
      usePolling(callback, intervalMs)
      return () => h('div')
    },
  })
  return mount(component)
}

function setHidden(hidden) {
  Object.defineProperty(document, 'hidden', { value: hidden, configurable: true })
  document.dispatchEvent(new Event('visibilitychange'))
}

describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    Object.defineProperty(document, 'hidden', { value: false, configurable: true })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('вызывает callback каждый интервал, но не сразу при монтировании', async () => {
    const callback = vi.fn().mockResolvedValue(undefined)
    mountWithPolling(callback)

    // onMounted только заводит таймер: первую загрузку делает сам компонент.
    expect(callback).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(1000)
    expect(callback).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1000)
    expect(callback).toHaveBeenCalledTimes(2)
  })

  it('не запускает следующий вызов, пока не завершился предыдущий', async () => {
    let resolveCall
    const callback = vi.fn(() => new Promise((resolve) => { resolveCall = resolve }))
    mountWithPolling(callback)

    await vi.advanceTimersByTimeAsync(1000)
    expect(callback).toHaveBeenCalledTimes(1)

    // Интервал прошёл дважды, а ответ на первый запрос всё ещё не пришёл —
    // параллельного второго быть не должно.
    await vi.advanceTimersByTimeAsync(2000)
    expect(callback).toHaveBeenCalledTimes(1)

    resolveCall()
    await vi.advanceTimersByTimeAsync(1000)
    expect(callback).toHaveBeenCalledTimes(2)
  })

  it('молчит на скрытой вкладке и обновляет сразу при возврате', async () => {
    const callback = vi.fn().mockResolvedValue(undefined)
    mountWithPolling(callback)

    setHidden(true)
    await vi.advanceTimersByTimeAsync(5000)
    expect(callback).not.toHaveBeenCalled()

    setHidden(false)
    await vi.advanceTimersByTimeAsync(0)
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('перестаёт опрашивать после размонтирования', async () => {
    const callback = vi.fn().mockResolvedValue(undefined)
    const wrapper = mountWithPolling(callback)

    await vi.advanceTimersByTimeAsync(1000)
    expect(callback).toHaveBeenCalledTimes(1)

    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(5000)
    expect(callback).toHaveBeenCalledTimes(1)
  })

  it('не роняет цикл, если callback упал', async () => {
    const callback = vi.fn()
      .mockRejectedValueOnce(new Error('сеть моргнула'))
      .mockResolvedValue(undefined)
    mountWithPolling(callback)

    await vi.advanceTimersByTimeAsync(1000)
    expect(callback).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(1000)
    expect(callback).toHaveBeenCalledTimes(2)
  })
})
