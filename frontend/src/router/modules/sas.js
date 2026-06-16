// SAS 學生申請 — 路由
export default [
  {
    path: '/sas/apply',
    name: 'sas-apply',
    component: () => import('@/views/sas/ApplyView.vue'),
  },
  {
    path: '/sas/applications',
    name: 'sas-my-applications',
    component: () => import('@/views/sas/MyApplicationsView.vue'),
  },
]
