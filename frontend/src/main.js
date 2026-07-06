import { createApp } from 'vue'
import { createPinia } from 'pinia'
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

app.mount('#app')
