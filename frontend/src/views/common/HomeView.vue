<script setup>
// 系統首頁 / 個人主控台（依角色顯示功能入口）。
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const ROLE_LABEL = {
  STUDENT: '學生', TEACHER: '老師', SPONSOR: '獎助單位', REVIEWER: '審查人員', ADMIN: '系統管理員',
}

const tiles = computed(() => {
  const r = auth.role
  const list = []
  if (r === 'STUDENT') {
    list.push({ to: '/sas/apply', text: '瀏覽 / 申請獎學金', desc: '查看開放中的獎學金並填寫申請表' })
    list.push({ to: '/sas/applications', text: '我的申請進度', desc: '追蹤審查狀態、邀請老師推薦' })
    list.push({ to: '/sas/profile', text: '個人資料', desc: '維護聯絡方式與緊急聯絡人' })
  }
  if (r === 'TEACHER') {
    list.push({ to: '/trs/recommendations', text: '推薦邀請', desc: '撰寫與送出學生推薦信' })
  }
  if (r === 'SPONSOR') {
    list.push({ to: '/sms/scholarships', text: '獎學金管理', desc: '張貼、修改、關閉本單位獎學金' })
  }
  if (r === 'REVIEWER') {
    list.push({ to: '/ras/applications', text: '審查申請案', desc: '檢視申請與推薦信、做出審查決定' })
  }
  if (r === 'ADMIN') {
    list.push({ to: '/sms/scholarships', text: '獎學金管理', desc: '管理所有單位的獎學金' })
    list.push({ to: '/aas/users', text: '帳號管理', desc: '新增 / 修改 / 刪除使用者帳號' })
    list.push({ to: '/aas/audit-logs', text: '稽核紀錄', desc: '檢視系統重要操作紀錄' })
  }
  list.push({ to: '/ncs/announcements', text: '公告', desc: '查看系統公告' })
  list.push({ to: '/ncs/notifications', text: '我的通知', desc: '申請 / 審查 / 推薦相關通知' })
  return list
})
</script>

<template>
  <main class="home page">
    <header class="page-head">
      <p class="eyebrow">主控台</p>
      <h1>你好，{{ auth.user?.name }}</h1>
      <p>以{{ ROLE_LABEL[auth.role] || auth.role }}身分登入。以下是你目前可進行的作業。</p>
    </header>

    <div class="grid">
      <RouterLink v-for="t in tiles" :key="t.to" :to="t.to" class="tile">
        <span class="tile-title">{{ t.text }}</span>
        <span class="tile-desc">{{ t.desc }}</span>
        <span class="tile-go" aria-hidden="true">→</span>
      </RouterLink>
    </div>

    <p class="note">開發方式與分工見 <code>docs/DEVELOPMENT.md</code>；版本內容見 <code>docs/V1_SLICE.md</code>。</p>
  </main>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.tile {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  text-decoration: none;
  background: var(--surface);
  box-shadow: var(--shadow-xs);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}
.tile:hover { border-color: var(--primary); box-shadow: var(--shadow-sm); transform: translateY(-2px); }
.tile-title { color: var(--text); font-family: var(--font-serif); font-weight: 600; font-size: 18px; }
.tile-desc { color: var(--muted); font-size: 13px; line-height: 1.6; }
.tile-go { position: absolute; top: 18px; right: 18px; color: var(--primary); font-size: 16px; opacity: 0; transition: opacity 0.15s ease, transform 0.15s ease; }
.tile:hover .tile-go { opacity: 1; transform: translateX(2px); }
.note { color: var(--muted); font-size: 13px; margin-top: 26px; }
</style>
