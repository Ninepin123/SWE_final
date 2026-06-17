<script setup>
// NCS 公告：所有人可看；系統管理員可發布。
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listAnnouncements, createAnnouncement } from '@/api/ncs'

const router = useRouter()
const auth = useAuthStore()
const items = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const form = reactive({ title: '', body: '' })

const isAdmin = computed(() => auth.role === 'ADMIN')
function fmtDate(t) { return t ? new Date(t).toLocaleString('zh-TW') : '' }

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await listAnnouncements()
    items.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function publish() {
  error.value = ''; notice.value = ''
  if (!form.title.trim()) { error.value = '請填寫公告標題'; return }
  try {
    await createAnnouncement({ title: form.title, body: form.body || null })
    notice.value = '已發布公告'
    form.title = ''; form.body = ''
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '發布失敗'
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  load()
})
</script>

<template>
  <main class="page">
    <h1>公告</h1>

    <section v-if="isAdmin" class="card">
      <h2>發布公告</h2>
      <label>標題<input v-model="form.title" /></label>
      <label>內容<textarea v-model="form.body" rows="3"></textarea></label>
      <button class="primary" @click="publish">發布</button>
      <span v-if="notice" class="notice">{{ notice }}</span>
    </section>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading">載入中…</p>
    <p v-else-if="items.length === 0" class="muted">目前沒有公告。</p>

    <div v-else class="list">
      <article v-for="a in items" :key="a.announcement_id" class="ann">
        <div class="row"><h3>{{ a.title }}</h3><span class="time">{{ fmtDate(a.created_at) }}</span></div>
        <p v-if="a.body" class="body">{{ a.body }}</p>
      </article>
    </div>
  </main>
</template>

<style scoped>
.page { max-width: 720px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
h2 { font-size: 16px; margin: 0 0 12px; }
h3 { margin: 0; font-size: 16px; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; margin-bottom: 18px; }
.card label { display: flex; flex-direction: column; font-size: 13px; color: #4a5568; gap: 4px; margin-bottom: 10px; }
input, textarea { padding: 8px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 14px; font-family: inherit; }
.primary { background: #2b6cb0; color: #fff; border: none; padding: 9px 16px; border-radius: 8px; cursor: pointer; margin-right: 10px; }
.list { display: flex; flex-direction: column; gap: 12px; }
.ann { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
.row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.time { color: #a0aec0; font-size: 12px; white-space: nowrap; }
.body { color: #4a5568; font-size: 14px; margin: 6px 0 0; white-space: pre-wrap; }
.muted { color: #a0aec0; }
.notice { color: #22732f; }
.error { color: #c53030; }
</style>
