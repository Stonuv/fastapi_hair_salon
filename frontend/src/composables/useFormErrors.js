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

  /** Мост к utils/validators.js: пустая строка от валидатора снимает ошибку
   * поля, непустая -- ставит. Возвращает true для валидного поля, чтобы
   * validateAll() складывалась из вызовов проверок, а не из ручных проверок
   * Object.keys(errors) после них. */
  function setOrClear(field, message) {
    if (message) {
      errors[field] = message
      return false
    }
    delete errors[field]
    return true
  }

  /** Все проверки формы разом (перед отправкой): вызывает каждую функцию и
   * возвращает true, только если валидны все поля. Через reduce, а не
   * every(): every останавливается на первой ошибке и подсветил бы лишь
   * одно поле из нескольких неверных. */
  function validateAll(...checks) {
    return checks.reduce((ok, check) => check() && ok, true)
  }

  /** Best-effort mapping of FastAPI 422 validation errors onto form fields —
   * см. friendlyValidationError (utils/errors.js) за переводом технического
   * item.msg в понятный русский текст, без сырых regex/имён типов.
   * Возвращает true, только если хотя бы одно поле подсветилось: 422 может
   * прийти и по query-параметру, которого на форме нет, -- тогда вызывающий
   * должен показать тост, иначе ошибка исчезнет бесследно. */
  function setFromResponse(err) {
    const detail = err?.response?.data?.detail
    clearAll()
    if (!Array.isArray(detail)) return false
    let mapped = 0
    for (const item of detail) {
      const { field, message } = friendlyValidationError(item)
      // loc ['body'] -- ошибка тела целиком (model_validator: «close_time
      // должен быть позже open_time» и подобные), а не отдельного поля:
      // подсветить нечего, пусть вызывающий покажет её тостом.
      if (field && field !== 'body') {
        errors[field] = message
        mapped += 1
      }
    }
    return mapped > 0
  }

  return { errors, setError, clearError, clearAll, setOrClear, validateAll, setFromResponse }
}
