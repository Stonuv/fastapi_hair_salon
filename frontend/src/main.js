import { createApp } from 'vue'
import { createPinia } from 'pinia'
import * as Sentry from '@sentry/vue'
import router from './router'
import App from './App.vue'
import { setUnauthorizedHandler } from './api/client'
import { useAuthStore } from './stores/auth'
import { useToastStore } from './stores/toast'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// 401 от API: чистим Pinia-стор локально (clearSession — не auth.logout(),
// иначе POST /auth/logout на уже отвергнутый токен сам вернёт 401 и
// зациклит обработчик); затем уводим на логин с возвратом. Неудачная
// попытка входа (мы ещё не залогинены) или запрос со страницы логина
// редирект не вызывает.
setUnauthorizedHandler(() => {
  const auth = useAuthStore()
  if (!auth.isLoggedIn) return
  auth.clearSession()
  const current = router.currentRoute.value
  if (current.path !== '/login') {
    router.push({ path: '/login', query: { redirect: current.fullPath } })
  }
})

// Error boundary: необработанная ошибка рендера не должна молча ломать
// страницу (ТЗ 5.5) — показываем тост и пишем в консоль.
app.config.errorHandler = (err, _instance, info) => {
  console.error('[vue error]', info, err)
  useToastStore().error('Что-то пошло не так. Обновите страницу.')
}

// VITE_SENTRY_DSN не задан на сборке -> просто не инициализируем (см. TODO
// у settings.sentry_dsn в backend/app/config.py — аккаунт на sentry.io ещё
// не создан). Порядок важен: Sentry.init должен идти ПОСЛЕ того, как выше
// выставлен app.config.errorHandler — сам оборачивает уже существующий
// обработчик (@sentry/vue делает это при инициализации), поэтому и тост,
// и отчёт в Sentry продолжат работать одновременно, а не одно вместо другого.
if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    app,
    dsn: import.meta.env.VITE_SENTRY_DSN,
    tracesSampleRate: 0,
  })
}

app.mount('#app')
