import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import eslintConfigPrettier from 'eslint-config-prettier'
import globals from 'globals'

export default [
  { ignores: ['dist/**'] },
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  // Отключает стилевые правила, конфликтующие с Prettier — сам Prettier
  // пока не форсируется в CI (см. .prettierrc.json/package.json), но
  // конфиг держим согласованным на будущее, если/когда его включат.
  eslintConfigPrettier,
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
      },
    },
    rules: {
      // `const { password_confirm, ...payload } = form` — деструктуризация
      // именно чтобы ИСКЛЮЧИТЬ поле из payload на бэкенд (RegisterPage.vue),
      // не забытая переменная.
      'no-unused-vars': ['error', { ignoreRestSiblings: true }],
      // "Pagination"/"Skeleton" ни с чем не конфликтуют — оригинальный смысл
      // правила (не путать с будущими нативными HTML-тегами) тут неприменим.
      'vue/multi-word-component-names': 'off',
    },
  },
  {
    // HomePreview.vue — визуальный live-редактор контента страницы
    // (AdminSettingsLive.vue): content — общий с родителем объект черновика,
    // прямая мутация вложенных полей (v-model/@click на content.hero.*) —
    // осознанный паттерн двусторонней привязки для редактора, не баг.
    files: ['src/components/HomePreview.vue'],
    rules: {
      'vue/no-mutating-props': 'off',
    },
  },
  {
    // Конфиги инструментов и тесты (Vitest/Playwright) выполняются в Node,
    // не в браузере — им нужен process/__dirname и т.п., которых нет в src.
    files: ['*.config.js', 'tests/**/*.js'],
    languageOptions: {
      globals: { ...globals.node },
    },
  },
]
