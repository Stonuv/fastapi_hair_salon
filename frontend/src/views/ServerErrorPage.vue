<template>
  <div class="flex min-h-[calc(100vh-65px)] flex-col items-center justify-center gap-4 px-4 text-center">
    <p class="font-mono text-7xl font-bold text-ink-900">500</p>
    <h1 class="font-display text-2xl font-bold uppercase tracking-tight text-ink-900">Ошибка на сервере</h1>
    <p class="max-w-md text-ink-600">
      Запрос не удалось выполнить — это сбой на нашей стороне, а не ошибка в ваших данных.
      Попробуйте обновить страницу через минуту.
    </p>
    <p v-if="supportPhone" class="max-w-md text-ink-600">
      Если не заработает, свяжитесь с нами: <a class="underline" :href="`tel:${supportPhone}`">{{ supportPhone }}</a>
    </p>
    <p v-else class="max-w-md text-ink-600">
      Если не заработает, свяжитесь с администратором салона — записи и оплаченные визиты при этом сбое не теряются.
    </p>
    <div class="mt-2 flex flex-wrap justify-center gap-3">
      <BaseButton @click="reload">Обновить страницу</BaseButton>
      <router-link :to="{ name: 'home' }">
        <BaseButton variant="ghost">На главную</BaseButton>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSalonStore } from '../stores/salon'
import BaseButton from '../components/ui/BaseButton.vue'

// Телефон берём из уже загруженного стора, но НЕ догружаем его здесь: на эту
// страницу попадают именно потому, что API только что ответил 5xx — новый
// запрос с высокой вероятностью упадёт так же. Нет данных — показываем
// текст без телефона (v-else выше), а не пустую строку.
const salonStore = useSalonStore()
const supportPhone = computed(
  () => salonStore.activeSalons.find((s) => s.phone)?.phone ?? null,
)

// router.push обратно не годится: страница уже в сломанном состоянии, нужна
// именно полная перезагрузка приложения.
function reload() {
  window.location.reload()
}
</script>
