import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSetupStore } from '../stores/setup'

const routes = [
  { path: '/setup', name: 'setup', component: () => import('../views/SetupWizard.vue'), meta: { hideHeader: true } },
  { path: '/', name: 'home', component: () => import('../views/HomePage.vue') },
  { path: '/masters', name: 'masters', component: () => import('../views/MastersPage.vue') },
  { path: '/masters/:id', name: 'master-booking', component: () => import('../views/BookingPage.vue'), props: true },
  { path: '/login', name: 'login', component: () => import('../views/LoginPage.vue'), meta: { guestOnly: true } },
  { path: '/register', name: 'register', component: () => import('../views/RegisterPage.vue'), meta: { guestOnly: true } },
  { path: '/password-reset', name: 'password-reset', component: () => import('../views/PasswordResetPage.vue'), meta: { guestOnly: true } },
  { path: '/profile', name: 'profile', component: () => import('../views/ProfilePage.vue'), meta: { requiresAuth: true } },
  {
    path: '/dashboard',
    component: () => import('../views/MasterDashboard.vue'),
    meta: { requiresAuth: true, roles: ['master'], hideHeader: true },
    children: [
      { path: '', name: 'dashboard-appointments', component: () => import('../views/dashboard/DashboardAppointments.vue') },
      { path: 'schedule', name: 'dashboard-schedule', component: () => import('../views/dashboard/DashboardSchedule.vue') },
      { path: 'reviews', name: 'dashboard-reviews', component: () => import('../views/dashboard/DashboardReviews.vue') },
    ],
  },
  {
    path: '/admin',
    component: () => import('../views/AdminPanel.vue'),
    meta: { requiresAuth: true, roles: ['admin'], hideHeader: true },
    children: [
      { path: '', name: 'admin-stats', component: () => import('../views/admin/AdminStats.vue') },
      { path: 'users', name: 'admin-users', component: () => import('../views/admin/AdminUsers.vue') },
      { path: 'services', name: 'admin-services', component: () => import('../views/admin/AdminServices.vue') },
      { path: 'masters', name: 'admin-masters', component: () => import('../views/admin/AdminMasters.vue') },
      { path: 'reviews', name: 'admin-reviews', component: () => import('../views/admin/AdminReviews.vue') },
      { path: 'settings', name: 'admin-settings', component: () => import('../views/admin/AdminSettings.vue') },
      { path: 'reports', name: 'admin-reports', component: () => import('../views/admin/AdminReports.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundPage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  const setup = useSetupStore()
  if (!setup.checked) {
    await setup.checkStatus()
  }
  if (!setup.completed) {
    return to.name === 'setup' ? true : { name: 'setup' }
  }
  if (setup.completed && to.name === 'setup') {
    return { name: 'home' }
  }

  const auth = useAuthStore()
  if (!auth.ready) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.roles && !to.meta.roles.includes(auth.user?.role)) {
    return { name: 'home' }
  }
  if (to.meta.guestOnly && auth.isLoggedIn) {
    // «Токен протух → редирект на /login?redirect=...», но пользователь уже
    // вошёл в другой вкладке — возвращаем его туда, куда он шёл.
    const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : null
    return redirect || { name: 'home' }
  }
  return true
})

export default router
