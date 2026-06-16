<script setup>
// RAS 審查申請案（僅審查人員 REVIEWER）。
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listReviewApplications, decide } from '@/api/ras'

const router = useRouter()
const auth = useAuthStore()

const STATUS_LABEL = { UNDER_REVIEW: '審核中', NEED_SUPPLEMENT: '需補件', APPROVED: '已通過', REJECTED: '未通過' }
const RESULT_LABEL = { APPROVED: '通過', REJECTED: '不通過', NEED_SUPPLEMENT: '需補件' }

const apps = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const decision = reactive({})  // application_id -> { result, comment }

const isReviewer = computed(() => auth.role === 'REVIEWER')
function fmtDate(t) { return t ? new Date(t).toLocaleString('zh-TW') : '' }

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await listReviewApplications()
    apps.value = data
    for (const a of data) {
      if (!decision[a.application_id]) decision[a.application_id] = { result: 'APPROVED', comment: '' }
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function submit(a) {
  error.value = ''; notice.value = ''
  const d = decision[a.application_id]
  try {
    await decide(a.application_id, { result: d.result, comment: d.comment || null })
    notice.value = `已完成「${a.scholarship_name || a.application_id}」的審查`
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '審查失敗'
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (isReviewer.value) load()
})
</script>

<template>
  <main class="page">
    <h1>審查申請案</h1>
    <p v-if="!isReviewer" class="warn">此功能僅限審查人員（REVIEWER）。</p>

    <template v-else>
      <p v-if="notice" class="notice">{{ notice }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading">載入中…</p>
      <p v-else-if="apps.length === 0" class="muted">目前沒有待審查的申請。</p>

      <div v-else class="list">
        <article v-for="a in apps" :key="a.application_id" class="app">
          <div class="head">
            <h3>{{ a.student_name }}<span class="gpa">GPA {{ a.gpa ?? '—' }}</span></h3>
            <span class="status">目前：{{ STATUS_LABEL[a.status] || a.status }}</span>
          </div>
          <p class="sch">申請獎學金：{{ a.scholarship_name || '—' }}（申請時間 {{ fmtDate(a.created_at) }}）</p>

          <div class="fields">
            <div v-if="a.statement"><span class="k">申請理由</span><p>{{ a.statement }}</p></div>
            <div class="inline">
              <span><span class="k">電話</span>{{ a.contact_phone || '—' }}</span>
              <span><span class="k">地址</span>{{ a.address || '—' }}</span>
            </div>
            <div v-if="a.household_status"><span class="k">家庭狀況</span><p>{{ a.household_status }}</p></div>
            <div v-if="a.academic_note"><span class="k">成績/排名</span><p>{{ a.academic_note }}</p></div>
          </div>

          <div class="recs" v-if="a.recommendations && a.recommendations.length">
            <strong>推薦信</strong>
            <div v-for="(rc, i) in a.recommendations" :key="i" class="rec">
              <span class="who">{{ rc.teacher_name }} 老師</span>
              <p>{{ rc.content || '（無內容）' }}</p>
            </div>
          </div>

          <div class="prev" v-if="a.review_result">
            最近審查：{{ a.reviewer_name || '—' }} 評為「{{ RESULT_LABEL[a.review_result] || a.review_result }}」
            於 {{ fmtDate(a.reviewed_at) }}<span v-if="a.review_comment">，意見：{{ a.review_comment }}</span>
          </div>

          <div class="decide">
            <select v-model="decision[a.application_id].result">
              <option value="APPROVED">通過</option>
              <option value="REJECTED">不通過</option>
              <option value="NEED_SUPPLEMENT">需補件</option>
            </select>
            <input v-model="decision[a.application_id].comment" placeholder="審查意見（選填）" />
            <button class="primary" @click="submit(a)">送出審查</button>
          </div>
        </article>
      </div>
    </template>
  </main>
</template>

<style scoped>
.page { max-width: 860px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
h3 { margin: 0; font-size: 17px; display: flex; align-items: center; gap: 10px; }
.gpa { font-size: 13px; color: #2b6cb0; background: #ebf8ff; padding: 2px 8px; border-radius: 999px; }
.list { display: flex; flex-direction: column; gap: 16px; }
.app { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; }
.head { display: flex; align-items: center; justify-content: space-between; }
.status { font-size: 13px; color: #718096; }
.sch { color: #4a5568; font-size: 14px; }
.fields { background: #f7fafc; border-radius: 10px; padding: 12px; margin: 10px 0; font-size: 14px; }
.fields p { margin: 2px 0 8px; }
.fields .inline { display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 8px; }
.k { display: inline-block; color: #718096; font-size: 12px; margin-right: 6px; }
.recs { border-top: 1px dashed #e2e8f0; padding-top: 10px; margin-top: 6px; }
.rec { background: #fffaf0; border: 1px solid #feebc8; border-radius: 10px; padding: 10px; margin: 8px 0; font-size: 14px; }
.rec .who { color: #975a16; font-weight: 600; }
.prev { background: #ebf8ff; color: #2c5282; font-size: 13px; border-radius: 8px; padding: 8px 12px; margin: 8px 0; }
.decide { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; align-items: center; }
select, input { padding: 8px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 14px; }
.decide input { flex: 1; min-width: 180px; }
.primary { background: #2b6cb0; color: #fff; border: none; padding: 9px 16px; border-radius: 8px; cursor: pointer; }
.muted { color: #a0aec0; }
.notice { color: #22732f; }
.error { color: #c53030; }
.warn { color: #c05621; }
</style>
