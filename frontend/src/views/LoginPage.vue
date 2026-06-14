<template>
  <div class="page">
    <div class="card">
      <h1 class="card__title">
        {{ isRegister ? 'Регистрация' : 'Вход' }}
      </h1>
      <div class="scissors-divider">✂</div>

      <form class="form" @submit.prevent="submit">
        <template v-if="isRegister">
          <div class="form__row">
            <input v-model="form.first_name" class="form__input"
                   placeholder="Имя" required />
            <input v-model="form.last_name" class="form__input"
                   placeholder="Фамилия" required />
          </div>
        </template>

        <input v-model="form.email" class="form__input"
               type="email" placeholder="Email" required />
        <input v-model="form.password" class="form__input"
               type="password" placeholder="Пароль" required />

        <p v-if="error" class="error">{{ error }}</p>

        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? '…' : (isRegister ? 'Зарегистрироваться' : 'Войти') }}
        </button>
      </form>

      <p class="card__switch">
        {{ isRegister ? 'Уже есть аккаунт?' : 'Нет аккаунта?' }}
        <button class="link-btn" @click="isRegister = !isRegister">
          {{ isRegister ? 'Войти' : 'Зарегистрироваться' }}
        </button>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router     = useRouter()
const auth       = useAuthStore()
const isRegister = ref(false)
const loading    = ref(false)
const error      = ref('')

const form = reactive({
  email: '', password: '', first_name: '', last_name: ''
})

async function submit() {
  loading.value = true
  error.value   = ''
  try {
    if (isRegister.value) {
      await auth.register(form)
    } else {
      await auth.login({ email: form.email, password: form.password })
    }
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка. Проверьте данные.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 64px);
  padding: 2rem 1.5rem;
}
.card {
  width: 100%;
  max-width: 400px;
  background: var(--c-cream);
  border: 1px solid var(--c-latte);
  border-radius: 10px;
  padding: 2.5rem 2rem;
}
.card__title {
  font-family: var(--f-display);
  font-size: 2rem;
  font-weight: 400;
  color: var(--c-espresso);
  margin: 0 0 0.5rem;
  text-align: center;
}
.scissors-divider {
  text-align: center;
  font-size: 0.9rem;
  color: var(--c-latte);
  position: relative;
  margin: 0 0 1.75rem;
}
.scissors-divider::before,
.scissors-divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: calc(50% - 1.5rem);
  height: 1px;
  background: var(--c-latte);
}
.scissors-divider::before { left: 0; }
.scissors-divider::after  { right: 0; }

.form { display: flex; flex-direction: column; gap: 0.75rem; }
.form__row { display: flex; gap: 0.75rem; }
.form__input {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 1px solid var(--c-latte);
  border-radius: 5px;
  background: #fff;
  font-size: 0.95rem;
  color: var(--c-espresso);
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.form__input:focus { border-color: var(--c-matcha); }

.btn {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: var(--c-matcha);
  color: #fff;
  border: none;
  border-radius: 5px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn:hover    { opacity: 0.85; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.error {
  color: #b05050;
  font-size: 0.875rem;
  margin: 0;
}
.card__switch {
  text-align: center;
  margin: 1.25rem 0 0;
  font-size: 0.875rem;
  color: #8a7060;
}
.link-btn {
  background: none;
  border: none;
  color: var(--c-matcha);
  cursor: pointer;
  font-size: inherit;
  padding: 0;
  margin-left: 0.25rem;
}
</style>
