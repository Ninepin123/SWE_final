// NCS — 路由
export default [
  { path: '/ncs/notifications', name: 'ncs-notifications', component: () => import('@/views/ncs/NotificationsView.vue') },
  { path: '/ncs/announcements', name: 'ncs-announcements', component: () => import('@/views/ncs/AnnouncementsView.vue') },
]
