import { createRouter, createWebHistory } from 'vue-router'
import { session } from '@/auth/session'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/batches',
      name: 'available-batches',
      component: () => import('../views/AvailableBatchesView.vue'),
      meta: { role: 'charity' },
    },
    {
      path: '/my-batches',
      name: 'my-batches',
      component: () => import('../views/AvailableBatchesView.vue'),
      props: { list: 'donations' },
      meta: { role: 'donor' },
    },
    {
      path: '/my-reservations',
      name: 'my-reservations',
      component: () => import('../views/AvailableBatchesView.vue'),
      props: { list: 'reservations' },
      meta: { role: 'charity' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/AuthView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/AuthView.vue'),
      props: { register: true },
      meta: { guestOnly: true },
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  await session.initializeSession()
  const user = session.user.value

  if (to.meta.role && !user) return { name: 'login' }
  if ((to.meta.guestOnly && user) || (to.meta.role && to.meta.role !== user?.role)) {
    return { name: 'home' }
  }
})

export default router
