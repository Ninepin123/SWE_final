<script setup>
// SAS 我的申請進度（學生）：看狀態、邀請老師推薦、看推薦狀態。
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listMyApplications } from '@/api/sas'
import { listTeachers } from '@/api/aas'
import { listMyRecommendations, requestRecommendation } from '@/api/trs'

const router = useRouter()
const auth = useAuthStore()

const STATUS_LABEL = { UNDER_REVIEW: '審核中', NEED_SUPPLEMENT: '需補件', APPROVED: '已通過', REJECTED: '未通過' }
const STATUS_CLASS = { UNDER_REVIEW: 'review', NEED_SUPPLEMENT: 'supp', APPROVED: 'ok', REJECTED: 'no' }
const REC_LABEL = { REQUESTED: '已邀請', DRAFT: '撰寫中', SUBMITTED: '已送出' }

const apps = ref([])
const recs = ref([])
const teachers = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')
const pickTeacher = reactive({})  // application_id -> teacher_id

const isStudent = computed(() => auth.role === 'STUDENT')
function fmtDate(t) { return t ? new Date(t).toLocaleString('zh-TW') : '' }
function recsFor(appId) { return recs.value.filter((r) => r.application_id === appId) }

async function load() {
  loading.value = true; error.value = ''
  try {
    const [a, r, t] = await Promise.all([listMyApplications(), listMyRecommendations(), listTeachers()])
    apps.value = a.data
    recs.value = r.data
    teachers.value = t.data
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function invite(appId) {
  error.value = ''; notice.value = ''
  const teacherId = pickTeacher[appId]
  if (!teacherId) { error.value = '請先選擇老師'; return }
  try {
    await requestRecommendation({ application_id: appId, teacher_id: Number(teacherId) })
    notice.value = '已送出推薦邀請'
    pickTeacher[appId] = ''
    const { data } = await listMyRecommendations()
    recs.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || '邀請失敗'
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (isStudent.value) load()
})
</script>

<template>
  <main class="page">
    <h1>我的申請進度</h1>
    <p v-if="!isStudent" class="warn">此功能僅限學生帳號。</p>

    <template v-else>
      <p v-if="notice" class="notice">{{ notice }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading">載入中…</p>
      <p v-else-if="apps.length === 0" class="muted">你還沒有任何申請。<RouterLink to="/sas/apply">去申請</RouterLink></p>

      <div v-else class="list">
        <article v-for="a in apps" :key="a.application_id" class="app">
          <div class="head">
            <h3>{{ a.scholarship_name || ('申請 #' + a.application_id) }}</h3>
            <span :class="['pill', STATUS_CLASS[a.status]]">{{ STATUS_LABEL[a.status] || a.status }}</span>
          </div>
          <p class="when">申請時間：{{ fmtDate(a.created_at) }}</p>
          <p class="statement" v-if="a.statement"><span class="lbl">申請理由：</span>{{ a.statement }}</p>

          <div class="rec-box">
            <strong>推薦信</strong>
            <ul v-if="recsFor(a.application_id).length" class="recs">
              <li v-for="rc in recsFor(a.application_id)" :key="rc.rec_id">
                {{ rc.teacher_name }} —
                <span :class="['rpill', rc.status === 'SUBMITTED' ? 'ok' : 'pend']">{{ REC_LABEL[rc.status] || rc.status }}</span>
              </li>
            </ul>
            <p v-else class="muted small">尚未邀請任何老師</p>

            <div class="invite">
              <select v-model="pickTeacher[a.application_id]">
                <option value="">選擇老師…</option>
                <option v-for="t in teachers" :key="t.user_id" :value="t.user_id">
                  {{ t.name }}<span v-if="t.department"> （{{ t.department }}）</span>
                </option>
              </select>
              <button class="primary" @click="invite(a.application_id)">邀請推薦</button>
            </div>
          </div>
        </article>
      </div>
    </template>
  </main>
</template>

<style scoped>
.page { max-width: 820px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
h3 { margin: 0; font-size: 17px; }
.list { display: flex; flex-direction: column; gap: 14px; }
.app { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg); padding: 18px; box-shadow: var(--shadow-xs); }
.head { display: flex; align-items: center; justify-content: space-between; }
.when { color: var(--muted); font-size: 13px; font-family: var(--font-mono); }
.statement { color: var(--text-secondary); font-size: 14px; }
.lbl { color: var(--muted); }
.rec-box { margin-top: 12px; border-top: 1px dashed var(--line); padding-top: 12px; }
.recs { margin: 8px 0; padding-left: 18px; font-size: 14px; }
.invite { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
select { flex: 1; min-width: 180px; }
.primary { background: var(--primary); color: #fff; border: none; padding: 8px 14px; border-radius: var(--radius-sm); cursor: pointer; font-weight: 600; }
.primary:hover { background: var(--primary-strong); }
.pill { padding: 3px 10px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 700; }
.pill.review { background: var(--info-soft); color: var(--info); }
.pill.supp { background: var(--warning-soft); color: var(--warning); }
.pill.ok { background: var(--success-soft); color: var(--success); }
.pill.no { background: var(--danger-soft); color: var(--danger); }
.rpill { padding: 1px 8px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 700; }
.rpill.ok { background: var(--success-soft); color: var(--success); }
.rpill.pend { background: var(--surface-sunken); color: var(--muted); }
.muted { color: var(--muted); }
.small { font-size: 13px; }
.notice { color: var(--success); }
.error { color: var(--danger); }
.warn { color: var(--warning); }
</style>
