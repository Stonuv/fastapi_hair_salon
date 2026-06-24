import { reactive } from 'vue'

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

  /** Best-effort mapping of FastAPI 422 validation errors onto form fields. */
  function setFromResponse(err) {
    const detail = err?.response?.data?.detail
    clearAll()
    if (Array.isArray(detail)) {
      for (const item of detail) {
        const field = item.loc?.[item.loc.length - 1]
        if (field) errors[field] = item.msg
      }
      return true
    }
    return false
  }

  return { errors, setError, clearError, clearAll, setFromResponse }
}
