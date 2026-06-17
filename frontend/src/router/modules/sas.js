// SAS 學生申請 — 路由（負責人：填上姓名）
// 此檔由 router/index.js 自動載入，只需要 export default 路由陣列。
// 頁面元件放在 src/views/sas/，命名用 PascalCase + View 結尾。
export default [
  {
    path: '/scholarships/:id/apply',
    name: 'sas-application-wizard',
    component: () => import('@/views/sas/ApplicationWizardView.vue'),
    meta: {
      title: '獎學金申請',
      roles: ['STUDENT'],
    },
  },
  {
    path: '/applications',
    name: 'sas-my-applications',
    component: () => import('@/views/sas/MyApplicationsView.vue'),
    meta: {
      title: '我的申請',
      roles: ['STUDENT'],
    },
  },
  {
    path: '/profile',
    name: 'sas-profile',
    component: () => import('@/views/sas/ProfileView.vue'),
    meta: {
      title: '個人資料',
      roles: ['STUDENT'],
    },
  },
]
