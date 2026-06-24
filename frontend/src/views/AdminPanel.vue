<template>
  <DashboardLayout :title="pageTitle">
    <template #nav>
      <SidebarLink :to="{ name: 'admin-stats' }" label="Статистика" :icon="ChartBarIcon" />
      <SidebarLink :to="{ name: 'admin-users' }" label="Пользователи" :icon="UsersIcon" />
      <SidebarLink :to="{ name: 'admin-services' }" label="Услуги" :icon="ScissorsIcon" />
      <SidebarLink :to="{ name: 'admin-masters' }" label="Мастера" :icon="UserGroupIcon" />
      <SidebarLink :to="{ name: 'admin-reviews' }" label="Отзывы" :icon="StarIcon" />
    </template>

    <router-view />
  </DashboardLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChartBarIcon, UsersIcon, ScissorsIcon, UserGroupIcon, StarIcon } from '@heroicons/vue/24/outline'
import DashboardLayout from '../components/DashboardLayout.vue'
import SidebarLink from '../components/SidebarLink.vue'

const route = useRoute()
const titles = {
  'admin-stats': 'Статистика',
  'admin-users': 'Пользователи',
  'admin-services': 'Услуги',
  'admin-masters': 'Мастера',
  'admin-reviews': 'Отзывы',
}
const pageTitle = computed(() => titles[route.name] ?? 'Админ-панель')
</script>
