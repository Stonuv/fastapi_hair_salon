import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import client, { setServerErrorHandler } from '../../../src/api/client'

// Перехватчики axios работают вокруг адаптера, поэтому подмена адаптера —
// самый прямой способ проверить их без сети и без мок-библиотек: адаптер
// отвечает тем, что нужно тесту, а сам перехватчик остаётся настоящим.
function respondWith(response) {
  client.defaults.adapter = (config) =>
    Promise.reject(Object.assign(new Error('mock'), { config, response }))
}

describe('перехватчик 5xx в api/client', () => {
  let onServerError
  let originalAdapter

  beforeEach(() => {
    originalAdapter = client.defaults.adapter
    onServerError = vi.fn()
    setServerErrorHandler(onServerError)
  })

  afterEach(() => {
    client.defaults.adapter = originalAdapter
    setServerErrorHandler(null)
  })

  it('зовёт обработчик на 500', async () => {
    respondWith({ status: 500, data: { detail: 'Внутренняя ошибка сервера. Попробуйте позже.' } })
    await expect(client.get('/admin/stats')).rejects.toBeTruthy()
    expect(onServerError).toHaveBeenCalledTimes(1)
  })

  it('зовёт обработчик на 502 — упавший бэкенд за прокси выглядит так же', async () => {
    respondWith({ status: 502, data: '' })
    await expect(client.get('/admin/stats')).rejects.toBeTruthy()
    expect(onServerError).toHaveBeenCalledTimes(1)
  })

  it('молчит на фоновом запросе: автообновление не должно уводить со страницы', async () => {
    respondWith({ status: 500, data: {} })
    await expect(client.get('/admin/stats', { background: true })).rejects.toBeTruthy()
    expect(onServerError).not.toHaveBeenCalled()
  })

  it('молчит на 4xx — это ошибка запроса, её показывает сама форма', async () => {
    respondWith({ status: 422, data: { detail: 'Неверный формат' } })
    await expect(client.post('/appointments', {})).rejects.toBeTruthy()
    expect(onServerError).not.toHaveBeenCalled()
  })

  it('молчит на сетевой ошибке: офлайн — не повод терять заполненную форму', async () => {
    client.defaults.adapter = (config) =>
      Promise.reject(Object.assign(new Error('Network Error'), { config, response: undefined }))
    await expect(client.post('/appointments', {})).rejects.toBeTruthy()
    expect(onServerError).not.toHaveBeenCalled()
  })
})
