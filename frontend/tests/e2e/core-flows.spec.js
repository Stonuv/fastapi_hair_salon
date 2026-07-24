// Сквозные сценарии поверх реального backend + Postgres (не мока) — тот же
// принцип, что backend/tests/integration/, только через настоящий браузер
// и HTTP. Оба теста идут в одном describe.serial и на одной БД: первый
// создаёт единственного на инсталляцию admin через /setup (эндпоинт
// самоблокируется после первого вызова — второй раз его не пройти), второй
// переиспользует те же учётные данные, чтобы засеять услугу/мастера/
// расписание через API, прежде чем вести реального клиента через UI.
//
// Локальный запуск (нужен работающий backend на :8000 с чистой БД,
// см. README «Быстрый старт» — например docker compose up db backend):
//
//     TEST_DATABASE_URL=... alembic upgrade head   # если БД совсем пустая
//     cd frontend && npx playwright test
//
// В CI — джоба frontend-e2e (.github/workflows/ci.yml) поднимает Postgres
// и backend сама; фронтенд (vite dev server) поднимает сам Playwright
// (см. webServer в playwright.config.js).
import { test, expect } from '@playwright/test'

test.describe.configure({ mode: 'serial' })

const API_URL = process.env.E2E_API_URL || 'http://localhost:8000/api'
const RUN_ID = Date.now()

const ADMIN = {
  first_name: 'Игорь',
  last_name: 'Волков',
  email: `owner.e2e.${RUN_ID}@example.com`,
  password: 'SuperSecret123',
}
const NEW_BRAND_NAME = `Сайтама E2E ${RUN_ID}`

const CLIENT = {
  first_name: 'Анна',
  last_name: 'Смирнова',
  email: `client.e2e.${RUN_ID}@example.com`,
  password: 'ClientSecret123',
}

// Известная гонка backend (не артефакт теста — воспроизводится через
// голый curl, без браузера): запрос, который читает строку, вставленную
// буквально предыдущим запросом той же цепочки (create user → create
// master profile по его id, и т.п.), иногда не находит свежесозданную
// запись. Один и тот же эффект всплывает под разными кодами в зависимости
// от того, ГДЕ в коде лежит проверка "не найдено" — 401 "Пользователь не
// найден" из get_current_user (аутентификация вызывающего) или 404
// "Пользователь не найден" из самого бизнес-метода (напр.
// create_master_profile ищет по id только что созданного пользователя) —
// текст сообщения совпадает не просто так, это одна и та же причина, а не
// два разных бага. Самоисправляется, но не всегда за первую же повторную
// попытку — в наблюдениях окно доходило до ~400мс. См. отчёт в
// сопроводительном сообщении: чинили на месте два похожих бага
// (setup-wizard, logout), но этот — глубже (похоже на протухшее
// соединение в пуле SQLAlchemy) и заслуживает отдельного расследования,
// а не гадания вслепую в коде аутентификации. До починки — ретраи с
// нарастающей паузой именно на эту конкретную ошибку, чтобы сиды
// e2e-теста не были заложниками того же окна гонки.
async function postWithRetry(request, url, options) {
  const delaysMs = [100, 200, 400, 800]
  for (let attempt = 0; attempt <= delaysMs.length; attempt++) {
    const res = await request.post(url, options)
    if (res.ok()) return res
    const body = await res.text()
    // Подстрока "не найден" (без учёта родовых окончаний — "найдена"
    // начинается с тех же 6 букв) ловит все варианты этой гонки разом:
    // "Пользователь не найден" (401, get_current_user), "Мастер {id} не
    // найден" (404, business-логика) и т.п. — сущность каждый раз разная,
    // причина одна и та же.
    const isKnownRace = (res.status() === 401 || res.status() === 404) && body.includes('не найден')
    if (!isKnownRace || attempt === delaysMs.length) return res
    await new Promise((resolve) => setTimeout(resolve, delaysMs[attempt]))
  }
  throw new Error('unreachable')
}

