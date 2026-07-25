import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { salonsApi } from '../api'

/**
 * Точки сети (ROADMAP.md §4.9). Грузится один раз в App.vue, как siteContent.
 *
 * Важно: GET /api/salons отдаёт РАЗНЫЙ список в зависимости от того, кто
 * спрашивает — закрытые точки видят только admin/owner. Поэтому админка
 * (AdminPanel.vue) перезапрашивает список с force=true при входе в панель,
 * а публичные экраны (футер, секция на главной) читают activeSalons и
 * остаются корректными, даже если в сторе лежит расширенный список.
 */
export const useSalonStore = defineStore('salon', () => {
  const salons = ref([])
  const loaded = ref(false)
  // null = «вся сеть». Актуально только для owner: у admin выбор один — его
  // домашняя точка, бэкенд всё равно принудит её (см. resolve_salon_scope).
  const viewingSalonId = ref(null)

  const activeSalons = computed(() => salons.value.filter((s) => s.is_active))
  const byId = computed(() =>
    Object.fromEntries(salons.value.map((s) => [s.id, s])),
  )
  const viewingSalon = computed(() =>
    viewingSalonId.value ? byId.value[viewingSalonId.value] ?? null : null,
  )

  async function load(force = false) {
    if (loaded.value && !force) return
    try {
      const { data } = await salonsApi.list()
      salons.value = data
    } finally {
      loaded.value = true
    }
  }

  function setViewing(id) {
    viewingSalonId.value = id || null
  }

  /** После создания/редактирования точки — чтобы переключатель и футер не отстали. */
  async function refresh() {
    await load(true)
  }

  return {
    salons, activeSalons, loaded, viewingSalonId, viewingSalon, byId,
    load, refresh, setViewing,
  }
})
