// 路由進入點（組長維護）。
// ⚠️ 各子系統「不要」直接改這個檔案——
//    請把自己的路由寫在 src/router/modules/<子系統>.js（export default 一個陣列），
//    這裡會自動載入合併，避免多人改同一檔造成衝突。
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const moduleRoutes = Object.values(
  import.meta.glob('./modules/*.js', { eager: true }),
).flatMap((m) => m.default ?? [])

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/common/DashboardView.vue'),
      meta: {
        title: '系統總覽',
        roles: ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN'],
      },
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('@/views/common/ForbiddenView.vue'),
      meta: {
        title: '無權限',
      },
    },
    ...moduleRoutes,
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard',
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) {
    return true
  }

  const auth = useAuthStore()
  if (!auth.token) {
    return {
      name: 'aas-login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (!auth.user) {
    await auth.fetchMe()
  }

  const roles = to.meta.roles || []
  if (roles.length && !roles.includes(auth.role)) {
    return {
      name: 'forbidden',
    }
  }

  return true
})

export default router
