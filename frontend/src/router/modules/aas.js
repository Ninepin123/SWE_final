// AAS 帳號與權限管理 — 路由（負責人：填上姓名）
// 此檔由 router/index.js 自動載入，只需要 export default 路由陣列。
// 頁面元件放在 src/views/aas/，命名用 PascalCase + View 結尾。
export default [
  {
    path: '/login',
    name: 'aas-login',
    component: () => import('@/views/aas/LoginView.vue'),
    meta: {
      public: true,
      title: '登入',
    },
  },
  {
    path: '/admin/users',
    name: 'aas-users',
    component: () => import('@/views/aas/UserManagementView.vue'),
    meta: {
      title: '帳號管理',
      roles: ['ADMIN'],
    },
  },
  {
    path: '/admin/audit-logs',
    name: 'aas-audit-logs',
    component: () => import('@/views/aas/AuditLogView.vue'),
    meta: {
      title: '稽核日誌',
      roles: ['ADMIN'],
    },
  },
]
