// TRS — 路由（老師撰寫推薦信頁；學生端動作在「我的申請進度」內）
export default [
  { path: '/trs/recommendations', name: 'trs-teacher', component: () => import('@/views/trs/TeacherRecommendationsView.vue') },
]