test.describe('Сквозные сценарии', () => {
  test('первый запуск, вход администратора и изменение настроек сайта', async ({ page }) => {
    await test.step('/setup создаёт первого администратора', async () => {
      await page.goto('/setup')
      await page.getByLabel('Имя').fill(ADMIN.first_name)
      await page.getByLabel('Фамилия').fill(ADMIN.last_name)
      await page.getByLabel('Email').fill(ADMIN.email)
      const passwordInputs = page.locator('input[type="password"]')
      await passwordInputs.nth(0).fill(ADMIN.password)
      await passwordInputs.nth(1).fill(ADMIN.password)
      await page.getByRole('button', { name: 'Далее' }).click()

      // Шаг 2 (контент сайта) — значения по умолчанию уже подставлены,
      // ничего менять не нужно для этого сценария.
      await expect(page.getByRole('heading', { name: 'Настройка «Сайтама»' })).toBeVisible()
      await page.getByRole('button', { name: 'Далее' }).click()

      await page.getByRole('button', { name: 'Завершить настройку' }).click()
      await expect(page).toHaveURL(/\/admin$/)
    })

    await test.step('выход и повторный вход через форму логина', async () => {
      await page.getByRole('button', { name: 'Выйти' }).click()
      await expect(page).toHaveURL(/\/login$/)

      await page.getByLabel('Email').fill(ADMIN.email)
      await page.locator('input[type="password"]').fill(ADMIN.password)
      await page.getByRole('button', { name: 'Войти' }).click()
      await expect(page).toHaveURL('/')
    })

    await test.step('изменение настроек сайта в редакторе главной', async () => {
      await page.goto('/admin/settings')
      // Первый .sai-editable на странице — название бренда в шапке сайта
      // (AppHeader рендерится раньше HomePreview/AppFooter в этом редакторе).
      const brandNameInput = page.locator('.sai-editable').first()
      await brandNameInput.fill(NEW_BRAND_NAME)
      await page.getByRole('button', { name: 'Сохранить' }).click()
      await expect(page.getByRole('status').filter({ hasText: 'Настройки сайта сохранены' })).toBeVisible()

      // Перезагрузка — убеждаемся, что сохранилось на сервере, а не только в памяти вкладки.
      await page.reload()
      await expect(page.locator('.sai-editable').first()).toHaveValue(NEW_BRAND_NAME)
    })
  })

  test('клиент регистрируется, бронирует запись и отменяет её', async ({ page, request }) => {
    const serviceName = `Стрижка E2E ${RUN_ID}`
    const masterEmail = `master.e2e.${RUN_ID}@example.com`

    await test.step('сиды через API от имени admin: услуга, мастер, расписание на неделю', async () => {
      const loginRes = await request.post(`${API_URL}/auth/login`, {
        data: { email: ADMIN.email, password: ADMIN.password },
      })
      expect(loginRes.ok(), await loginRes.text()).toBeTruthy()

      const svcRes = await postWithRetry(request, `${API_URL}/services`, {
        data: { name: serviceName, price: 1500, duration_min: 40 },
      })
      expect(svcRes.ok(), await svcRes.text()).toBeTruthy()
      const service = await svcRes.json()

      const userRes = await postWithRetry(request, `${API_URL}/admin/users`, {
        data: {
          first_name: 'Мастер', last_name: 'Тестовый',
          email: masterEmail, phone: null, password: 'MasterSecret123', role: 'master',
        },
      })
      expect(userRes.ok(), await userRes.text()).toBeTruthy()
      const masterUser = await userRes.json()

      const masterRes = await postWithRetry(request, `${API_URL}/admin/users/${masterUser.id}/master`)
      expect(masterRes.ok(), await masterRes.text()).toBeTruthy()
      const master = await masterRes.json()

      const addServiceRes = await postWithRetry(request, `${API_URL}/masters/${master.id}/services`, {
        data: { service_id: service.id, price_override: null },
      })
      expect(addServiceRes.ok(), await addServiceRes.text()).toBeTruthy()

      // Все 7 дней недели — сценарий не завязан на то, каким днём недели
      // окажется "завтра" в момент прогона CI.
      for (let day = 0; day < 7; day++) {
        const schedRes = await postWithRetry(request, `${API_URL}/masters/${master.id}/schedule`, {
          data: { day_of_week: day, start_time: '09:00:00', end_time: '19:00:00', is_working: true },
        })
        expect(schedRes.ok(), await schedRes.text()).toBeTruthy()
      }
    })

    await test.step('регистрация клиента', async () => {
      await page.goto('/register')
      await page.getByLabel('Имя').fill(CLIENT.first_name)
      await page.getByLabel('Фамилия').fill(CLIENT.last_name)
      await page.getByLabel('Email').fill(CLIENT.email)
      const passwordInputs = page.locator('input[type="password"]')
      await passwordInputs.nth(0).fill(CLIENT.password)
      await passwordInputs.nth(1).fill(CLIENT.password)
      await page.getByRole('checkbox').check()
      await page.getByRole('button', { name: 'Зарегистрироваться' }).click()
      await expect(page).toHaveURL('/')
    })

    await test.step('бронирование записи к мастеру', async () => {
      await page.goto('/masters')
      await page.getByRole('link', { name: 'Записаться' }).first().click()

      await page.locator('section').filter({ hasText: 'Услуга' }).getByRole('button', { name: new RegExp(serviceName) }).click()
      // Завтра, а не сегодня — исключает флейк из-за уже прошедшего
      // рабочего времени, если прогон CI стартует поздно вечером по UTC.
      await page.locator('section').filter({ hasText: 'Дата' }).getByRole('button').nth(1).click()
      await page.locator('section').filter({ hasText: 'Время' }).getByRole('button').first().click()

      await page.getByRole('button', { name: 'Записаться' }).click()
      await expect(page.getByText('Запись оформлена')).toBeVisible()
    })

    await test.step('отмена записи в личном кабинете', async () => {
      await page.getByRole('link', { name: 'Мои записи' }).click()
      await expect(page).toHaveURL(/\/profile$/)
      await expect(page.getByText(serviceName)).toBeVisible()

      await page.getByRole('button', { name: 'Отменить' }).click()
      await expect(page.getByRole('status').filter({ hasText: 'Запись отменена' })).toBeVisible()
      await expect(page.getByRole('button', { name: 'Отменить' })).toHaveCount(0)
    })
  })
})
