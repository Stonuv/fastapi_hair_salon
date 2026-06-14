import { createRouter, createWebHistory } from 'vue-router'
import MastersPage     from '../views/MastersPage.vue'
import BookingPage     from '../views/BookingPage.vue'
import LoginPage       from '../views/LoginPage.vue'
import ProfilePage     from '../views/ProfilePage.vue'
import MasterDashboard from '../views/MasterDashboard.vue'
import AdminPanel      from '../views/AdminPanel.vue'

const routes = [
  { path: '/',            component: MastersPage     },
  { path: '/masters/:id', component: BookingPage     },
  { path: '/login',       component: LoginPage       },
  { path: '/profile',     component: ProfilePage     },
  { path: '/dashboard',   component: MasterDashboard },
  { path: '/admin',       component: AdminPanel      },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
