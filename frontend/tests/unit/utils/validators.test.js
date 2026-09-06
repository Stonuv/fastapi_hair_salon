import { describe, it, expect } from 'vitest'
import {
  requiredText, textError, emailError, phoneError, passwordError,
  numberError, moneyError, timeRangeError, MONEY_MAX,
} from '../../../src/utils/validators'

// Валидаторы обязаны быть не слабее серверных схем (backend/app/schemas):
// всё, что проходит здесь, должно проходить и на бэкенде — иначе форма
// пропустит запрос, который вернётся 422-м ответом.

describe('requiredText / textError', () => {
  it('пустое значение и пробелы -- ошибка с переданным текстом', () => {
    expect(requiredText('', 'Укажите имя')).toBe('Укажите имя')
    expect(requiredText('   ', 'Укажите имя')).toBe('Укажите имя')
    expect(requiredText(null, 'Укажите имя')).toBe('Укажите имя')
  })

  it('NameStr: до 100 символов включительно', () => {
    expect(requiredText('а'.repeat(100), 'Укажите имя')).toBe('')
    expect(requiredText('а'.repeat(101), 'Укажите имя')).toBe('Не более 100 символов')
  })

  it('собственная нижняя граница -- ServiceBase.name (min_length=2)', () => {
    expect(textError('С', { min: 2, max: 200 })).toBe('Минимум 2 символа')
    expect(textError('Стрижка', { min: 2, max: 200 })).toBe('')
  })

  it('необязательное поле пустым проходит, но длину всё равно проверяет', () => {
    expect(textError('', { required: false })).toBe('')
    expect(textError('а'.repeat(2001), { max: 2000, required: false })).toBe('Не более 2000 символов')
  })

  it('склонение в сообщении считается, а не пишется «символ(ов)»', () => {
    expect(textError('а', { min: 5 })).toBe('Минимум 5 символов')
    expect(textError('а', { min: 2 })).toBe('Минимум 2 символа')
    expect(textError('аа', { min: 21 })).toBe('Минимум 21 символ')
    expect(textError('аа', { min: 11 })).toBe('Минимум 11 символов')
  })
})

describe('emailError', () => {
  it('корректный адрес проходит', () => {
    expect(emailError('user@example.com')).toBe('')
  })

  it('без @ или без домена -- ошибка', () => {
    expect(emailError('user')).toBe('Некорректный email')
    expect(emailError('user@example')).toBe('Некорректный email')
    expect(emailError('user @ example.com')).toBe('Некорректный email')
  })

  it('двойная собака не проходит -- \\S+ пропускал «user@@example.com» на сервер', () => {
    expect(emailError('user@@example.com')).toBe('Некорректный email')
    expect(emailError('@example.com')).toBe('Некорректный email')
  })

  it('пустое значение обязательно по умолчанию и допустимо при required=false', () => {
    expect(emailError('')).toBe('Укажите email')
    expect(emailError('', { required: false })).toBe('')
  })
})

describe('phoneError', () => {
  it('форматы, которые принимает PhoneStr', () => {
    expect(phoneError('+7 999 000 00 00')).toBe('')
    expect(phoneError('8(999)000-00-00')).toBe('')
  })

  it('пустой телефон валиден -- поле необязательное (PhoneStr | None)', () => {
    expect(phoneError('')).toBe('')
  })

  it('буквы и слишком короткий номер отклоняются', () => {
    expect(phoneError('телефон')).not.toBe('')
    expect(phoneError('1234')).not.toBe('')
  })

  it('длиннее 20 символов -- как max_length=20 на сервере', () => {
    expect(phoneError('+7 999 000 00 00 000 00')).not.toBe('')
    // Ровно 21 символ: паттерн PhoneStr его пропускает («+» сверх {5,20}),
    // а max_length=20 -- нет; клиент обязан отклонить вместе с сервером.
    expect('+7(41149606093578026 ').toHaveLength(21)
    expect(phoneError('+7(41149606093578026 ')).not.toBe('')
  })

  it('длина считается по исходной строке -- пробелы по краям уходят на сервер', () => {
    expect(phoneError(' 533  ')).toBe('')
  })
})

describe('passwordError', () => {
  it('PasswordStr: минимум 8 символов', () => {
    expect(passwordError('1234567')).toBe('Минимум 8 символов')
    expect(passwordError('12345678')).toBe('')
  })

  it('верхняя граница считается в байтах -- как ограничение bcrypt (72)', () => {
    expect(passwordError('a'.repeat(72))).toBe('')
    expect(passwordError('a'.repeat(73))).not.toBe('')
    // 36 кириллических символов -- ровно 72 байта в UTF-8, 37 -- уже больше.
    expect(passwordError('я'.repeat(36))).toBe('')
    expect(passwordError('я'.repeat(37))).not.toBe('')
  })

  it('required=false -- поле «оставьте пустым, чтобы не менять»', () => {
    expect(passwordError('', { required: false })).toBe('')
    expect(passwordError('123', { required: false })).toBe('Минимум 8 символов')
  })
})

describe('numberError / moneyError', () => {
  it('Field(gt=0): ноль и отрицательные отклоняются', () => {
    expect(numberError('0')).toBe('Значение должно быть больше 0')
    expect(numberError('-5')).toBe('Значение должно быть больше 0')
    expect(numberError('1')).toBe('')
  })

  it('нечисловое значение', () => {
    expect(numberError('дорого')).toBe('Введите число')
  })

  it('integer=true -- длительность в минутах целая', () => {
    expect(numberError('30', { integer: true })).toBe('')
    expect(numberError('30.5', { integer: true })).toBe('Введите целое число')
  })

  it('деньги: Numeric(10,2) -- два знака после запятой и верхняя граница', () => {
    expect(moneyError('1500')).toBe('')
    expect(moneyError('1500.50')).toBe('')
    expect(moneyError('1500.555')).toBe('Не более двух знаков после запятой')
    // Хвостовые нули -- это по-прежнему два знака: Decimal на сервере
    // нормализует их и такую цену принимает.
    expect(moneyError('1500.4000')).toBe('')
    expect(moneyError(MONEY_MAX)).toBe('')
    expect(moneyError(MONEY_MAX + 1)).not.toBe('')
  })

  it('пустое значение: обязательное по умолчанию, необязательное -- по флагу', () => {
    expect(moneyError('')).toBe('Укажите цену')
    expect(moneyError('', { required: false })).toBe('')
  })
})

describe('timeRangeError', () => {
  it('конец должен быть строго позже начала (close_after_open, end_after_start)', () => {
    expect(timeRangeError('09:00', '20:00')).toBe('')
    expect(timeRangeError('20:00', '09:00')).not.toBe('')
    expect(timeRangeError('09:00', '09:00')).not.toBe('')
  })

  it('незаполненная пара не считается ошибкой -- проверять нечего', () => {
    expect(timeRangeError('', '20:00')).toBe('')
    expect(timeRangeError('09:00', '')).toBe('')
  })
})
