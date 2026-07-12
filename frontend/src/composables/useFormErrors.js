import { reactive } from 'vue'
import { friendlyValidationError } from '../utils/errors'

export function useFormErrors() {
  const errors = reactive({})

  function setError(field, message) {
    errors[field] = message
  }

  function clearError(field) {
    delete errors[field]
  }

  function clearAll() {
    Object.keys(errors).forEach((key) => delete errors[key])
  }

  /** Best-effort mapping of FastAPI 422 validation errors onto form fields —
   * см. friendlyValidationError (utils/errors.js) за переводом технического
   * item.msg в понятный русский текст, без сырых regex/имён типов. */
  function setFromResponse(err) {
    const detail = err?.response?.data?.detail
    clearAll()
    if (Array.isArray(detail)) {
      for (const item of detail) {
        const { field, message } = friendlyValidationError(item)
        if (field) errors[field] = message
      }
      return true
    }
    return false
  }

  return { errors, setError, clearError, clearAll, setFromResponse }
}
