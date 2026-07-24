import { describe, it, expect } from 'vitest'
import { useFormErrors } from '../../../src/composables/useFormErrors'

describe('useFormErrors', () => {
  it('setError/clearError управляют одним полем', () => {
    const { errors, setError, clearError } = useFormErrors()
    setError('email', 'Неверный формат')
    expect(errors.email).toBe('Неверный формат')
    clearError('email')
    expect(errors.email).toBeUndefined()
  })

  it('clearAll сбрасывает все поля разом', () => {
    const { errors, setError, clearAll } = useFormErrors()
    setError('email', 'x')
    setError('phone', 'y')
    clearAll()
    expect(Object.keys(errors)).toHaveLength(0)
  })

  it('setFromResponse раскладывает 422 detail[] по полям и возвращает true', () => {
    const { errors, setFromResponse } = useFormErrors()
    const handled = setFromResponse({
      response: { data: { detail: [{ type: 'missing', loc: ['body', 'phone'] }] } },
    })
    expect(handled).toBe(true)
    expect(errors.phone).toBe('Обязательное поле')
  })

  it('setFromResponse возвращает false и очищает старые ошибки, если detail не массив (напр. строка/500)', () => {
    const { errors, setError, setFromResponse } = useFormErrors()
    setError('email', 'старая ошибка')
    const handled = setFromResponse({ response: { data: { detail: 'Внутренняя ошибка сервера' } } })
    expect(handled).toBe(false)
    expect(errors.email).toBeUndefined()
  })

  it('повторный setFromResponse очищает ошибки от предыдущего вызова', () => {
    const { errors, setFromResponse } = useFormErrors()
    setFromResponse({ response: { data: { detail: [{ type: 'missing', loc: ['body', 'phone'] }] } } })
    setFromResponse({ response: { data: { detail: [{ type: 'missing', loc: ['body', 'email'] }] } } })
    expect(errors.phone).toBeUndefined()
    expect(errors.email).toBe('Обязательное поле')
  })
})
