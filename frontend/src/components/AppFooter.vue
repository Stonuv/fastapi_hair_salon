<template>
  <footer class="bg-[#0c0c0c] px-4 py-16 sm:px-6">
    <div class="mx-auto max-w-6xl">
      <div class="grid gap-10 border-b border-white/15 pb-12 sm:grid-cols-[1.6fr_1fr_1fr_1fr]">
        <div>
          <div class="flex items-baseline gap-2.5">
            <span class="font-display text-2xl font-black uppercase tracking-tight text-stone-50">Сайтама</span>
            <span class="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">Барбершоп</span>
          </div>
          <p class="mt-4 max-w-xs text-sm leading-relaxed text-white/50">
            Чёткий срез, тихий зал. Современное барберство с точностью до минуты.
          </p>
        </div>
        <div>
          <div class="mb-4 font-mono text-[11px] uppercase tracking-wide text-white/40">Адрес</div>
          <div class="text-sm leading-relaxed text-white/70">ул. Тверская, 12<br>Москва<br>+7 (495) 123-45-67</div>
        </div>
        <div>
          <div class="mb-4 font-mono text-[11px] uppercase tracking-wide text-white/40">Часы работы</div>
          <div class="text-sm leading-relaxed text-white/70">Пн–Пт 9:00–20:00<br>Сб 10:00–18:00<br>Вс — выходной</div>
        </div>
        <div>
          <div class="mb-4 font-mono text-[11px] uppercase tracking-wide text-white/40">Мы в сети</div>
          <div class="flex flex-col gap-2.5">
            <a href="#" class="font-mono text-xs uppercase tracking-wide text-white/70 hover:text-white">Instagram ↗</a>
            <a href="#" class="font-mono text-xs uppercase tracking-wide text-white/70 hover:text-white">Google Карты ↗</a>
            <a href="#" class="font-mono text-xs uppercase tracking-wide text-white/70 hover:text-white">Сертификаты ↗</a>
          </div>
        </div>
      </div>
      <div class="flex flex-wrap items-center justify-between gap-2 pt-6 font-mono text-[11px] uppercase tracking-wide text-white/40">
        <span>© {{ year }} Барбершоп «Сайтама»</span>
        <span>Запись онлайн · Оплата картой и наличными</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
</script>
