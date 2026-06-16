<script setup>
// TRS 推薦邀請（老師）：撰寫 / 存草稿 / 送出推薦信。
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listTeacherRecommendations, saveRecommendation } from '@/api/trs'

const router = useRouter()
const auth = useAuthStore()

const REC_LABEL = { REQUESTED: '已邀請（待撰寫）', DRAFT: '草稿', SUBMITTED: '已送出' }

const items = ref([])
const drafts = reactive({})  // rec_id -> content
const loading = ref(false)
const error = ref('')
const notice = ref('')

const isTeacher = computed(() => auth.role === 'TEACHER')
function fmtDate(t) { return t ? new Date(t).toLocaleString('zh-TW') : '' }

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await listTeacherRecommendations()
    items.value = data
    for (const r of data) drafts[r.rec_id] = r.content || ''
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function save(rec, submit) {
  error.value = ''; notice.value = ''
  if (submit && !(drafts[rec.rec_id] || '').trim()) { error.value = '送出前請先填寫推薦信內容'; return }
  try {
    await saveRecommendation(rec.rec_id, { content: drafts[rec.rec_id], submit })
    notice.value = submit ? '已送出推薦信' : '已儲存草稿'
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '儲存失敗'
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (isTeacher.value) load()
})
</script>

<template>
  <main class="page">
    <h1>推薦邀請</h1>
    <p v-if="!isTeacher" class="warn">此功能僅限老師帳號。</p>

    <template v-else>
      <p v-if="notice" class="notice">{{ notice }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading">載入中…</p>
      <p v-else-if="items.length === 0" class="muted">目前沒有推薦邀請。</p>

      <div v-else class="list">
        <article v-for="r in items" :key="r.rec_id" class="rec">
          <div class="head">
            <h3>{{ r.student_name }}</h3>
            <span :class="['pill', r.status === 'SUBMITTED' ? 'ok' : 'pend']">{{ REC_LABEL[r.status] || r.status }}</span>
          </div>
          <p class="sch">獎學金：{{ r.scholarship_name || '—' }}　更新：{{ fmtDate(r.updated_at) }}</p>
          <textarea v-model="drafts[r.rec_id]" rows="5" placeholder="請撰寫推薦信內容…" :disabled="r.status === 'SUBMITTED'"></textarea>
          <div class="actions" v-if="r.status !== 'SUBMITTED'">
            <button class="ghost" @click="save(r, false)">存草稿</button>
            <button class="primary" @click="save(r, true)">送出</button>
          </div>
          <p v-else class="done">此推薦信已送出，不可再修改。</p>
        </article>
      </div>
    </template>
  </main>
</template>

<style scoped>
.page { max-width: 760px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
h3 { margin: 0; font-size: 17px; }
.list { display: flex; flex-direction: column; gap: 16px; }
.rec { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; }
.head { display: flex; align-items: center; justify-content: space-between; }
.sch { color: #718096; font-size: 13px; }
textarea { width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 14px; font-family: inherit; margin: 8px 0; }
textarea:disabled { background: #f7fafc; color: #4a5568; }
.actions { display: flex; gap: 8px; }
.primary { background: #2b6cb0; color: #fff; border: none; padding: 9px 16px; border-radius: 8px; cursor: pointer; }
.ghost { background: #edf2f7; border: none; padding: 9px 16px; border-radius: 8px; cursor: pointer; }
.done { color: #22732f; font-size: 13px; }
.pill { padding: 3px 10px; border-radius: 999px; font-size: 12px; }
.pill.ok { background: #c6f6d5; color: #22543d; }
.pill.pend { background: #feebc8; color: #7b341e; }
.muted { color: #a0aec0; }
.notice { color: #22732f; }
.error { color: #c53030; }
.warn { color: #c05621; }
</style>
