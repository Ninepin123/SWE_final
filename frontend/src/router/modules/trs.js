// TRS 教師推薦 — 路由（負責人：填上姓名）
// 此檔由 router/index.js 自動載入，只需要 export default 路由陣列。
// 頁面元件放在 src/views/trs/，命名用 PascalCase + View 結尾。
export default [
  {
    path: '/recommendations',
    name: 'trs-recommendations',
    component: () => import('@/views/trs/RecommendationRequestsView.vue'),
    meta: {
      title: '推薦信邀請',
      roles: ['RECOMMENDER'],
    },
  },
]
