<template>
  <DashboardLayout :title="pageTitle">
    <template #nav>
      <SidebarLink :to="{ name: 'dashboard-appointments' }" label="Мои записи" :icon="CalendarDaysIcon" />
      <SidebarLink :to="{ name: 'dashboard-schedule' }" label="Расписание" :icon="ClockIcon" />
      <SidebarLink :to="{ name: 'dashboard-reviews' }" label="Отзывы" :icon="StarIcon" />
    </template>

    <Skeleton v-if="!profileStore.loaded" height="h-64" />
    <router-view v-else />
  </DashboardLayout>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { CalendarDaysIcon, ClockIcon, StarIcon } from '@heroicons/vue/24/outline'
import DashboardLayout from '../components/DashboardLayout.vue'
import SidebarLink from '../components/SidebarLink.vue'
import Skeleton from '../components/ui/Skeleton.vue'
import { useMasterProfileStore } from '../stores/masterProfile'
import { useToastStore } from '../stores/toast'
import { extractErrorMessage } from '../utils/errors'

const route = useRoute()
const profileStore = useMasterProfileStore()
const toast = useToastStore()

const titles = {
  'dashboard-appointments': 'Мои записи',
  'dashboard-schedule': 'Расписание',
  'dashboard-reviews': 'Отзывы',
}
const pageTitle = computed(() => titles[route.name] ?? 'Кабинет мастера')

onMounted(async () => {
  try {
    await profileStore.load()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'Не удалось загрузить профиль мастера'))
  }
})
</script>
