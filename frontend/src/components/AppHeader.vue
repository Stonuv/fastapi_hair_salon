<template>
  <header class="header">
    <div class="header__inner">
      <router-link to="/" class="header__logo">✂ Сайтама</router-link>

      <nav class="header__nav">
        <router-link to="/" class="header__link">Мастера</router-link>

        <template v-if="auth.isLoggedIn">
          <router-link
            v-if="auth.user?.role === 'admin'"
            to="/admin"
            class="header__link"
          >Админ</router-link>

          <router-link
            v-if="auth.user?.role === 'master'"
            to="/dashboard"
            class="header__link"
          >Кабинет</router-link>

          <router-link to="/profile" class="header__link">
            {{ auth.user?.first_name }}
          </router-link>

          <button class="header__btn header__btn--ghost" @click="auth.logout">
            Выйти
          </button>
        </template>

        <template v-else>
          <router-link to="/login" class="header__btn">Войти</router-link>
        </template>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
</script>

<style scoped>
.header {
  position: sticky; top: 0; z-index: 100;
  background: var(--c-espresso);
  border-bottom: 1px solid var(--c-latte);
}
.header__inner {
  max-width: 1100px; margin: 0 auto;
  padding: 0 1.5rem; height: 64px;
  display: flex; align-items: center; justify-content: space-between;
}
.header__logo {
  font-family: var(--f-display); font-size: 1.4rem;
  color: var(--c-cream); text-decoration: none; letter-spacing: 0.04em;
}
.header__nav { display: flex; align-items: center; gap: 1.5rem; }
.header__link {
  color: var(--c-latte); text-decoration: none;
  font-size: 0.9rem; letter-spacing: 0.05em;
  text-transform: uppercase; transition: color 0.2s;
}
.header__link:hover,
.header__link.router-link-active { color: var(--c-cream); }
.header__btn {
  padding: 0.4rem 1rem;
  background: var(--c-matcha); color: var(--c-cream);
  border: none; border-radius: 4px; font-size: 0.85rem;
  cursor: pointer; text-decoration: none; transition: opacity 0.2s;
}
.header__btn:hover { opacity: 0.85; }
.header__btn--ghost {
  background: transparent;
  border: 1px solid var(--c-latte); color: var(--c-latte);
}
</style>
