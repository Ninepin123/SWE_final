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
      <RouterLink to="/" class="brand">NUKSAMS</RouterLink>
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
.topnav { background: #1f3a5f; color: #fff; box-shadow: 0 2px 8px rgba(0, 0, 0, .15); position: sticky; top: 0; z-index: 50; }
.bar { max-width: 1100px; margin: 0 auto; display: flex; align-items: center; gap: 14px; padding: 10px 16px; flex-wrap: wrap; }
.brand { color: #fff; font-weight: 800; font-size: 18px; letter-spacing: .5px; text-decoration: none; }
.links { display: flex; gap: 4px; flex-wrap: wrap; flex: 1; }
.navlink { color: #cdd9ea; text-decoration: none; padding: 6px 10px; border-radius: 8px; font-size: 14px; }
.navlink:hover { background: rgba(255, 255, 255, .12); color: #fff; }
.navlink.router-link-exact-active { background: #2b6cb0; color: #fff; }
.right { display: flex; align-items: center; gap: 12px; }
.bell { position: relative; text-decoration: none; font-size: 18px; line-height: 1; }
.bell-ic { filter: grayscale(.1); }
.badge { position: absolute; top: -8px; right: -10px; background: #e53e3e; color: #fff; font-size: 11px; min-width: 17px; height: 17px; line-height: 17px; text-align: center; border-radius: 9px; padding: 0 4px; }
.who { font-size: 13px; color: #e7eef7; }
.logout { background: rgba(255, 255, 255, .14); color: #fff; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 13px; }
.logout:hover { background: rgba(255, 255, 255, .26); }
</style>

<style>
/* 全域基礎樣式（非 scoped） */
* { box-sizing: border-box; }
body { margin: 0; background: #f4f6f9; color: #1a202c; font-family: system-ui, -apple-system, "Noto Sans TC", sans-serif; }
a { color: #2b6cb0; }
</style>
