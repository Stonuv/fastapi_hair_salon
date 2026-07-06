import { defineStore } from 'pinia'
import { ref } from 'vue'
import { setupApi } from '../api'

/**
 * Статус визарда первого запуска: показывать ли /setup вместо обычных
 * страниц. completed по умолчанию true (fail-open) — сетевая ошибка при
 * проверке не должна заблокировать доступ к уже настроенному сайту.
 */
export const useSetupStore = defineStore('setup', () => {
  const completed = ref(true)
  const requiresToken = ref(false)
  const checked = ref(false)

  async function checkStatus() {
    try {
      const { data } = await setupApi.status()
      completed.value = data.completed
      requiresToken.value = data.requires_token
    } catch {
      completed.value = true
    } finally {
      checked.value = true
    }
  }

  function markCompleted() {
    completed.value = true
  }

  return { completed, requiresToken, checked, checkStatus, markCompleted }
})
