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
  {
    path: '/announcements',
    name: 'ncs-announcements',
    component: () => import('@/views/ncs/AnnouncementsView.vue'),
    meta: {
      title: '公告中心',
      roles: ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN'],
    },
  },
  {
    path: '/admin/announcements',
    name: 'ncs-announcement-management',
    component: () => import('@/views/ncs/AnnouncementManagementView.vue'),
    meta: {
      title: '公告管理',
      roles: ['ADMIN'],
    },
  },
  {
    path: '/issues',
    name: 'ncs-issues',
    component: () => import('@/views/ncs/IssueReportView.vue'),
    meta: {
      title: '問題回報',
      roles: ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN'],
    },
  },
  {
    path: '/admin/issues',
    name: 'ncs-issue-management',
    component: () => import('@/views/ncs/IssueManagementView.vue'),
    meta: {
      title: '問題回報管理',
      roles: ['ADMIN'],
    },
  },
  {
    path: '/admin/system-alerts',
    name: 'ncs-system-alerts',
    component: () => import('@/views/ncs/SystemAlertsView.vue'),
    meta: {
      title: '系統警示',
      roles: ['ADMIN'],
    },
  },
]