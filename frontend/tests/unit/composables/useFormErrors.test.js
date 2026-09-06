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

  it('setOrClear ставит ошибку по непустому тексту и снимает по пустому', () => {
    const { errors, setOrClear } = useFormErrors()
    expect(setOrClear('email', 'Некорректный email')).toBe(false)
    expect(errors.email).toBe('Некорректный email')
    expect(setOrClear('email', '')).toBe(true)
    expect(errors.email).toBeUndefined()
  })

  it('validateAll вызывает все проверки, а не только до первой ошибки', () => {
    const { errors, setOrClear, validateAll } = useFormErrors()
    const ok = validateAll(
      () => setOrClear('email', 'Укажите email'),
      () => setOrClear('phone', 'Укажите телефон'),
    )
    expect(ok).toBe(false)
    // Обе ошибки должны быть подсвечены разом — иначе пользователь исправляет
    // форму по одному полю за отправку.
    expect(errors.email).toBe('Укажите email')
    expect(errors.phone).toBe('Укажите телефон')
  })

  it('validateAll возвращает true, когда все проверки чистые', () => {
    const { setOrClear, validateAll } = useFormErrors()
    expect(validateAll(() => setOrClear('email', ''), () => setOrClear('phone', ''))).toBe(true)
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

  it('setFromResponse возвращает false, если ни одно поле не подсветилось', () => {
    // 422 бывает и по параметрам, которых на форме нет — вызывающий обязан
    // показать тост, иначе ошибка пропадёт без следа.
    const { setFromResponse } = useFormErrors()
    expect(setFromResponse({ response: { data: { detail: [{ type: 'missing', loc: [] }] } } })).toBe(false)
  })

  it('ошибка модели целиком (loc: [body]) не считается полем формы', () => {
    const { errors, setFromResponse } = useFormErrors()
    const handled = setFromResponse({
      response: { data: { detail: [{ type: 'value_error', loc: ['body'], msg: 'Value error, close_time позже open_time' }] } },
    })
    expect(handled).toBe(false)
    expect(errors.body).toBeUndefined()
  })

  it('повторный setFromResponse очищает ошибки от предыдущего вызова', () => {
    const { errors, setFromResponse } = useFormErrors()
    setFromResponse({ response: { data: { detail: [{ type: 'missing', loc: ['body', 'phone'] }] } } })
    setFromResponse({ response: { data: { detail: [{ type: 'missing', loc: ['body', 'email'] }] } } })
    expect(errors.phone).toBeUndefined()
    expect(errors.email).toBe('Обязательное поле')
  })
})
