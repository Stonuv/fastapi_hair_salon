<template>
  <div>
    <label v-if="label" :for="inputId" class="mb-1.5 block text-sm font-medium text-ink-900">{{ label }}</label>
    <div class="relative">
      <select
        :id="inputId"
        :value="modelValue"
        :aria-label="ariaLabel"
        class="w-full cursor-pointer appearance-none rounded-lg border border-stone-200 bg-white px-3.5 py-2.5 pr-9 text-base transition-colors duration-200 focus:border-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-900/30"
        @change="$emit('update:modelValue', $event.target.value)"
      >
        <!-- Не disabled: во всех текущих применениях placeholder — это реальный
             вариант "сбросить фильтр" (например /masters "Любая услуга"), а не
             просто затравка формы — disabled делал бы его невыбираемым назад
             после того, как выбран другой option (ISSUES #24). -->
        <option v-if="placeholder" value="">{{ placeholder }}</option>
        <slot />
      </select>
      <!-- appearance-none убирает нативную стрелку браузера вместе со всем
           остальным нативным видом (ISSUES #39 — select выглядел как голый
           системный виджет рядом со стилизованными input/button) — рисуем
           свою, некликабельную. -->
      <ChevronDownIcon
        class="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-600"
        aria-hidden="true"
      />
    </div>
  </div>
</template>

<script setup>
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

// Без видимого label вызывающий обязан передать aria-label — иначе select
// долетает до пользователей скринридеров вообще без имени (axe: critical
// select-name). Явный проп, а не $attrs/inheritAttrs:false: большинство
// вызовов передают `class="w-48"` и т.п., рассчитывая, что он попадёт на
// обёртку <div> (управляет шириной, сам <select> и так `w-full`) — общий
// fallthrough увёл бы aria-label туда же, на <div>, не на <select>.
const props = defineProps({
  modelValue: [String, Number],
  label: String,
  placeholder: String,
  id: String,
  ariaLabel: String,
})
defineEmits(['update:modelValue'])
const inputId = props.id || `select-${Math.random().toString(36).slice(2, 9)}`
</script>
