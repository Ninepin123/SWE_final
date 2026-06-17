<script setup>
// SAS 瀏覽 / 申請獎學金（學生）。已申請過的獎學金，申請鈕會停用。
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listScholarships } from '@/api/sms'
import { apply, listMyApplications } from '@/api/sas'

const router = useRouter()
const auth = useAuthStore()

const CAT_LABEL = { SCHOOL: '校內', GOVERNMENT: '政府', PRIVATE: '民間', LOW_INCOME: '清寒', MERIT: '績優', OTHER: '其他' }

const items = ref([])
const appliedIds = ref(new Set())
const loading = ref(false)
const error = ref('')
const notice = ref('')

const selectedId = ref(null)
const form = reactive({ statement: '', contact_phone: '', address: '', household_status: '', academic_note: '' })

const isStudent = computed(() => auth.role === 'STUDENT')
function fmtDate(t) { return t ? new Date(t).toLocaleString('zh-TW') : '無期限' }
function hasApplied(id) { return appliedIds.value.has(id) }

async function load() {
  loading.value = true; error.value = ''
  try {
    const [sch, mine] = await Promise.all([
      listScholarships({ only_open: true }),
      listMyApplications(),
    ])
    items.value = sch.data
    appliedIds.value = new Set(mine.data.map((a) => a.scholarship_id))
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

function openForm(s) {
  selectedId.value = s.scholarship_id
  Object.assign(form, { statement: '', contact_phone: '', address: '', household_status: '', academic_note: '' })
  notice.value = ''; error.value = ''
}
function closeForm() { selectedId.value = null }

async function submit(s) {
  error.value = ''; notice.value = ''
  if (!form.statement.trim()) { error.value = '請填寫申請理由'; return }
  try {
    await apply({
      scholarship_id: s.scholarship_id,
      statement: form.statement,
      contact_phone: form.contact_phone || null,
      address: form.address || null,
      household_status: form.household_status || null,
      academic_note: form.academic_note || null,
    })
    appliedIds.value = new Set([...appliedIds.value, s.scholarship_id])
    selectedId.value = null
    notice.value = `已送出「${s.name}」的申請`
  } catch (e) {
    error.value = e?.response?.data?.detail || '申請失敗'
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (isStudent.value) load()
})
</script>

<template>
  <main class="page">
    <h1>瀏覽 / 申請獎學金</h1>
    <p v-if="!isStudent" class="warn">此功能僅限學生帳號。</p>

    <template v-else>
      <section class="me">
        <strong>申請人資料</strong>
        <span>姓名：{{ auth.user?.name }}</span>
        <span>學號：{{ auth.user?.account }}</span>
        <span>系所：{{ auth.user?.department || '—' }}</span>
        <span>GPA：{{ auth.user?.gpa ?? '—' }}</span>
        <RouterLink class="mini" to="/sas/profile">修改個人資料</RouterLink>
      </section>

      <p v-if="notice" class="notice">{{ notice }}</p>
      <p v-if="error" class="error">{{ error }}</p>

      <p v-if="loading">載入中…</p>
      <p v-else-if="items.length === 0" class="muted">目前沒有開放中的獎學金。</p>

      <div v-else class="list">
        <article v-for="s in items" :key="s.scholarship_id" class="sch">
          <h3>{{ s.name }}</h3>
          <p class="meta">
            {{ s.unit_name || '—' }}｜{{ CAT_LABEL[s.category] || s.category }}｜金額 {{ s.amount }}｜名額 {{ s.quota }}
            <span v-if="s.min_gpa"> ｜最低GPA {{ s.min_gpa }}</span>
          </p>
          <p class="desc" v-if="s.description">{{ s.description }}</p>
          <p class="deadline">截止：{{ fmtDate(s.deadline) }}</p>

          <button v-if="hasApplied(s.scholarship_id)" class="applied" disabled>已申請</button>
          <button v-else-if="selectedId !== s.scholarship_id" class="primary" @click="openForm(s)">填寫申請表</button>

          <div v-if="selectedId === s.scholarship_id" class="apply-form">
            <label>申請理由 / 自述 *<textarea v-model="form.statement" rows="3" placeholder="請說明申請動機與資格"></textarea></label>
            <div class="two">
              <label>聯絡電話<input v-model="form.contact_phone" /></label>
              <label>通訊地址<input v-model="form.address" /></label>
            </div>
            <label>家庭狀況<textarea v-model="form.household_status" rows="2"></textarea></label>
            <label>在學成績 / 排名說明<textarea v-model="form.academic_note" rows="2"></textarea></label>
            <div class="actions">
              <button class="primary" @click="submit(s)">送出申請</button>
              <button class="ghost" @click="closeForm">取消</button>
            </div>
          </div>
        </article>
      </div>
    </template>
  </main>
</template>

<style scoped>
h3 { margin: 0 0 4px; font-size: 17px; }
.me {
  background: var(--primary-tint);
  border: 1px solid var(--primary-soft);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  font-size: 14px;
  color: var(--primary-strong);
  margin-bottom: 16px;
}
.mini { font-size: 13px; }
.list { display: flex; flex-direction: column; gap: 14px; }
.sch { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg); padding: 18px; box-shadow: var(--shadow-xs); }
.meta { color: var(--text-secondary); font-size: 14px; }
.desc { color: var(--text-secondary); line-height: 1.65; }
.deadline { color: var(--muted); font-size: 13px; }
.primary { background: var(--primary); color: #fff; border: none; padding: 9px 16px; border-radius: var(--radius-sm); cursor: pointer; font-weight: 600; }
.primary:hover { background: var(--primary-strong); }
.ghost { background: var(--surface-muted); color: var(--text-secondary); border: none; padding: 9px 16px; border-radius: var(--radius-sm); cursor: pointer; font-weight: 600; }
.ghost:hover { background: var(--surface-sunken); }
.applied { background: var(--surface-sunken); color: var(--muted); border: none; padding: 9px 16px; border-radius: var(--radius-sm); cursor: not-allowed; font-weight: 600; }
.apply-form { margin-top: 14px; border-top: 1px dashed var(--line-strong); padding-top: 14px; display: flex; flex-direction: column; gap: 10px; }
.apply-form label { display: flex; flex-direction: column; font-size: 13px; color: var(--text-secondary); gap: 4px; font-weight: 600; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.actions { display: flex; gap: 8px; }
.muted { color: var(--muted); }
.notice { color: var(--success); font-weight: 600; }
.error { color: var(--danger); font-weight: 600; }
.warn { color: var(--warning); font-weight: 600; }
</style>
