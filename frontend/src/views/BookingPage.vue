<template>
  <div class="page">
    <!-- Hero -->
    <section class="hero">
      <p class="hero__eyebrow">Барбершоп · Сайтама</p>
      <h1 class="hero__title">Мастера,<br>которым доверяют</h1>
      <p class="hero__sub">Выберите мастера и запишитесь онлайн за 30 секунд</p>
    </section>

    <div class="scissors-divider">✂</div>

    <!-- Catalog -->
    <section class="catalog">
      <div v-if="loading" class="state">Загружаем мастеров…</div>

      <div v-else-if="error" class="state state--error">
        Не удалось загрузить мастеров. Попробуйте обновить страницу.
      </div>

      <div v-else-if="masters.length === 0" class="state">
        Мастера пока не добавлены.
      </div>

      <div v-else class="catalog__grid">
        <MasterCard
          v-for="master in masters"
          :key="master.id"
          :master="master"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { mastersApi } from '../api'
import MasterCard from '../components/MasterCard.vue'

const masters = ref([])
const loading = ref(true)
const error   = ref(false)

onMounted(async () => {
  try {
    const res = await mastersApi.getAll()
    masters.value = res.data.masters
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1.5rem 4rem;
}

/* Hero */
.hero {
  padding: 5rem 0 3.5rem;
  text-align: center;
}
.hero__eyebrow {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--c-caramel);
  margin: 0 0 1rem;
}
.hero__title {
  font-family: var(--f-display);
  font-size: clamp(2.8rem, 6vw, 5rem);
  color: var(--c-espresso);
  line-height: 1.05;
  margin: 0 0 1.25rem;
  font-weight: 400;
}
.hero__sub {
  color: #6b5b50;
  font-size: 1.05rem;
  margin: 0;
}

/* Divider */
.scissors-divider {
  text-align: center;
  font-size: 1rem;
  color: var(--c-latte);
  position: relative;
  margin: 0.5rem 0 3rem;
}
.scissors-divider::before,
.scissors-divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: calc(50% - 2rem);
  height: 1px;
  background: var(--c-latte);
}
.scissors-divider::before { left: 0; }
.scissors-divider::after  { right: 0; }

/* Catalog */
.catalog__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1.75rem;
}

/* States */
.state {
  text-align: center;
  padding: 4rem 0;
  color: #8a7060;
  font-size: 1rem;
}
.state--error { color: #b05050; }
</style>
