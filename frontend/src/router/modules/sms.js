// SMS 獎助學金資料管理 — 路由
export default [
  {
    path: '/sms/scholarships',
    name: 'sms-scholarships',
    component: () => import('@/views/sms/ScholarshipListView.vue'),
  },
]
