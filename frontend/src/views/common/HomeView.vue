<script setup>
// 系統首頁 / 個人主控台。
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const ROLE_LABEL = {
  STUDENT: '學生', TEACHER: '老師', SPONSOR: '獎助單位', REVIEWER: '審查人員', ADMIN: '系統管理員',
}

const links = computed(() => {
  const r = auth.role
  const all = []
  if (r === 'STUDENT') {
    all.push({ to: '/sas/apply', text: '申請獎學金' })
    all.push({ to: '/sas/applications', text: '我的申請進度' })
  }
  if (r === 'SPONSOR' || r === 'ADMIN') all.push({ to: '/sms/scholarships', text: '獎學金管理' })
  if (r === 'REVIEWER' || r === 'ADMIN') all.push({ to: '/ras/applications', text: '審查申請案' })
  if (r === 'ADMIN') all.push({ to: '/aas/users', text: '帳號管理' })
  // 所有登入者都能瀏覽獎學金列表
  if (r && r !== 'SPONSOR' && r !== 'ADMIN') all.push({ to: '/sms/scholarships', text: '瀏覽獎學金' })
  return all
})

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <main class="home">
    <h1>NUKSAMS 高雄大學獎(助)學金申請與管理系統</h1>

    <template v-if="auth.isLoggedIn">
      <p class="hello">
        你好，{{ auth.user?.name }}（{{ ROLE_LABEL[auth.role] || auth.role }}）
        <button class="link" @click="logout">登出</button>
      </p>
      <div class="grid">
        <RouterLink v-for="l in links" :key="l.to" :to="l.to" class="tile">{{ l.text }}</RouterLink>
      </div>
    </template>

    <template v-else>
      <p>請先登入以使用系統。</p>
      <RouterLink to="/login" class="tile solo">前往登入</RouterLink>
    </template>

    <p class="note">這是 v1 初版（核心流程）。完整功能與開發方式見 <code>docs/V1_SLICE.md</code> 與 <code>docs/DEVELOPMENT.md</code>。</p>
  </main>
</template>

<style scoped>
.home { max-width: 760px; margin: 6vh auto; padding: 0 16px; font-family: system-ui, sans-serif; }
h1 { font-size: 22px; }
.hello { color: #333; display: flex; align-items: center; gap: 12px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin: 16px 0; }
.tile { display: block; padding: 18px; border: 1px solid #e3e3e3; border-radius: 12px; text-decoration: none; color: #2b6cb0; font-weight: 600; background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,.04); }
.tile:hover { border-color: #2b6cb0; }
.solo { max-width: 220px; }
.link { background: none; border: none; color: #2b6cb0; cursor: pointer; text-decoration: underline; font-size: 14px; }
.note { color: #888; font-size: 13px; margin-top: 24px; }
code { background: #eef; padding: 1px 5px; border-radius: 4px; }
</style>
