// NCS 通知與溝通 — 路由（負責人：填上姓名）
// 此檔由 router/index.js 自動載入，只需要 export default 路由陣列。
// 頁面元件放在 src/views/ncs/，命名用 PascalCase + View 結尾。
export default [
  {
    path: '/notifications',
    name: 'ncs-notifications',
    component: () => import('@/views/ncs/NotificationsView.vue'),
    meta: {
      title: '通知中心',
      roles: ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN'],
    },
  },
]
