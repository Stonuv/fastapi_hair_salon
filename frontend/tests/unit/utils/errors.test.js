import { describe, it, expect } from 'vitest'
import { extractErrorMessage, friendlyValidationError } from '../../../src/utils/errors'

describe('friendlyValidationError', () => {
  it('обязательное поле помечается стандартным текстом независимо от имени', () => {
    const { field, message } = friendlyValidationError({ type: 'missing', loc: ['body', 'phone'] })
    expect(field).toBe('phone')
    expect(message).toBe('Обязательное поле')
  })

  it('email/phone используют собственные читаемые сообщения даже при незнакомом типе ошибки', () => {
    expect(friendlyValidationError({ type: 'string_pattern_mismatch', loc: ['body', 'email'] }).message)
      .toBe('Введите корректный email')
    expect(friendlyValidationError({ type: 'value_error', loc: ['body', 'phone'] }).message)
      .toBe('Введите корректный номер телефона, например +7 999 000 00 00')
  })

  it('value_error из собственных валидаторов отдаёт msg без префикса Pydantic', () => {
    const { message } = friendlyValidationError({
      type: 'value_error', loc: ['body', 'comment'], msg: 'Value error, Ссылки запрещены',
    })
    expect(message).toBe('Ссылки запрещены')
  })

  it('незнакомый тип без явного маппинга получает общий фолбэк', () => {
    const { message } = friendlyValidationError({ type: 'something_new', loc: ['body', 'note'] })
    expect(message).toBe('Некорректное значение')
  })

  it('известный тип берётся из MESSAGE_BY_TYPE', () => {
    expect(friendlyValidationError({ type: 'string_too_short', loc: ['body', 'note'] }).message)
      .toBe('Слишком короткое значение')
  })
})

describe('extractErrorMessage', () => {
  it('строковый detail возвращается как есть', () => {
    const err = { response: { data: { detail: 'Неверный логин или пароль' } } }
    expect(extractErrorMessage(err)).toBe('Неверный логин или пароль')
  })

  it('массив detail из 422 схлопывается в одну строку через "; "', () => {
    const err = {
      response: {
        data: {
          detail: [
            { type: 'missing', loc: ['body', 'phone'] },
            { type: 'string_too_short', loc: ['body', 'name'] },
          ],
        },
      },
    }
    expect(extractErrorMessage(err)).toBe('Обязательное поле; Слишком короткое значение')
  })

  it('при отсутствии detail (сетевая ошибка/500) возвращается фолбэк', () => {
    expect(extractErrorMessage({}, 'Что-то пошло не так')).toBe('Что-то пошло не так')
    expect(extractErrorMessage({})).toBe('Что-то пошло не так. Попробуйте ещё раз.')
  })
})
