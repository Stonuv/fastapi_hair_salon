// Клиентская половина двусторонней валидации: те же ограничения, что задают
// схемы бэкенда (backend/app/schemas/fields.py и соседние), но проверяемые до
// отправки запроса — чтобы ошибка подсвечивалась сразу под полем, а не
// возвращалась 422-м ответом. Сервер остаётся единственным авторитетом:
// клиент здесь лишь дублирует правила и ослаблять их нельзя (иначе форма
// пропустит то, что бэкенд отклонит, и пользователь снова увидит тост вместо
// подсветки). Каждая функция возвращает текст ошибки или '' — пустая строка
// означает «поле валидно», см. setOrClear в composables/useFormErrors.js.
//
// При изменении ограничения на сервере правьте и здесь: расхождение не ломает
// защиту, но возвращает форму к сообщениям «после запроса».

// PhoneStr: pattern ^\+?[0-9()\- ]{5,20}$ И max_length=20. Одного паттерна
// мало: он разрешает «+» сверх двадцати символов, то есть 21-символьный номер
// прошёл бы клиент и упёрся в max_length на сервере — длину проверяем отдельно.
const PHONE_RE = /^\+?[0-9()\- ]{5,20}$/
const PHONE_MAX = 20
// EmailStr на сервере разбирается полноценным парсером; на клиенте достаточно
// формы «есть @ и точка в домене» — задача подсказать опечатку, а не повторить
// RFC 5322. Собаку из частей адреса исключаем явно: с \S+ выражение
// пропускало «user@@example.com» (первый \S+ съедал «user@»), и такой адрес
// доходил до сервера за 422-м ответом.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
// PasswordStr: min_length=8, максимум 72 байта (предел bcrypt)
const PASSWORD_MIN = 8
const PASSWORD_MAX_BYTES = 72
// NameStr: 1..100
const NAME_MAX = 100

/** «5 символов» / «2 символа» — сообщения показываются пользователю, поэтому
 * склонение считаем, а не пишем «символ(ов)». */
function plural(n, one, few, many) {
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 14) return many
  const mod10 = n % 10
  if (mod10 === 1) return one
  if (mod10 >= 2 && mod10 <= 4) return few
  return many
}

const chars = (n) => `${n} ${plural(n, 'символ', 'символа', 'символов')}`

/** Обязательное непустое поле — NameStr и прочие Field(min_length=1). */
export function requiredText(value, message, max = NAME_MAX) {
  return textError(value, { min: 1, max, message })
}

/** Текстовое поле с собственными границами — например ServiceBase.name
 * (min_length=2, max_length=200). */
export function textError(value, { min = 1, max = NAME_MAX, required = true, message = 'Обязательное поле' } = {}) {
  const v = (value ?? '').trim()
  if (!v) return required ? message : ''
  if (v.length < min) return `Минимум ${chars(min)}`
  if (v.length > max) return `Не более ${chars(max)}`
  return ''
}

export function emailError(value, { required = true } = {}) {
  const v = (value ?? '').trim()
  if (!v) return required ? 'Укажите email' : ''
  if (!EMAIL_RE.test(v)) return 'Некорректный email'
  return ''
}

/** Телефон почти везде необязателен (PhoneStr | None): пустое значение
 * валидно и уходит на сервер как null. */
export function phoneError(value, { required = false } = {}) {
  const raw = value ?? ''
  if (!raw.trim()) return required ? 'Укажите телефон' : ''
  // Паттерн и длину меряем по исходной строке, а не по обрезанной: на сервер
  // уходит именно она, и пробелы по краям входят в max_length=20.
  if (!PHONE_RE.test(raw) || raw.length > PHONE_MAX) return 'Некорректный номер, например +7 999 000 00 00'
  return ''
}

/** required=false — поле «оставьте пустым, чтобы не менять» (AdminUserUpdate
 * .new_password): пустая строка валидна, заполненная проверяется полностью. */
export function passwordError(value, { required = true } = {}) {
  const v = value ?? ''
  if (!v) return required ? `Минимум ${chars(PASSWORD_MIN)}` : ''
  if (v.length < PASSWORD_MIN) return `Минимум ${chars(PASSWORD_MIN)}`
  // Именно байты: bcrypt обрезает по 72 байтам, кириллица занимает по два.
  if (new TextEncoder().encode(v).length > PASSWORD_MAX_BYTES) {
    return `Слишком длинный пароль (до ${PASSWORD_MAX_BYTES} байт, кириллица считается за два)`
  }
  return ''
}

/** Числовое поле: PositiveMoney (gt=0, decimal_places=2, max_digits=10) и
 * целые Field(gt=0). Границы задаются вызывающим, значение по умолчанию —
 * «строго больше нуля». */
export function numberError(value, {
  min = 0, max = Infinity, integer = false, required = true, message = 'Укажите значение',
} = {}) {
  const raw = typeof value === 'string' ? value.trim() : value
  if (raw === '' || raw === null || raw === undefined) return required ? message : ''
  const n = Number(raw)
  if (!Number.isFinite(n)) return 'Введите число'
  if (integer && !Number.isInteger(n)) return 'Введите целое число'
  if (n <= min) return `Значение должно быть больше ${min}`
  if (n > max) return `Значение должно быть не больше ${max}`
  // Считаем знаки у разобранного числа, а не у строки: «1500.4000» -- это те
  // же два знака, Decimal на сервере нормализует хвостовые нули и такую цену
  // принимает.
  if (!integer && (String(n).split('.')[1]?.length ?? 0) > 2) return 'Не более двух знаков после запятой'
  return ''
}

/** Деньги: Numeric(10,2) в БД и PositiveMoney в схемах — до 99 999 999,99. */
export const MONEY_MAX = 99999999.99

export function moneyError(value, { required = true, message = 'Укажите цену' } = {}) {
  return numberError(value, { min: 0, max: MONEY_MAX, required, message })
}

/** Пара «начало — конец»: SalonCreate.close_after_open,
 * ScheduleCreate.end_after_start. */
export function timeRangeError(start, end, message = 'Время закрытия должно быть позже времени открытия') {
  if (!start || !end) return ''
  return end <= start ? message : ''
}
