import { defineConfig, devices } from '@playwright/test'

// Сквозные сценарии гоняются против реального backend + Postgres (см.
// tests/e2e/README.md) — так же, как backend/tests/integration/, только
// через реальный браузер и HTTP, а не httpx. CI поднимает backend
// отдельным шагом (.github/workflows/ci.yml, джоба frontend-e2e);
// локально ожидается тот же контракт — уже работающий backend на :8000.
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: process.env.E2E_BASE_URL || 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
