// AAS — 路由
export default [
  { path: '/login', name: 'aas-login', component: () => import('@/views/aas/LoginView.vue') },
  { path: '/aas/users', name: 'aas-users', component: () => import('@/views/aas/UserListView.vue') },
  { path: '/aas/audit-logs', name: 'aas-audit', component: () => import('@/views/aas/AuditLogView.vue') },
]
