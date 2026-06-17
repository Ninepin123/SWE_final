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
      name: 'home',
      component: () => import('@/views/common/HomeView.vue'),
    },
    ...moduleRoutes,
  ],
})

// 全域導航守衛（NUKSAMS039）：未登入只能停在 /login；已登入就別再進 /login。
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path !== '/login' && !auth.isLoggedIn) {
    return { path: '/login' }
  }
  if (to.path === '/login' && auth.isLoggedIn) {
    return { path: '/' }
  }
})

export default router
