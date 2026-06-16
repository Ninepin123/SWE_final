<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listScholarships, createScholarship } from '@/api/sms'

const router = useRouter()
const auth = useAuthStore()

const items = ref([])
const error = ref('')
const msg = ref('')
const canManage = computed(() => auth.role === 'SPONSOR' || auth.role === 'ADMIN')

const CATEGORIES = ['SCHOOL', 'GOVERNMENT', 'PRIVATE', 'LOW_INCOME', 'MERIT', 'OTHER']
const CATEGORY_LABEL = {
  SCHOOL: '校內', GOVERNMENT: '政府', PRIVATE: '私人贊助', LOW_INCOME: '清寒', MERIT: '成績優良', OTHER: '其他',
}

const form = ref({
  name: '', year: new Date().getFullYear(), amount: '', quota: 1,
  min_gpa: '', department_limit: '', category: 'OTHER', description: '', deadline: '',
})

async function load() {
  error.value = ''
  try {
    const { data } = await listScholarships()
    items.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '載入失敗'
  }
}

function num(v) {
  return v === '' || v === null ? null : Number(v)
}

async function submit() {
  msg.value = ''
  error.value = ''
  const f = form.value
  if (!f.name.trim() || !f.year) {
    error.value = '獎學金名稱與年度為必填'
    return
  }
  const payload = {
    name: f.name.trim(),
    year: Number(f.year),
    amount: num(f.amount) ?? 0,
    quota: num(f.quota) ?? 1,
    min_gpa: num(f.min_gpa),
    department_limit: f.department_limit.trim() || null,
    category: f.category,
    description: f.description.trim() || null,
    deadline: f.deadline ? f.deadline : null,
  }
  try {
    await createScholarship(payload)
    msg.value = `已新增獎學金「${payload.name}」`
    form.value = { name: '', year: new Date().getFullYear(), amount: '', quota: 1, min_gpa: '', department_limit: '', category: 'OTHER', description: '', deadline: '' }
    load()
  } catch (e) {
    error.value = e.response?.data?.detail || '新增失敗'
  }
}

function fmtDeadline(d) {
  if (!d) return '不限'
  return new Date(d).toLocaleString('zh-TW', { dateStyle: 'medium', timeStyle: 'short' })
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  load()
})
</script>

<template>
  <main class="page">
    <header class="bar">
      <RouterLink to="/">← 首頁</RouterLink>
      <h1>獎學金{{ canManage ? '管理' : '列表' }}</h1>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="canManage" class="form">
      <h2>新增獎學金</h2>
      <div class="grid">
        <label>名稱<input v-model="form.name" /></label>
        <label>年度<input v-model="form.year" type="number" /></label>
        <label>金額<input v-model="form.amount" type="number" placeholder="0" /></label>
        <label>名額<input v-model="form.quota" type="number" /></label>
        <label>最低 GPA<input v-model="form.min_gpa" type="number" step="0.01" placeholder="不限" /></label>
        <label>限定科系<input v-model="form.department_limit" placeholder="不限" /></label>
        <label>分類
          <select v-model="form.category">
            <option v-for="c in CATEGORIES" :key="c" :value="c">{{ CATEGORY_LABEL[c] }}</option>
          </select>
        </label>
        <label>截止時間<input v-model="form.deadline" type="datetime-local" /></label>
      </div>
      <label class="full">說明<textarea v-model="form.description" rows="2" /></label>
      <button class="primary" @click="submit">新增</button>
      <p v-if="msg" class="ok">{{ msg }}</p>
    </section>

    <p v-if="!items.length" class="empty">目前沒有獎學金資料。</p>
    <div class="cards">
      <article v-for="s in items" :key="s.scholarship_id" class="card">
        <div class="card-head">
          <h3>{{ s.name }}</h3>
          <span class="badge" :class="s.status === 'OPEN' ? 'open' : 'closed'">
            {{ s.status === 'OPEN' ? '開放中' : '已關閉' }}
          </span>
        </div>
        <p class="meta">
          {{ s.unit_name || ('單位#' + s.unit_id) }} · {{ CATEGORY_LABEL[s.category] || s.category }} · {{ s.year }} 年度
        </p>
        <p class="amount">NT$ {{ s.amount.toLocaleString() }}　名額 {{ s.quota }}</p>
        <p class="cond">
          最低 GPA：{{ s.min_gpa ?? '不限' }}　限定科系：{{ s.department_limit || '不限' }}
        </p>
        <p class="cond">截止：{{ fmtDeadline(s.deadline) }}</p>
        <p v-if="s.description" class="desc">{{ s.description }}</p>
      </article>
    </div>
  </main>
</template>

<style scoped>
.page { max-width: 900px; margin: 4vh auto; padding: 0 16px; font-family: system-ui, sans-serif; }
.bar { display: flex; align-items: center; gap: 16px; }
.bar a { color: #2b6cb0; text-decoration: none; }
h1 { font-size: 22px; }
.form { border: 1px solid #e3e3e3; border-radius: 12px; padding: 16px; margin: 12px 0 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: #444; }
label.full { margin-top: 10px; }
input, select, textarea { padding: 8px 10px; border: 1px solid #ccc; border-radius: 8px; font-size: 14px; }
.primary { margin-top: 12px; padding: 9px 18px; border: none; border-radius: 8px; background: #2b6cb0; color: #fff; cursor: pointer; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.card { border: 1px solid #e3e3e3; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.04); }
.card-head { display: flex; justify-content: space-between; align-items: start; gap: 8px; }
h3 { margin: 0; font-size: 16px; }
.badge { font-size: 12px; padding: 2px 8px; border-radius: 999px; white-space: nowrap; }
.badge.open { background: #e6f4ea; color: #1a7f37; }
.badge.closed { background: #f1f1f1; color: #888; }
.meta { color: #666; font-size: 13px; margin: 6px 0; }
.amount { font-weight: 700; margin: 4px 0; }
.cond { font-size: 13px; color: #555; margin: 2px 0; }
.desc { font-size: 13px; color: #444; margin-top: 8px; }
.error { color: #c0392b; }
.ok { color: #1a7f37; }
.empty { color: #888; }
</style>
