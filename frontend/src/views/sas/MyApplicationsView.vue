<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listMyApplications } from '@/api/sas'

const router = useRouter()
const auth = useAuthStore()

const items = ref([])
const error = ref('')

const STATUS = {
  UNDER_REVIEW: { label: '審核中', cls: 'review' },
  NEED_SUPPLEMENT: { label: '需補件', cls: 'supplement' },
  APPROVED: { label: '已通過', cls: 'approved' },
  REJECTED: { label: '未通過', cls: 'rejected' },
}

async function load() {
  error.value = ''
  try {
    const { data } = await listMyApplications()
    items.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '載入失敗'
  }
}

function fmt(d) {
  return new Date(d).toLocaleString('zh-TW', { dateStyle: 'medium', timeStyle: 'short' })
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (auth.role !== 'STUDENT') {
    error.value = '此頁僅供學生查看'
    return
  }
  load()
})
</script>

<template>
  <main class="page">
    <header class="bar">
      <RouterLink to="/">← 首頁</RouterLink>
      <h1>我的申請進度</h1>
      <RouterLink to="/sas/apply" class="right">＋ 申請新獎學金</RouterLink>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="auth.role === 'STUDENT' && !items.length" class="empty">你還沒有任何申請。</p>

    <table v-if="items.length">
      <thead>
        <tr><th>獎學金</th><th>狀態</th><th>申請時間</th><th>自述</th></tr>
      </thead>
      <tbody>
        <tr v-for="a in items" :key="a.application_id">
          <td>{{ a.scholarship_name }}</td>
          <td><span class="badge" :class="STATUS[a.status]?.cls">{{ STATUS[a.status]?.label || a.status }}</span></td>
          <td>{{ fmt(a.created_at) }}</td>
          <td class="stmt">{{ a.statement || '—' }}</td>
        </tr>
      </tbody>
    </table>
  </main>
</template>

<style scoped>
.page { max-width: 820px; margin: 4vh auto; padding: 0 16px; font-family: system-ui, sans-serif; }
.bar { display: flex; align-items: center; gap: 16px; }
.bar a { color: #2b6cb0; text-decoration: none; }
.right { margin-left: auto; }
h1 { font-size: 22px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { border-bottom: 1px solid #eee; padding: 10px; text-align: left; vertical-align: top; }
th { background: #f7f9fb; }
.stmt { color: #555; max-width: 280px; }
.badge { font-size: 12px; padding: 3px 10px; border-radius: 999px; }
.review { background: #fff4e5; color: #b35900; }
.supplement { background: #fdeaea; color: #b3261e; }
.approved { background: #e6f4ea; color: #1a7f37; }
.rejected { background: #f1f1f1; color: #777; }
.error { color: #c0392b; }
.empty { color: #888; }
</style>
