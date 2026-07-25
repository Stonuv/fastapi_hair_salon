<template>
  <div class="flex min-h-screen items-center justify-center px-4 py-12">
    <BaseCard class="w-full max-w-xl">
      <p class="font-mono text-xs uppercase tracking-widest text-brand-700">Первый запуск · шаг {{ step }} из 4</p>
      <h1 class="mt-1 font-display text-2xl font-black uppercase tracking-tight text-ink-900">Настройка «Сайтама»</h1>
      <p class="mt-1 text-sm text-ink-600">Создайте аккаунт владельца и первую точку, чтобы начать работу с панелью управления</p>

      <form class="mt-6 space-y-4" novalidate @submit.prevent="onSubmitStep">
        <!-- Шаг 1: аккаунт администратора -->
        <div v-if="step === 1" class="space-y-4">
          <BaseInput
            v-if="setup.requiresToken"
            v-model="setupToken"
            label="Код настройки"
            required
            hint="Значение переменной окружения SETUP_TOKEN, заданной при деплое"
            :error="errors.setup_token"
            @blur="validateSetupToken"
          />

          <div class="grid grid-cols-2 gap-3">
            <BaseInput
              v-model="owner.first_name"
              label="Имя"
              required
              :error="errors.first_name"
              @blur="validateField('first_name', owner.first_name, 'Укажите имя')"
            />
            <BaseInput
              v-model="owner.last_name"
              label="Фамилия"
              required
              :error="errors.last_name"
              @blur="validateField('last_name', owner.last_name, 'Укажите фамилию')"
            />
          </div>

          <BaseInput
            v-model="owner.email"
            label="Email"
            type="email"
            autocomplete="email"
            required
            :error="errors.email"
            @blur="validateEmail"
          />
          <BaseInput
            v-model="owner.phone"
            label="Телефон"
            hint="Необязательно"
            autocomplete="tel"
            :error="errors.phone"
          />
          <BaseInput
            v-model="owner.password"
            label="Пароль"
            type="password"
            autocomplete="new-password"
            required
            hint="Минимум 8 символов"
            :error="errors.password"
            @blur="validatePassword"
          />
          <BaseInput
            v-model="owner.confirm_password"
            label="Повторите пароль"
            type="password"
            autocomplete="new-password"
            required
            :error="errors.confirm_password"
            @blur="validateConfirmPassword"
          />
        </div>

        <!-- Шаг 2: первая точка сети -->
        <div v-else-if="step === 2" class="space-y-4">
          <p class="text-sm text-ink-600">
            Первая точка сети. Позже владелец может добавить ещё точки и назначить каждой своего администратора.
          </p>
          <BaseInput
            v-model="salon.name"
            label="Название точки"
            required
            hint="Например, «Сайтама на Тверской»"
            :error="errors.salon_name"
            @blur="validateField('salon_name', salon.name, 'Укажите название точки')"
          />
          <BaseInput
            v-model="salon.address"
            label="Адрес"
            required
            :error="errors.salon_address"
            @blur="validateField('salon_address', salon.address, 'Укажите адрес')"
          />
          <BaseInput v-model="salon.phone" label="Телефон точки" hint="Необязательно" />
          <div>
            <p class="mb-1.5 text-sm font-medium text-ink-900">Время работы</p>
            <p class="mb-2 text-sm text-ink-600">
              Жёсткая граница: ни расписание мастера, ни запись клиента не смогут выйти за эти рамки.
            </p>
            <div class="flex items-center gap-3">
              <BaseTimeInput v-model="salon.open_time" />
              <span class="text-ink-600">—</span>
              <BaseTimeInput v-model="salon.close_time" />
            </div>
            <p v-if="errors.salon_hours" class="mt-1 text-sm text-danger">{{ errors.salon_hours }}</p>
          </div>
        </div>

        <!-- Шаг 3: базовые настройки сайта -->
        <div v-else-if="step === 3" class="space-y-4">
          <Skeleton v-if="settingsLoading" height="h-64" />
          <p v-else-if="!siteContent" class="text-sm text-danger">
            Не удалось загрузить настройки сайта. Можно продолжить без них — эти поля можно будет заполнить позже в «Админ → Редактор главной».
          </p>
          <template v-else>
            <div class="grid gap-4 sm:grid-cols-2">
              <BaseInput v-model="siteContent.header.brand_name" label="Название бренда" required />
              <BaseInput v-model="siteContent.header.brand_tagline" label="Подпись под названием" required />
            </div>
            <p class="text-sm text-ink-600/80">
              Бренд общий на всю сеть. Адрес и часы в подвале сайта заполнятся из точки, указанной на прошлом шаге;
              остальной контент можно донастроить позже в «Админ → Редактор главной».
            </p>
          </template>
        </div>

        <!-- Шаг 4: проверка и завершение -->
        <div v-else class="space-y-3">
          <p class="text-sm text-ink-600">Проверьте данные перед завершением настройки:</p>
          <dl class="space-y-1.5 rounded-lg border border-stone-200 p-4 text-sm">
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Владелец</dt><dd class="font-medium text-ink-900">{{ owner.first_name }} {{ owner.last_name }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Email</dt><dd class="font-medium text-ink-900">{{ owner.email }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Точка</dt><dd class="font-medium text-ink-900">{{ salon.name }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Адрес</dt><dd class="font-medium text-ink-900">{{ salon.address }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Время работы</dt><dd class="font-medium text-ink-900">{{ salon.open_time }} — {{ salon.close_time }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="text-ink-600">Название бренда</dt><dd class="font-medium text-ink-900">{{ siteContent?.header?.brand_name || '—' }}</dd></div>
          </dl>
        </div>

        <div class="flex justify-between pt-2">
          <BaseButton v-if="step > 1" type="button" variant="ghost" @click="step -= 1">Назад</BaseButton>
          <span v-else />
          <BaseButton type="submit" :loading="loading" :disabled="step === 3 && settingsLoading">
            {{ step < 4 ? 'Далее' : 'Завершить настройку' }}
          </BaseButton>
        </div>
      </form>
    </BaseCard>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { setupApi, settingsApi } from '../api'
import { useAuthStore } from '../stores/auth'
import { useSetupStore } from '../stores/setup'
import { useToastStore } from '../stores/toast'
import { useFormErrors } from '../composables/useFormErrors'
import { extractErrorMessage } from '../utils/errors'
import BaseCard from '../components/ui/BaseCard.vue'
import BaseInput from '../components/ui/BaseInput.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import BaseTimeInput from '../components/ui/BaseTimeInput.vue'
import Skeleton from '../components/ui/Skeleton.vue'

const router = useRouter()
const auth = useAuthStore()
const setup = useSetupStore()
const toast = useToastStore()
const { errors, setError, clearError, clearAll, setFromResponse } = useFormErrors()

const step = ref(1)
const loading = ref(false)
const settingsLoading = ref(true)

// Владелец сети, не администратор точки: роль admin с введением сети
// привязана к конкретному салону, на первом запуске её ставить некуда
// (см. backend SetupService.complete).
const owner = reactive({
  first_name: '', last_name: '', email: '', phone: '',
  password: '', confirm_password: '',
})
// Дефолты те же, что у заглушки из миграции 0013 — визард её заполняет.
const salon = reactive({
  name: '', address: '', phone: '',
  open_time: '09:00:00', close_time: '20:00:00',
})
const setupToken = ref('')
const siteContent = ref(null)

onMounted(async () => {
  try {
    const { data } = await settingsApi.get()
    siteContent.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить настройки сайта'))
  } finally {
    settingsLoading.value = false
  }
})

function validateField(field, value, message) {
  if (!value.trim()) return setError(field, message)
  clearError(field)
}

function validateEmail() {
  if (!owner.email) return setError('email', 'Укажите email')
  if (!/^\S+@\S+\.\S+$/.test(owner.email)) return setError('email', 'Некорректный email')
  clearError('email')
}

function validatePassword() {
  if (owner.password.length < 8) return setError('password', 'Минимум 8 символов')
  clearError('password')
}

function validateConfirmPassword() {
  if (owner.confirm_password !== owner.password) return setError('confirm_password', 'Пароли не совпадают')
  clearError('confirm_password')
}

function validateSetupToken() {
  if (setup.requiresToken && !setupToken.value.trim()) return setError('setup_token', 'Укажите код настройки')
  clearError('setup_token')
}

function validateStep1() {
  validateField('first_name', owner.first_name, 'Укажите имя')
  validateField('last_name', owner.last_name, 'Укажите фамилию')
  validateEmail()
  validatePassword()
  validateConfirmPassword()
  validateSetupToken()
  return !Object.keys(errors).length
}

function validateStep2() {
  validateField('salon_name', salon.name, 'Укажите название точки')
  validateField('salon_address', salon.address, 'Укажите адрес')
  // Та же граница, что и CHECK ck_salons_close_after_open на бэкенде —
  // ловим до запроса, чтобы показать поле, а не общий тост.
  if (salon.close_time <= salon.open_time) {
    setError('salon_hours', 'Время закрытия должно быть позже времени открытия')
  } else {
    clearError('salon_hours')
  }
  return !Object.keys(errors).length
}

async function onSubmitStep() {
  if (step.value === 1) {
    if (!validateStep1()) return
    step.value = 2
    return
  }
  if (step.value === 2) {
    if (!validateStep2()) return
    step.value = 3
    return
  }
  if (step.value === 3) {
    step.value = 4
    return
  }
  await finish()
}

function siteContentWithSalonFooter() {
  // footer.address/hours пока живут в контенте сайта (AppFooter.vue читает
  // именно их), но фактически описывают точку — спрашивать их вторым
  // экраном после шага «первая точка» значило бы задать один вопрос дважды.
  // Заполняем из салона. Когда AppFooter перейдёт на список точек
  // (ROADMAP.md §4.9), эти два поля уйдут из схемы вместе с ним.
  if (!siteContent.value) return null
  return {
    ...siteContent.value,
    footer: {
      ...siteContent.value.footer,
      address: salon.address,
      hours: `Ежедневно ${salon.open_time.slice(0, 5)}–${salon.close_time.slice(0, 5)}`,
    },
  }
}

async function finish() {
  loading.value = true
  try {
    const res = await setupApi.complete({
      owner: {
        first_name: owner.first_name,
        last_name: owner.last_name,
        email: owner.email,
        phone: owner.phone || null,
        password: owner.password,
      },
      salon: {
        name: salon.name,
        address: salon.address,
        phone: salon.phone || null,
        open_time: salon.open_time,
        close_time: salon.close_time,
      },
      site_content: siteContentWithSalonFooter(),
      setup_token: setupToken.value || null,
    })
    auth.user = res.data.user
    // ready=true — избегаем лишнего fetchMe() в router-guard сразу после этого:
    // /setup — единственный флоу, где guard ещё ни разу не трогал auth.fetchMe()
    // (его собственная ветка про !setup.completed возвращается раньше), поэтому
    // ready тут всё ещё false. Без этой строки следующая же навигация (на
    // admin-stats) дёргает GET /auth/me, а он гоняется с тем же коммитом,
    // что и сам /api/setup (pg_advisory_xact_lock) — маленькое, но полностью
    // воспроизводимое окно 401 "Пользователь не найден" сразу после успешной
    // настройки. У login()/register() та же проблема отсутствует только
    // потому, что ready уже true к моменту их вызова (fetchMe() при самой
    // первой загрузке SPA).
    auth.ready = true
    setup.markCompleted()
    toast.success('Настройка завершена — добро пожаловать!')
    router.push({ name: 'admin-stats' })
  } catch (err) {
    if (err.response?.status === 404) {
      setup.markCompleted()
      toast.error('Настройка уже была выполнена ранее')
      router.push({ name: 'login' })
      return
    }
    if (err.response?.status === 403) {
      clearAll()
      setError('setup_token', extractErrorMessage(err, 'Неверный код настройки'))
      step.value = 1
      return
    }
    clearAll()
    if (setFromResponse(err)) {
      // Вернуть пользователя на тот шаг, где лежит поле с ошибкой, иначе он
      // видит подсветку на экране, который сейчас не показан.
      if (['email', 'password', 'first_name', 'last_name', 'phone'].some((f) => f in errors)) {
        step.value = 1
      } else if (['name', 'address', 'open_time', 'close_time'].some((f) => f in errors)) {
        step.value = 2
      }
    } else {
      toast.error(extractErrorMessage(err, 'Не удалось завершить настройку'))
    }
  } finally {
    loading.value = false
  }
}
</script>
