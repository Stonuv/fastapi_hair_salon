import { watch } from 'vue'

/** Debounced watcher — fires `callback` `delay`ms after the watched source stops changing. */
export function useDebouncedWatch(source, callback, delay = 350) {
  let timer = null
  watch(source, (...args) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => callback(...args), delay)
  })
}
