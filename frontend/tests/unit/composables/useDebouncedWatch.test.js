import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ref, nextTick } from 'vue'
import { useDebouncedWatch } from '../../../src/composables/useDebouncedWatch'

describe('useDebouncedWatch', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('вызывает callback только после того, как источник перестал меняться', async () => {
    const source = ref('a')
    const callback = vi.fn()
    useDebouncedWatch(source, callback, 300)

    source.value = 'ab'
    await nextTick()
    vi.advanceTimersByTime(200)
    source.value = 'abc'
    await nextTick()
    vi.advanceTimersByTime(200)
    expect(callback).not.toHaveBeenCalled()

    vi.advanceTimersByTime(100)
    expect(callback).toHaveBeenCalledTimes(1)
    // oldValue — значение на момент ПОСЛЕДНЕГО срабатывания watch(), а не
    // исходное 'a': watch фиксирует новую пару (new, old) при каждом
    // изменении source, debounce лишь откладывает вызов callback.
    expect(callback).toHaveBeenCalledWith('abc', 'ab', expect.anything())
  })

  it('использует delay по умолчанию (350мс), если не передан явно', async () => {
    const source = ref(0)
    const callback = vi.fn()
    useDebouncedWatch(source, callback)

    source.value = 1
    await nextTick()
    vi.advanceTimersByTime(349)
    expect(callback).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(callback).toHaveBeenCalledTimes(1)
  })
})
