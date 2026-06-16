// RAS 審查與核發 — 路由
export default [
  {
    path: '/ras/applications',
    name: 'ras-applications',
    component: () => import('@/views/ras/ReviewListView.vue'),
  },
]
