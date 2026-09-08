<template>
  <div class="flex min-h-[calc(100vh-65px)] flex-col items-center justify-center gap-4 px-4 text-center">
    <p class="font-mono text-7xl font-bold text-ink-900">404</p>
    <h1 class="font-display text-2xl font-bold uppercase tracking-tight text-ink-900">Страница не найдена</h1>
    <p class="max-w-md text-ink-600">
      Такой страницы не существует или она была перемещена. Найдите мастера по специализации 🤭
    </p>

    <!-- Поиск ведёт в тот же каталог мастеров с уже подставленным фильтром
         (/masters?specialization=…), а не в отдельную страницу результатов:
         единственное текстовое поле поиска в публичной части — там. -->
    <form class="mt-2 flex w-full max-w-md flex-col gap-3 sm:flex-row" @submit.prevent="search">
      <BaseInput
        v-model="query"
        class="flex-1"
        placeholder="Например: борода, фейд…"
        aria-label="Поиск по специализации мастера"
      />
      <BaseButton type="submit">Найти</BaseButton>
    </form>

    <router-link :to="{ name: 'masters' }" class="font-mono text-xs uppercase tracking-wider text-ink-600 underline">
      Показать всех мастеров
    </router-link>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseInput from '../components/ui/BaseInput.vue'

const router = useRouter()
const query = ref('')

function search() {
  const trimmed = query.value.trim()
  // Пустой запрос — просто весь каталог, без ?specialization= в адресе:
  // пустой параметр в ссылке выглядел бы как применённый фильтр.
  router.push({ name: 'masters', query: trimmed ? { specialization: trimmed } : {} })
}
</script>
