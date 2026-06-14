<template>
  <router-link :to="`/masters/${master.id}`" class="card">
    <div class="card__photo">
      <img v-if="master.photo_url" :src="master.photo_url" :alt="fullName" />
      <div v-else class="card__photo-placeholder">✂</div>
    </div>
    <div class="card__body">
      <p class="card__spec">{{ master.specialization || 'Мастер' }}</p>
      <h3 class="card__name">{{ fullName }}</h3>
      <div class="card__divider">✂</div>
      <p class="card__cta">Записаться →</p>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  master: { type: Object, required: true }
})

const fullName = computed(() =>
  `${props.master.first_name} ${props.master.last_name}`
)
</script>

<style scoped>
.card {
  display: block;
  text-decoration: none;
  background: var(--c-cream);
  border: 1px solid var(--c-latte);
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.25s, box-shadow 0.25s;
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(44, 24, 16, 0.12);
}
.card__photo {
  width: 100%;
  aspect-ratio: 3/4;
  background: var(--c-latte);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.card__photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.card__photo-placeholder {
  font-size: 3rem;
  opacity: 0.3;
  color: var(--c-espresso);
}
.card__body {
  padding: 1.25rem;
}
.card__spec {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--c-caramel);
  margin: 0 0 0.35rem;
}
.card__name {
  font-family: var(--f-display);
  font-size: 1.35rem;
  color: var(--c-espresso);
  margin: 0;
  font-weight: 500;
}
.card__divider {
  margin: 0.85rem 0;
  font-size: 0.75rem;
  color: var(--c-latte);
  text-align: center;
  position: relative;
}
.card__divider::before,
.card__divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 38%;
  height: 1px;
  background: var(--c-latte);
}
.card__divider::before { left: 0; }
.card__divider::after  { right: 0; }
.card__cta {
  font-size: 0.85rem;
  color: var(--c-matcha);
  margin: 0;
  font-weight: 500;
  letter-spacing: 0.03em;
}
</style>
