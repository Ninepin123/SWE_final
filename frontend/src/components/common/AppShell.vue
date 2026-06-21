<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const ALL_ROLES = ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN']
const NON_ADMIN_ROLES = ALL_ROLES.filter((role) => role !== 'ADMIN')

const navGroups = [
  {
    label: '主要功能',
    items: [
      {
        label: '系統總覽',
        to: '/dashboard',
        roles: ALL_ROLES,
        icon: 'dashboard',
      },
      {
        label: '可申請獎學金',
        to: '/scholarships',
        roles: ['STUDENT'],
        icon: 'scholarship',
      },
      {
        label: '我的申請',
        to: '/applications',
        roles: ['STUDENT'],
        icon: 'application',
      },
      {
        label: '個人資料',
        to: '/profile',
        roles: ['STUDENT'],
        icon: 'profile',
      },
      {
        label: '申請案審查',
        to: '/reviews',
        roles: ['REVIEWER'],
        icon: 'review',
      },
      {
        label: '核發名單',
        to: '/award-list',
        roles: ['REVIEWER', 'ADMIN'],
        icon: 'list',
      },
      {
        label: '年度統計與報表',
        to: '/statistics',
        roles: ['REVIEWER', 'ADMIN'],
        icon: 'chart',
      },
      {
        label: '推薦信邀請',
        to: '/recommendations',
        roles: ['TEACHER'],
        icon: 'recommend',
      },
    ],
  },
  {
    label: 'NCS 通知與溝通',
    items: [
      {
        label: '公告中心',
        to: '/announcements',
        roles: NON_ADMIN_ROLES,
        icon: 'archive',
      },
      {
        label: '通知中心',
        to: '/notifications',
        roles: NON_ADMIN_ROLES,
        icon: 'bell',
      },
      {
        label: '問題回報',
        to: '/issues',
        roles: NON_ADMIN_ROLES,
        icon: 'review',
      },
    ],
  },
  {
    label: '系統管理',
    items: [
      {
        label: '單位管理',
        to: '/admin/units',
        roles: ['ADMIN'],
        icon: 'building',
      },
      {
        label: '科系與部門管理',
        to: '/admin/departments',
        roles: ['ADMIN'],
        icon: 'graduation',
      },
      {
        label: '帳號管理',
        to: '/admin/users',
        roles: ['ADMIN'],
        icon: 'admin',
      },
      {
        label: '獎學金管理',
        to: '/admin/scholarships',
        roles: ['SPONSOR', 'ADMIN'],
        icon: 'manage',
      },
      {
        label: '公告管理',
        to: '/admin/announcements',
        roles: ['ADMIN'],
        icon: 'archive',
      },
      {
        label: '問題回報管理',
        to: '/admin/issues',
        roles: ['ADMIN'],
        icon: 'review',
      },
      {
        label: '系統警示',
        to: '/admin/system-alerts',
        roles: ['ADMIN'],
        icon: 'bell',
      },
      {
        label: '稽核日誌',
        to: '/admin/audit-logs',
        roles: ['ADMIN'],
        icon: 'archive',
      },
    ],
  },
]

const currentRole = computed(() => auth.user?.role ?? auth.role)

const isAdmin = computed(() => currentRole.value === 'ADMIN')

// 管理員的「公告中心」與「公告管理」合併，快捷鈕直接導向公告管理頁面。
const announcementsTo = computed(() => (isAdmin.value ? '/admin/announcements' : '/announcements'))

const visibleGroups = computed(() =>
  navGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => item.roles.includes(currentRole.value)),
    }))
    .filter((group) => group.items.length > 0),
)

const pageShellClass = computed(() => ({
  'page-shell--wide': route.meta.widePage,
}))

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/dashboard">
        <span class="brand__mark seal" aria-hidden="true">奬</span>
        <span class="brand__body">
          <strong>高大獎助學金</strong>
          <small>NUKSAMS · 獎學金系統</small>
        </span>
      </RouterLink>

      <nav aria-label="主要導覽">
        <div
          v-for="group in visibleGroups"
          :key="group.label"
          class="sidebar__group"
        >
          <p class="sidebar__group-label">
            {{ group.label }}
          </p>

          <div class="sidebar__nav">
            <RouterLink
              v-for="item in group.items"
              :key="item.to"
              class="sidebar__link"
              :to="item.to"
            >
              <Icon :name="item.icon" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </div>
        </div>
      </nav>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="topbar__title">
          <p class="eyebrow">NUKSAMS</p>
          <h1>{{ route.meta.title || '獎學金申請與審查系統' }}</h1>
        </div>

        <div class="topbar__actions">
          <div class="user-chip">
            <strong>{{ auth.user?.name ?? '使用者' }}</strong>
            <span>{{ auth.roleLabel }}</span>
          </div>

          <button
            type="button"
            class="icon-button"
            :title="isAdmin ? '公告管理' : '公告中心'"
            @click="router.push(announcementsTo)"
          >
            <Icon name="archive" />
          </button>

          <button
            v-if="!isAdmin"
            type="button"
            class="icon-button"
            title="通知中心"
            @click="router.push('/notifications')"
          >
            <Icon name="bell" />
          </button>

          <button type="button" class="ghost-button" @click="logout">
            <Icon name="logout" />
            登出
          </button>
        </div>
      </header>

      <main class="page-shell" :class="pageShellClass">
        <RouterView />
      </main>
    </div>
  </div>
</template>
