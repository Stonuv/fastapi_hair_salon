export function extractErrorMessage(err, fallback = 'Что-то пошло не так. Попробуйте ещё раз.') {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => d.msg).join('; ')
  }
  return fallback
}
