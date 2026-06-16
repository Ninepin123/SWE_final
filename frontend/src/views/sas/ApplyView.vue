<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listScholarships } from '@/api/sms'
import { apply as applyApi } from '@/api/sas'

const router = useRouter()
const auth = useAuthStore()

const items = ref([])
const error = ref('')
const statements = reactive({})   // scholarship_id -> 自述
const applied = reactive({})      // scholarship_id -> true
const sending = ref(null)

async function load() {
  error.value = ''
  try {
    const { data } = await listScholarships({ only_open: true })
    items.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '載入失敗'
  }
}

async function submit(s) {
  error.value = ''
  sending.value = s.scholarship_id
  try {
    await applyApi({ scholarship_id: s.scholarship_id, statement: statements[s.scholarship_id] || null })
    applied[s.scholarship_id] = true
  } catch (e) {
    error.value = e.response?.data?.detail || '申請失敗'
  } finally {
    sending.value = null
  }
}

function fmtDeadline(d) {
  if (!d) return '不限'
  return new Date(d).toLocaleString('zh-TW', { dateStyle: 'medium', timeStyle: 'short' })
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (auth.role !== 'STUDENT') {
    error.value = '此頁僅供學生申請'
    return
  }
  load()
})
</script>

<template>
  <main class="page">
    <header class="bar">
      <RouterLink to="/">← 首頁</RouterLink>
      <h1>申請獎學金</h1>
      <RouterLink to="/sas/applications" class="right">我的申請進度 →</RouterLink>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="auth.role === 'STUDENT' && !items.length" class="empty">目前沒有可申請的獎學金。</p>

    <div class="cards" v-if="auth.role === 'STUDENT'">
      <article v-for="s in items" :key="s.scholarship_id" class="card">
        <h3>{{ s.name }}</h3>
        <p class="meta">{{ s.unit_name || ('單位#' + s.unit_id) }} · {{ s.year }} 年度</p>
        <p class="amount">NT$ {{ s.amount.toLocaleString() }}　名額 {{ s.quota }}</p>
        <p class="cond">最低 GPA：{{ s.min_gpa ?? '不限' }}　截止：{{ fmtDeadline(s.deadline) }}</p>
        <p v-if="s.description" class="desc">{{ s.description }}</p>

        <template v-if="applied[s.scholarship_id]">
          <p class="ok">✅ 已送出申請，請至「我的申請進度」查看。</p>
        </template>
        <template v-else>
          <textarea v-model="statements[s.scholarship_id]" rows="2" placeholder="申請理由 / 自述（選填）" />
          <button class="primary" :disabled="sending === s.scholarship_id" @click="submit(s)">
            {{ sending === s.scholarship_id ? '送出中…' : '申請' }}
          </button>
        </template>
      </article>
    </div>
  </main>
</template>

<style scoped>
.page { max-width: 900px; margin: 4vh auto; padding: 0 16px; font-family: system-ui, sans-serif; }
.bar { display: flex; align-items: center; gap: 16px; }
.bar a { color: #2b6cb0; text-decoration: none; }
.right { margin-left: auto; }
h1 { font-size: 22px; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.card { border: 1px solid #e3e3e3; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.04); }
h3 { margin: 0 0 6px; font-size: 16px; }
.meta { color: #666; font-size: 13px; margin: 2px 0; }
.amount { font-weight: 700; margin: 4px 0; }
.cond { font-size: 13px; color: #555; margin: 2px 0; }
.desc { font-size: 13px; color: #444; margin: 8px 0; }
textarea { width: 100%; box-sizing: border-box; padding: 8px 10px; border: 1px solid #ccc; border-radius: 8px; font-size: 14px; margin: 8px 0; }
.primary { padding: 9px 18px; border: none; border-radius: 8px; background: #2b6cb0; color: #fff; cursor: pointer; }
.primary:disabled { opacity: .6; }
.error { color: #c0392b; }
.ok { color: #1a7f37; font-size: 14px; }
.empty { color: #888; }
</style>
