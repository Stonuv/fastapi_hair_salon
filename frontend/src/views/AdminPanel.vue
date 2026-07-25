<template>
  <DashboardLayout :title="pageTitle">
    <template #nav>
      <SidebarLink :to="{ name: 'admin-stats' }" label="Статистика" :icon="ChartBarIcon" />
      <SidebarLink :to="{ name: 'admin-users' }" label="Пользователи" :icon="UsersIcon" />
      <SidebarLink :to="{ name: 'admin-services' }" label="Услуги" :icon="ScissorsIcon" />
      <SidebarLink :to="{ name: 'admin-masters' }" label="Мастера" :icon="UserGroupIcon" />
      <SidebarLink :to="{ name: 'admin-reviews' }" label="Отзывы" :icon="StarIcon" />
      <SidebarLink :to="{ name: 'admin-reports' }" label="Отчёты" :icon="DocumentChartBarIcon" />
      <!-- Контент сайта — бренд всей сети, PATCH /api/settings owner-only
           (ROADMAP.md §4.4): администратору точки пункт не показываем, иначе
           он вёл бы на экран, который отдаёт 403 при сохранении. -->
      <SidebarLink v-if="auth.isOwner" :to="{ name: 'admin-settings' }" label="Настройки" :icon="PencilSquareIcon" />
    </template>

    <router-view />
  </DashboardLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChartBarIcon, UsersIcon, ScissorsIcon, UserGroupIcon, StarIcon, DocumentChartBarIcon, PencilSquareIcon } from '@heroicons/vue/24/outline'
import DashboardLayout from '../components/DashboardLayout.vue'
import SidebarLink from '../components/SidebarLink.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const titles = {
  'admin-stats': 'Статистика',
  'admin-users': 'Пользователи',
  'admin-services': 'Услуги',
  'admin-masters': 'Мастера',
  'admin-reviews': 'Отзывы',
  'admin-reports': 'Отчёты',
}
const pageTitle = computed(() => titles[route.name] ?? 'Админ-панель')
</script>
