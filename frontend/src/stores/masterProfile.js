import { defineStore } from 'pinia'
import { ref } from 'vue'
import { mastersApi } from '../api'

/** Кэш профиля мастера для текущего пользователя — нужен во всех вкладках кабинета. */
export const useMasterProfileStore = defineStore('masterProfile', () => {
  const profile = ref(null)
  const loaded = ref(false)

  async function load(force = false) {
    if (loaded.value && !force) return
    const { data } = await mastersApi.getMe()
    profile.value = data
    loaded.value = true
  }

  return { profile, loaded, load }
})
