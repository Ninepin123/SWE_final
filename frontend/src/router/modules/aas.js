// AAS 帳號與權限管理 — 路由
// 此檔由 router/index.js 自動載入，只需要 export default 路由陣列。
export default [
  {
    path: '/login',
    name: 'aas-login',
    component: () => import('@/views/aas/LoginView.vue'),
  },
  {
    path: '/aas/users',
    name: 'aas-users',
    component: () => import('@/views/aas/UserListView.vue'),
  },
]
