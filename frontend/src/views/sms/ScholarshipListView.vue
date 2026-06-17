<script setup>
// SMS 獎學金列表 / 管理。所有登入者可瀏覽；獎助單位與管理員可新增/修改/刪除。
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listScholarships, createScholarship, updateScholarship, deleteScholarship } from '@/api/sms'

const router = useRouter()
const auth = useAuthStore()

const CATEGORIES = ['SCHOOL', 'GOVERNMENT', 'PRIVATE', 'LOW_INCOME', 'MERIT', 'OTHER']
const CAT_LABEL = { SCHOOL: '校內', GOVERNMENT: '政府', PRIVATE: '民間', LOW_INCOME: '清寒', MERIT: '績優', OTHER: '其他' }

const items = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

const canManage = computed(() => auth.role === 'SPONSOR' || auth.role === 'ADMIN')

const createForm = reactive({
  name: '', year: new Date().getFullYear(), amount: 0, quota: 1, min_gpa: '', department_limit: '', category: 'OTHER', description: '', deadline: '',
})

const editingId = ref(null)
const editForm = reactive({
  name: '', year: 0, amount: 0, quota: 1, min_gpa: '', department_limit: '', category: 'OTHER', description: '', deadline: '', status: 'OPEN',
})

function numOrNull(v) { return v === '' || v === null ? null : Number(v) }
function fmtDate(t) { return t ? new Date(t).toLocaleString('zh-TW') : '無期限' }

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await listScholarships()
    items.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  error.value = ''; notice.value = ''
  try {
    await createScholarship({
      name: createForm.name,
      year: Number(createForm.year),
      amount: Number(createForm.amount),
      quota: Number(createForm.quota),
      min_gpa: numOrNull(createForm.min_gpa),
      department_limit: createForm.department_limit || null,
      category: createForm.category,
      description: createForm.description || null,
      deadline: createForm.deadline || null,
    })
    notice.value = '已新增獎學金'
    Object.assign(createForm, { name: '', year: new Date().getFullYear(), amount: 0, quota: 1, min_gpa: '', department_limit: '', category: 'OTHER', description: '', deadline: '' })
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '新增失敗'
  }
}

function startEdit(s) {
  editingId.value = s.scholarship_id
  Object.assign(editForm, {
    name: s.name, year: s.year, amount: s.amount, quota: s.quota,
    min_gpa: s.min_gpa ?? '', department_limit: s.department_limit || '',
    category: s.category, description: s.description || '',
    deadline: s.deadline ? String(s.deadline).slice(0, 16) : '', status: s.status,
  })
}
function cancelEdit() { editingId.value = null }

async function submitEdit(id) {
  error.value = ''; notice.value = ''
  try {
    await updateScholarship(id, {
      name: editForm.name,
      year: Number(editForm.year),
      amount: Number(editForm.amount),
      quota: Number(editForm.quota),
      min_gpa: numOrNull(editForm.min_gpa),
      department_limit: editForm.department_limit || null,
      category: editForm.category,
      description: editForm.description || null,
      deadline: editForm.deadline || null,
      status: editForm.status,
    })
    notice.value = '已更新獎學金'
    editingId.value = null
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '更新失敗'
  }
}

async function remove(s) {
  if (!confirm(`確定刪除獎學金「${s.name}」？`)) return
  error.value = ''; notice.value = ''
  try {
    await deleteScholarship(s.scholarship_id)
    notice.value = '已刪除獎學金'
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '刪除失敗'
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  load()
})
</script>

