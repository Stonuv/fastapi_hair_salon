import { defineStore } from 'pinia'
import { ref } from 'vue'

let nextId = 1

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function push(message, variant = 'info', duration = 4000) {
    const id = nextId++
    toasts.value.push({ id, message, variant })
    if (duration > 0) {
      setTimeout(() => dismiss(id), duration)
    }
    return id
  }

  function dismiss(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  const success = (message) => push(message, 'success')
  const error = (message) => push(message, 'error')
  const info = (message) => push(message, 'info')

  return { toasts, push, dismiss, success, error, info }
})
