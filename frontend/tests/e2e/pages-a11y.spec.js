// Регрессия доступности (axe-core) на нескольких ключевых публичных
// страницах — закрепляет уже сделанную вручную a11y-работу (клавиатурная
// навигация, контраст, ARIA), чтобы те же проблемы не вернулись незаметно.
// Не полный аудит (axe ловит ~30-50% проблем доступности автоматически,
// остальное — по-прежнему ручная проверка), а именно регрессионный тест.
//
// Требует уже настроенный сайт (первый admin создан, есть контент) — на
// пустой БД всё, кроме /setup, редиректит на /setup (router-guard). В CI
// (джоба frontend-e2e) это гарантируется порядком файлов: при
// `workers: 1`/`fullyParallel: false` (playwright.config.js) Playwright
// прогоняет спек-файлы в алфавитном порядке пути, а «core-flows» < «pages»
// — так что core-flows.spec.js успевает пройти /setup первым. Для
// локального прогона — то же самое: сначала `npx playwright test
// core-flows`, потом уже этот файл (или просто `npx playwright test` без
// фильтра, порядок тот же).
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

async function expectNoViolations(page) {
  const results = await new AxeBuilder({ page }).analyze()
  if (results.violations.length === 0) return
  const summary = results.violations
    .map((v) => `- [${v.impact}] ${v.id}: ${v.description} (${v.nodes.length} элемент(ов): ${v.nodes.map((n) => n.target.join(' ')).join(', ')})`)
    .join('\n')
  expect(summary, `axe нашёл нарушения доступности:\n${summary}`).toBe('')
}

test.describe('Доступность (axe-core)', () => {
  test('главная страница', async ({ page }) => {
    await page.goto('/')
    await expectNoViolations(page)
  })

  test('каталог мастеров', async ({ page }) => {
    await page.goto('/masters')
    await expectNoViolations(page)
  })

  test('вход', async ({ page }) => {
    await page.goto('/login')
    await expectNoViolations(page)
  })
})