<template>
  <main class="page">
    <h1>獎學金{{ canManage ? '管理' : '列表' }}</h1>

    <section v-if="canManage" class="card">
      <h2>新增獎學金</h2>
      <div class="form-grid">
        <label>名稱<input v-model="createForm.name" /></label>
        <label>年度<input v-model="createForm.year" type="number" /></label>
        <label>金額<input v-model="createForm.amount" type="number" /></label>
        <label>名額<input v-model="createForm.quota" type="number" /></label>
        <label>最低GPA<input v-model="createForm.min_gpa" type="number" step="0.01" /></label>
        <label>限定系所<input v-model="createForm.department_limit" /></label>
        <label>分類
          <select v-model="createForm.category">
            <option v-for="c in CATEGORIES" :key="c" :value="c">{{ CAT_LABEL[c] }}</option>
          </select>
        </label>
        <label>截止時間<input v-model="createForm.deadline" type="datetime-local" /></label>
        <label class="full">說明<textarea v-model="createForm.description" rows="2"></textarea></label>
      </div>
      <button class="primary" @click="submitCreate">新增</button>
    </section>

    <p v-if="notice" class="notice">{{ notice }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <p v-if="loading">載入中…</p>
    <p v-else-if="items.length === 0" class="muted">目前沒有獎學金。</p>

    <div v-else class="list">
      <article v-for="s in items" :key="s.scholarship_id" class="sch">
        <div class="sch-head">
          <h3>{{ s.name }}</h3>
          <span :class="['pill', s.status === 'OPEN' ? 'open' : 'closed']">{{ s.status === 'OPEN' ? '開放中' : '已關閉' }}</span>
        </div>
        <p class="meta">
          {{ s.unit_name || '—' }}｜{{ s.year }} 年度｜{{ CAT_LABEL[s.category] || s.category }}｜
          金額 {{ s.amount }}｜名額 {{ s.quota }}
          <span v-if="s.min_gpa"> ｜最低GPA {{ s.min_gpa }}</span>
          <span v-if="s.department_limit"> ｜限 {{ s.department_limit }}</span>
        </p>
        <p class="desc" v-if="s.description">{{ s.description }}</p>
        <p class="deadline">截止：{{ fmtDate(s.deadline) }}</p>

        <div v-if="canManage" class="ops">
          <button class="link" @click="startEdit(s)">編輯</button>
          <button class="link danger" @click="remove(s)">刪除</button>
        </div>

        <div v-if="editingId === s.scholarship_id" class="edit">
          <div class="form-grid">
            <label>名稱<input v-model="editForm.name" /></label>
            <label>年度<input v-model="editForm.year" type="number" /></label>
            <label>金額<input v-model="editForm.amount" type="number" /></label>
            <label>名額<input v-model="editForm.quota" type="number" /></label>
            <label>最低GPA<input v-model="editForm.min_gpa" type="number" step="0.01" /></label>
            <label>限定系所<input v-model="editForm.department_limit" /></label>
            <label>分類
              <select v-model="editForm.category">
                <option v-for="c in CATEGORIES" :key="c" :value="c">{{ CAT_LABEL[c] }}</option>
              </select>
            </label>
            <label>狀態
              <select v-model="editForm.status">
                <option value="OPEN">開放中</option>
                <option value="CLOSED">已關閉</option>
              </select>
            </label>
            <label>截止時間<input v-model="editForm.deadline" type="datetime-local" /></label>
            <label class="full">說明<textarea v-model="editForm.description" rows="2"></textarea></label>
          </div>
          <button class="primary" @click="submitEdit(s.scholarship_id)">儲存</button>
          <button class="ghost" @click="cancelEdit">取消</button>
        </div>
      </article>
    </div>
  </main>
</template>

<style scoped>
.page { max-width: 920px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
h2 { font-size: 16px; margin: 0 0 12px; }
h3 { margin: 0; font-size: 17px; }
.card, .sch { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg); padding: 18px; box-shadow: var(--shadow-xs); }
.card { margin-bottom: 18px; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 12px; }
.full { grid-column: 1 / -1; }
label { display: flex; flex-direction: column; font-size: 13px; color: var(--text-secondary); gap: 4px; }
.primary { background: var(--primary); color: #fff; border: none; padding: 9px 16px; border-radius: var(--radius-sm); cursor: pointer; margin-right: 8px; font-weight: 600; }
.primary:hover { background: var(--primary-strong); }
.ghost { background: var(--surface-muted); color: var(--text-secondary); border: none; padding: 9px 16px; border-radius: var(--radius-sm); cursor: pointer; }
.ghost:hover { background: var(--surface-sunken); color: var(--text); }
.list { display: flex; flex-direction: column; gap: 14px; }
.sch-head { display: flex; align-items: center; justify-content: space-between; }
.meta { color: var(--text-secondary); font-size: 14px; }
.desc { color: var(--text-secondary); }
.deadline { color: var(--muted); font-size: 13px; font-family: var(--font-mono); }
.ops { display: flex; gap: 12px; margin-top: 6px; }
.link { background: none; border: none; color: var(--primary); cursor: pointer; text-decoration: underline; font-size: 13px; padding: 0; }
.link:hover { color: var(--primary-strong); }
.link.danger { color: var(--danger); }
.edit { margin-top: 12px; border-top: 1px dashed var(--line); padding-top: 12px; }
.pill { padding: 2px 10px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 700; }
.pill.open { background: var(--success-soft); color: var(--success); }
.pill.closed { background: var(--surface-sunken); color: var(--muted); }
.muted { color: var(--muted); }
.notice { color: var(--success); }
.error { color: var(--danger); }
</style>
