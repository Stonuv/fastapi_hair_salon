// FastAPI/Pydantic 422 msg — сырые технические строки ("String should match
// pattern '^\+?[0-9()\- ]{5,20}$'", "String should have at least..."). Клиент
// не должен их видеть (ISSUES #4, #20) — переводим по item.type в понятный
// русский текст. Для полей с собственным читаемым сообщением (email/phone)
// подставляем его независимо от типа ошибки — точнее любого общего текста.
const FIELD_MESSAGES = {
  email: 'Введите корректный email',
  phone: 'Введите корректный номер телефона, например +7 999 000 00 00',
}

const MESSAGE_BY_TYPE = {
  string_too_short:  'Слишком короткое значение',
  string_too_long:   'Слишком длинное значение',
  string_pattern_mismatch: 'Неверный формат',
  greater_than:       'Значение слишком маленькое',
  greater_than_equal: 'Значение слишком маленькое',
  less_than:          'Значение слишком большое',
  less_than_equal:    'Значение слишком большое',
  int_parsing:      'Введите число',
  float_parsing:    'Введите число',
  decimal_parsing:  'Введите число',
  bool_parsing:     'Некорректное значение',
  uuid_parsing:     'Некорректный идентификатор',
}

/** Переводит один элемент FastAPI 422 detail[] в пару {field, message} на
 * понятном русском — общая логика для useFormErrors (поэлементно под полями
 * формы) и extractErrorMessage (единый текст тоста). */
export function friendlyValidationError(item) {
  const field = item.loc?.[item.loc.length - 1]
  let message
  if (item.type === 'missing') {
    message = 'Обязательное поле'
  } else if (field && FIELD_MESSAGES[field]) {
    message = FIELD_MESSAGES[field]
  } else if (item.type === 'value_error') {
    // Наши собственные валидаторы (raise ValueError(...)) уже пишут понятный
    // текст на русском — Pydantic лишь добавляет префикс "Value error, ".
    message = item.msg.replace(/^Value error,\s*/, '')
  } else {
    message = MESSAGE_BY_TYPE[item.type] || 'Некорректное значение'
  }
  return { field, message }
}

export function extractErrorMessage(err, fallback = 'Что-то пошло не так. Попробуйте ещё раз.') {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => friendlyValidationError(d).message).join('; ')
  }
  return fallback
}
