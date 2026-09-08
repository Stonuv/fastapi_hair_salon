import { onMounted, onUnmounted } from 'vue'

/**
 * Периодический вызов `callback` с паузой на скрытой вкладке.
 *
 * setTimeout после завершения вызова, а не setInterval: медленный ответ
 * (или вставший бэкенд) при setInterval копил бы параллельные запросы —
 * следующий тик приходит, не дождавшись предыдущего.
 *
 * Скрытая вкладка вообще не опрашивается: браузер оставляет её открытой
 * сутками, и админ-панель, забытая во второй вкладке, иначе стучала бы в
 * /admin/stats всю ночь. Возврат на вкладку — сразу вызов, а не ожидание
 * ещё одного интервала: свежие числа нужны именно в момент, когда на них
 * снова смотрят.
 */
export function usePolling(callback, intervalMs = 30000) {
  let timer = null
  let stopped = false

  function schedule() {
    clearTimeout(timer)
    timer = setTimeout(run, intervalMs)
  }

  async function run() {
    clearTimeout(timer)
    try {
      await callback()
    } catch {
      // Ошибку разбирает сам callback. Цикл она не роняет: сеть моргнула —
      // следующий тик попробует снова.
    }
    if (!stopped && !document.hidden) schedule()
  }

  function onVisibilityChange() {
    if (stopped) return
    if (document.hidden) clearTimeout(timer)
    else run()
  }

  function stop() {
    stopped = true
    clearTimeout(timer)
    document.removeEventListener('visibilitychange', onVisibilityChange)
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', onVisibilityChange)
    if (!document.hidden) schedule()
  })
  // Уход со страницы должен гасить цикл — иначе таймер переживает компонент
  // и дёргает API уже из закрытого экрана.
  onUnmounted(stop)

  return { stop, refreshNow: run }
}
