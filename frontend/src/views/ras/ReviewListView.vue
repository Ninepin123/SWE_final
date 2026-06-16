<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listReviewApplications, decide as decideApi } from '@/api/ras'

const router = useRouter()
const auth = useAuthStore()

const items = ref([])
const error = ref('')
const comments = reactive({})  // application_id -> 審查意見
const busy = ref(null)

const STATUS = {
  UNDER_REVIEW: '審核中', NEED_SUPPLEMENT: '需補件', APPROVED: '已通過', REJECTED: '未通過',
}

async function load() {
  error.value = ''
  try {
    const { data } = await listReviewApplications()
    items.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '載入失敗'
  }
}

async function decide(a, result) {
  error.value = ''
  busy.value = a.application_id
  try {
    await decideApi(a.application_id, { result, comment: comments[a.application_id] || null })
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || '審查失敗'
  } finally {
    busy.value = null
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (auth.role !== 'REVIEWER' && auth.role !== 'ADMIN') {
    error.value = '此頁僅供審查人員 / 管理員'
    return
  }
  load()
})
</script>

<template>
  <main class="page">
    <header class="bar">
      <RouterLink to="/">← 首頁</RouterLink>
      <h1>審查申請案</h1>
    </header>
    <p class="hint">依申請人 GPA 由高到低排序。</p>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="(auth.role === 'REVIEWER' || auth.role === 'ADMIN') && !items.length" class="empty">目前沒有待審查的申請案。</p>

    <table v-if="items.length">
      <thead>
        <tr><th>申請人</th><th>GPA</th><th>獎學金</th><th>目前狀態</th><th>自述</th><th>審查</th></tr>
      </thead>
      <tbody>
        <tr v-for="a in items" :key="a.application_id">
          <td>{{ a.student_name }}</td>
          <td>{{ a.gpa ?? '—' }}</td>
          <td>{{ a.scholarship_name }}</td>
          <td>{{ STATUS[a.status] || a.status }}</td>
          <td class="stmt">{{ a.statement || '—' }}</td>
          <td class="actions">
            <input v-model="comments[a.application_id]" placeholder="審查意見（選填）" />
            <div class="btns">
              <button class="ok" :disabled="busy === a.application_id" @click="decide(a, 'APPROVED')">通過</button>
              <button class="no" :disabled="busy === a.application_id" @click="decide(a, 'REJECTED')">不通過</button>
              <button class="sup" :disabled="busy === a.application_id" @click="decide(a, 'NEED_SUPPLEMENT')">補件</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </main>
</template>

<style scoped>
.page { max-width: 1000px; margin: 4vh auto; padding: 0 16px; font-family: system-ui, sans-serif; }
.bar { display: flex; align-items: center; gap: 16px; }
.bar a { color: #2b6cb0; text-decoration: none; }
h1 { font-size: 22px; }
.hint { color: #888; font-size: 13px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { border-bottom: 1px solid #eee; padding: 10px; text-align: left; vertical-align: top; }
th { background: #f7f9fb; }
.stmt { color: #555; max-width: 220px; }
.actions input { width: 160px; padding: 6px 8px; border: 1px solid #ccc; border-radius: 8px; font-size: 13px; }
.btns { display: flex; gap: 6px; margin-top: 6px; }
.btns button { padding: 6px 10px; border: none; border-radius: 8px; color: #fff; cursor: pointer; font-size: 13px; }
.btns button:disabled { opacity: .6; }
.ok { background: #1a7f37; }
.no { background: #b3261e; }
.sup { background: #b35900; }
.error { color: #c0392b; }
.empty { color: #888; }
</style>
