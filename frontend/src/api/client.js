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

// Access-токен короткоживущий (см. backend/app/config.py) — 401 сперва
// пробуем тихо пережить через refresh-токен (httpOnly-cookie, отдельная от
// access) и повторить исходный запрос, вместо немедленного разлогина.
// Общий промис — конкурентные 401 от нескольких запросов не должны бить по
// /auth/refresh параллельно: ротация делает предыдущий refresh-токен
// одноразовым, вторая параллельная попытка получила бы 401 на уже
// использованный токен.
let refreshPromise = null

function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = axios
      .post('/api/auth/refresh', null, { withCredentials: true })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

const NO_RETRY_PATHS = ['/auth/login', '/auth/register', '/auth/refresh']

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    const isNoRetryEndpoint = NO_RETRY_PATHS.some((path) => config?.url?.startsWith(path))

    if (response?.status === 401 && config && !config._retriedAfterRefresh && !isNoRetryEndpoint) {
      config._retriedAfterRefresh = true
      try {
        await refreshAccessToken()
        return client(config)
      } catch {
        // refresh тоже не удался (сессия отозвана/истекла) — падаем ниже на onUnauthorized
      }
    }

    if (error.response?.status === 401 && onUnauthorized) {
      onUnauthorized()
    }
    return Promise.reject(error)
  }
)

export default client
