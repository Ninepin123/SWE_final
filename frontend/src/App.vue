<script setup>
// App 殼層（組長維護）：全域導覽列 + 版型。
// 各子系統頁面請寫在 src/views/<子系統>/ 並透過 router 顯示。
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { unreadCount } from '@/api/ncs'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const ROLE_LABEL = {
  STUDENT: '學生', TEACHER: '老師', SPONSOR: '獎助單位', REVIEWER: '審查人員', ADMIN: '系統管理員',
}
const unread = ref(0)

const showNav = computed(() => auth.isLoggedIn && route.path !== '/login')

const links = computed(() => {
  const r = auth.role
  const items = [{ to: '/', text: '首頁' }]
  if (r === 'STUDENT') {
    items.push({ to: '/sas/apply', text: '瀏覽獎學金' })
    items.push({ to: '/sas/applications', text: '我的申請' })
    items.push({ to: '/sas/profile', text: '個人資料' })
  }
  if (r === 'TEACHER') items.push({ to: '/trs/recommendations', text: '推薦邀請' })
  if (r === 'SPONSOR') items.push({ to: '/sms/scholarships', text: '獎學金管理' })
  if (r === 'REVIEWER') items.push({ to: '/ras/applications', text: '審查申請' })
  if (r === 'ADMIN') {
    items.push({ to: '/sms/scholarships', text: '獎學金管理' })
    items.push({ to: '/aas/users', text: '帳號管理' })
    items.push({ to: '/aas/audit-logs', text: '稽核紀錄' })
  }
  items.push({ to: '/ncs/announcements', text: '公告' })
  return items
})

async function refreshUnread() {
  if (!auth.isLoggedIn) { unread.value = 0; return }
  try {
    const { data } = await unreadCount()
    unread.value = data.count || 0
  } catch (e) {
    // 尚未登入或暫時失敗時略過
  }
}

async function logout() {
  await auth.logout()
  router.push('/login')
}

onMounted(refreshUnread)
watch(() => route.fullPath, refreshUnread)
</script>

<template>
  <header v-if="showNav" class="topnav">
    <div class="bar">
      <RouterLink to="/" class="brand">
        <span class="brand__seal seal" aria-hidden="true">奬</span>
        <span class="brand__name">
          <strong>高大獎助學金</strong>
          <small>NUKSAMS</small>
        </span>
      </RouterLink>
      <nav class="links">
        <RouterLink v-for="l in links" :key="l.to" :to="l.to" class="navlink">{{ l.text }}</RouterLink>
      </nav>
      <div class="right">
        <RouterLink to="/ncs/notifications" class="bell" title="通知">
          <span class="bell-ic">🔔</span>
          <span v-if="unread > 0" class="badge">{{ unread }}</span>
        </RouterLink>
        <span class="who">{{ auth.user?.name }}（{{ ROLE_LABEL[auth.role] || auth.role }}）</span>
        <button class="logout" @click="logout">登出</button>
      </div>
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
.topnav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(253, 251, 246, 0.88);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--line);
}
.bar { max-width: 1120px; margin: 0 auto; display: flex; align-items: center; gap: 16px; padding: 12px 22px; flex-wrap: wrap; }

.brand { display: flex; align-items: center; gap: 11px; text-decoration: none; }
.brand__seal { width: 38px; height: 38px; font-size: 22px; }
.brand__name { display: grid; line-height: 1.2; }
.brand__name strong { font-family: var(--font-serif); font-size: 16px; font-weight: 600; color: var(--text); }
.brand__name small { color: var(--muted); font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.12em; }

.links { display: flex; gap: 2px; flex-wrap: wrap; flex: 1; }
.navlink { color: var(--text-secondary); text-decoration: none; padding: 7px 12px; border-radius: var(--radius-sm); font-size: 14px; font-weight: 600; transition: background 0.12s ease, color 0.12s ease; }
.navlink:hover { background: var(--surface-muted); color: var(--text); }
.navlink.router-link-exact-active { background: var(--primary-soft); color: var(--primary); }

.right { display: flex; align-items: center; gap: 12px; }
.bell { position: relative; text-decoration: none; font-size: 18px; line-height: 1; }
.bell-ic { filter: grayscale(.1); }
.badge { position: absolute; top: -8px; right: -10px; background: var(--seal); color: #fff; font-size: 11px; min-width: 17px; height: 17px; line-height: 17px; text-align: center; border-radius: 9px; padding: 0 4px; font-weight: 700; }
.who { font-size: 13px; color: var(--text-secondary); }
.logout { background: transparent; color: var(--text-secondary); border: 1px solid var(--line-strong); padding: 7px 13px; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; font-weight: 600; transition: background 0.12s ease, border-color 0.12s ease; }
.logout:hover { background: var(--surface-muted); border-color: var(--primary); color: var(--primary); }
</style>
