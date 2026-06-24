<template>
  <div class="flex min-h-[calc(100vh-65px)] flex-col items-center justify-center gap-4 px-4 text-center">
    <p class="font-mono text-7xl font-bold text-ink-900">404</p>
    <h1 class="font-display text-2xl font-bold uppercase tracking-tight text-ink-900">Страница не найдена</h1>
    <p class="max-w-md text-ink-600">
      Такой страницы не существует или она была перемещена. Попробуйте найти мастера в каталоге.
    </p>
    <router-link :to="{ name: 'masters' }">
      <BaseButton class="mt-2">К каталогу мастеров</BaseButton>
    </router-link>
  </div>
</template>

<script setup>
import BaseButton from '../components/ui/BaseButton.vue'
</script>
