<template>
  <!-- Владелец сети выбирает область просмотра: вся сеть или конкретная
       точка. Администратор точки выбора не имеет — бэкенд всё равно сузит
       до его собственной (resolve_salon_scope), поэтому вместо неработающего
       select показываем статичную подпись (ROADMAP.md §4.9). -->
  <BaseSelect
    v-if="auth.isOwner"
    :model-value="salonStore.viewingSalonId ?? ''"
    placeholder="Вся сеть"
    aria-label="Точка сети"
    class="w-full sm:w-56"
    @update:model-value="salonStore.setViewing($event)"
  >
    <option v-for="s in salonStore.salons" :key="s.id" :value="s.id">
      {{ s.name }}{{ s.is_active ? '' : ' (закрыта)' }}
    </option>
  </BaseSelect>

  <p
    v-else-if="auth.salon"
    class="flex items-center gap-1.5 font-mono text-xs uppercase tracking-wide text-ink-600"
  >
    <BuildingStorefrontIcon class="h-4 w-4 shrink-0" aria-hidden="true" />
    {{ auth.salon.name }}
  </p>
</template>

<script setup>
import { BuildingStorefrontIcon } from '@heroicons/vue/24/outline'
import { useAuthStore } from '../stores/auth'
import { useSalonStore } from '../stores/salon'
import BaseSelect from './ui/BaseSelect.vue'

const auth = useAuthStore()
const salonStore = useSalonStore()
</script>
