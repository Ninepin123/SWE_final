// SMS 獎助學金資料管理 — 路由（負責人：填上姓名）
// 此檔由 router/index.js 自動載入，只需要 export default 路由陣列。
// 頁面元件放在 src/views/sms/，命名用 PascalCase + View 結尾。
export default [
  {
    path: '/scholarships',
    name: 'sms-scholarship-list',
    component: () => import('@/views/sms/ScholarshipListView.vue'),
    meta: {
      title: '可申請獎學金',
      roles: ['STUDENT'],
    },
  },
  {
    path: '/admin/scholarships',
    name: 'sms-admin-scholarships',
    component: () => import('@/views/sms/ScholarshipManagementView.vue'),
    meta: {
      title: '獎學金管理',
      roles: ['SPONSOR', 'ADMIN'],
    },
  },
]
