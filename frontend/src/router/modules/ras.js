// RAS 審查與核發 — 路由（負責人：填上姓名）
// 此檔由 router/index.js 自動載入，只需要 export default 路由陣列。
// 頁面元件放在 src/views/ras/，命名用 PascalCase + View 結尾。
export default [
  {
    path: '/reviews',
    name: 'ras-reviews',
    component: () => import('@/views/ras/ReviewQueueView.vue'),
    meta: {
      title: '申請案審查',
      roles: ['REVIEWER'],
    },
  },
]
