<script setup>
// AAS 稽核紀錄（系統管理員）：檢視系統重要操作（帳號/獎學金/審查）。
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listAuditLogs } from '@/api/aas'

const router = useRouter()
const auth = useAuthStore()
const logs = ref([])
const loading = ref(false)
const error = ref('')
const isAdmin = computed(() => auth.role === 'ADMIN')

const ACTION_LABEL = {
  CREATE_USER: '新增帳號', UPDATE_USER: '修改帳號', DELETE_USER: '刪除帳號',
  CREATE_SCHOLARSHIP: '新增獎學金', UPDATE_SCHOLARSHIP: '修改獎學金', DELETE_SCHOLARSHIP: '刪除獎學金',
}

function fmt(t) {
  if (!t) return '—'
  return new Date(t).toLocaleString('zh-TW')
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listAuditLogs()
    logs.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (isAdmin.value) load()
})
</script>

<template>
  <main class="page">
    <h1>稽核紀錄</h1>
    <p v-if="!isAdmin" class="warn">此功能僅限系統管理員。</p>

    <template v-else>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading">載入中…</p>
      <p v-else-if="logs.length === 0" class="muted">目前沒有任何紀錄。</p>
      <table v-else class="tbl">
        <thead>
          <tr><th>時間</th><th>操作者</th><th>動作</th><th>對象</th><th>說明</th></tr>
        </thead>
        <tbody>
          <tr v-for="l in logs" :key="l.log_id">
            <td>{{ fmt(l.created_at) }}</td>
            <td>{{ l.actor_name || ('#' + (l.actor_id ?? '?')) }}</td>
            <td>{{ ACTION_LABEL[l.action] || l.action }}</td>
            <td>{{ l.target_type ? `${l.target_type} #${l.target_id}` : '—' }}</td>
            <td>{{ l.detail || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </main>
</template>

<style scoped>
.page { max-width: 1000px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
.tbl { width: 100%; border-collapse: collapse; font-size: 14px; background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; overflow: hidden; }
.tbl th, .tbl td { text-align: left; padding: 10px; border-bottom: 1px solid #edf2f7; }
.tbl th { background: #f7fafc; }
.muted { color: #a0aec0; }
.error { color: #c53030; }
.warn { color: #c05621; }
</style>
