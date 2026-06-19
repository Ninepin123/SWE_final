<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { ROLE_LABELS } from '@/api/aas'
import { useMockApi } from '@/api/http'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

// 導覽項目依角色分組：主要操作 / 系統管理 / 通用
const navGroups = [
  {
    label: '主要功能',
    items: [
      { label: '系統總覽', to: '/dashboard', roles: ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN'], icon: 'dashboard' },
      { label: '可申請獎學金', to: '/scholarships', roles: ['STUDENT'], icon: 'scholarship' },
      { label: '我的申請', to: '/applications', roles: ['STUDENT'], icon: 'application' },
      { label: '個人資料', to: '/profile', roles: ['STUDENT'], icon: 'profile' },
      { label: '申請案審查', to: '/reviews', roles: ['REVIEWER'], icon: 'review' },
      { label: '推薦信邀請', to: '/recommendations', roles: ['TEACHER'], icon: 'recommend' },
    ],
  },
  {
    label: '系統管理',
    items: [
      { label: '帳號管理', to: '/admin/users', roles: ['ADMIN'], icon: 'admin' },
      { label: '稽核日誌', to: '/admin/audit-logs', roles: ['ADMIN'], icon: 'archive' },
      { label: '獎學金管理', to: '/admin/scholarships', roles: ['SPONSOR', 'ADMIN'], icon: 'manage' },
    ],
  },
  {
    label: '其他',
    items: [
      { label: '通知中心', to: '/notifications', roles: ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN'], icon: 'notification' },
    ],
  },
]

const visibleGroups = computed(() =>
  navGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => item.roles.includes(auth.user?.role)),
    }))
    .filter((group) => group.items.length),
)

const roleOptions = computed(() =>
  Object.entries(ROLE_LABELS)
    .map(([value, label]) => ({ value, label })),
)

async function switchRole(event) {
  await auth.loginAs(event.target.value)
  toast.info(`已切換為${auth.roleLabel}`)
  router.push('/dashboard')
}

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
        <div v-for="group in visibleGroups" :key="group.label" class="sidebar__group">
          <p class="sidebar__group-label">{{ group.label }}</p>
          <div class="sidebar__nav">
            <RouterLink
              v-for="item in group.items"
              :key="item.to"
              class="sidebar__link"
              :to="item.to"
            >
              <Icon :name="item.icon" />
              {{ item.label }}
            </RouterLink>
          </div>
        </div>
      </nav>

      <p v-if="useMockApi" class="sidebar__dev-note">測試模式 · mock 後端運作中</p>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="topbar__title">
          <p class="eyebrow">NUKSAMS</p>
          <h1>{{ route.meta.title || '獎學金申請與審查系統' }}</h1>
        </div>
        <div class="topbar__actions">
          <!-- 開發期角色切換器：正式環境透過 body.dev-mode 控制顯示 -->
          <label class="role-switcher dev-only">
            <span>測試角色</span>
            <select :value="auth.role" @change="switchRole">
              <option v-for="option in roleOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <div class="user-chip">
            <strong>{{ auth.user?.name }}</strong>
            <span>{{ auth.roleLabel }}</span>
          </div>
          <button type="button" class="icon-button" title="通知" @click="router.push('/notifications')">
            <Icon name="bell" />
          </button>
          <button type="button" class="ghost-button" @click="logout">
            <Icon name="logout" />
            登出
          </button>
        </div>
      </header>

      <main class="page-shell">
        <RouterView />
      </main>
    </div>
  </div>
</template>
