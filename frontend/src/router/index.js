import { createRouter, createWebHistory } from 'vue-router'
import MastersPage from '../views/MastersPage.vue'
import BookingPage from '../views/BookingPage.vue'
import LoginPage   from '../views/LoginPage.vue'

const routes = [
  { path: '/',            component: MastersPage },
  { path: '/masters/:id', component: BookingPage },
  { path: '/login',       component: LoginPage   },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
