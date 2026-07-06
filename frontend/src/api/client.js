import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  // Access-токен живёт в httpOnly-cookie (не в localStorage — см. README
  // «Осознанные компромиссы безопасности»), браузер прикладывает её сам;
  // withCredentials нужен, если фронтенд когда-нибудь окажется на другом
  // origin от API (сейчас оба — за одним прокси, dev и prod).
  withCredentials: true,
})

// Обработчик 401 внедряется из main.js (setUnauthorizedHandler): прямой
// импорт router отсюда создавал цикл client → router → stores → client,
// а чистить надо Pinia-стор (auth.clearSession()) — саму cookie снял сервер.
let onUnauthorized = null

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && onUnauthorized) {
      onUnauthorized()
    }
    return Promise.reject(error)
  }
)

export default client
