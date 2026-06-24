<template>
  <div>
    <Skeleton v-if="loading" height="h-96" />
    <div v-else class="space-y-3">
      <BaseCard v-for="day in days" :key="day.value" class="flex flex-wrap items-center gap-4">
        <label class="flex w-32 flex-shrink-0 items-center gap-2 font-medium text-ink-900">
          <input
            type="checkbox"
            class="h-5 w-5 cursor-pointer rounded border-stone-200 text-brand-900 focus:ring-brand-900/30"
            v-model="day.is_working"
          />
          {{ day.label }}
        </label>
        <template v-if="day.is_working">
          <BaseInput v-model="day.start_time" type="time" class="w-36" />
          <span class="text-ink-600">—</span>
          <BaseInput v-model="day.end_time" type="time" class="w-36" />
        </template>
        <span v-else class="text-sm text-ink-600">Выходной</span>
        <BaseButton
          size="sm"
          variant="ghost"
          class="ml-auto"
          :loading="saving === day.value"
          @click="saveDay(day)"
        >
          Сохранить
        </BaseButton>
      </BaseCard>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { mastersApi } from '../../api'
import { useMasterProfileStore } from '../../stores/masterProfile'
import { useToastStore } from '../../stores/toast'
import { extractErrorMessage } from '../../utils/errors'
import BaseCard from '../../components/ui/BaseCard.vue'
import BaseInput from '../../components/ui/BaseInput.vue'
import BaseButton from '../../components/ui/BaseButton.vue'
import Skeleton from '../../components/ui/Skeleton.vue'

const profileStore = useMasterProfileStore()
const toast = useToastStore()

const labels = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Субботa', 'Воскресенье']
const days = reactive(
  labels.map((label, value) => ({ value, label, is_working: false, start_time: '09:00', end_time: '18:00' }))
)
const loading = ref(true)
const saving = ref(null)

onMounted(async () => {
  try {
    const { data } = await mastersApi.getSchedule(profileStore.profile.id)
    for (const entry of data) {
      const day = days[entry.day_of_week]
      day.is_working = entry.is_working
      day.start_time = entry.start_time.slice(0, 5)
      day.end_time = entry.end_time.slice(0, 5)
    }
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить расписание'))
  } finally {
    loading.value = false
  }
})

async function saveDay(day) {
  saving.value = day.value
  try {
    await mastersApi.setSchedule(profileStore.profile.id, {
      day_of_week: day.value,
      start_time: `${day.start_time}:00`,
      end_time: `${day.end_time}:00`,
      is_working: day.is_working,
    })
    toast.success(`Расписание на ${day.label.toLowerCase()} сохранено`)
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось сохранить расписание'))
  } finally {
    saving.value = null
  }
}
</script>
