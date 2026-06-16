<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listUsers, createUser } from '@/api/aas'

const router = useRouter()
const auth = useAuthStore()

const users = ref([])
const error = ref('')
const msg = ref('')
const form = ref({ account: '', password: '', name: '', role: 'STUDENT', department: '', gpa: '', unit_id: '' })

const ROLES = ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN']

async function load() {
  error.value = ''
  try {
    const { data } = await listUsers()
    users.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '載入失敗'
  }
}

async function submit() {
  msg.value = ''
  error.value = ''
  const f = form.value
  if (!f.account.trim() || !f.password || !f.name.trim()) {
    error.value = '帳號、密碼、姓名為必填'
    return
  }
  const payload = {
    account: f.account.trim(),
    password: f.password,
    name: f.name.trim(),
    role: f.role,
    department: f.department.trim() || null,
    gpa: f.gpa === '' ? null : Number(f.gpa),
    unit_id: f.unit_id === '' ? null : Number(f.unit_id),
  }
  try {
    await createUser(payload)
    msg.value = `已新增帳號 ${payload.account}`
    form.value = { account: '', password: '', name: '', role: 'STUDENT', department: '', gpa: '', unit_id: '' }
    load()
  } catch (e) {
    error.value = e.response?.data?.detail || '新增失敗'
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (auth.role !== 'ADMIN') {
    error.value = '此頁僅限管理員'
    return
  }
  load()
})
</script>

<template>
  <main class="page">
    <header class="bar">
      <RouterLink to="/">← 首頁</RouterLink>
      <h1>帳號管理</h1>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="auth.role === 'ADMIN'" class="form">
      <h2>新增帳號</h2>
      <div class="row">
        <input v-model="form.account" placeholder="帳號 / 學號" />
        <input v-model="form.password" type="password" placeholder="密碼" />
        <input v-model="form.name" placeholder="姓名" />
        <select v-model="form.role">
          <option v-for="r in ROLES" :key="r" :value="r">{{ r }}</option>
        </select>
        <input v-model="form.department" placeholder="科系（選填）" />
        <input v-model="form.gpa" placeholder="GPA（選填）" />
        <input v-model="form.unit_id" placeholder="單位ID（選填）" />
        <button class="primary" @click="submit">新增</button>
      </div>
      <p v-if="msg" class="ok">{{ msg }}</p>
    </section>

    <table v-if="users.length">
      <thead>
        <tr><th>ID</th><th>帳號</th><th>姓名</th><th>角色</th><th>科系</th><th>單位ID</th></tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.user_id">
          <td>{{ u.user_id }}</td><td>{{ u.account }}</td><td>{{ u.name }}</td>
          <td>{{ u.role }}</td><td>{{ u.department || '—' }}</td><td>{{ u.unit_id ?? '—' }}</td>
        </tr>
      </tbody>
    </table>
  </main>
</template>

<style scoped>
.page { max-width: 900px; margin: 4vh auto; padding: 0 16px; font-family: system-ui, sans-serif; }
.bar { display: flex; align-items: center; gap: 16px; }
.bar a { color: #2b6cb0; text-decoration: none; }
h1 { font-size: 22px; }
.form { border: 1px solid #e3e3e3; border-radius: 12px; padding: 16px; margin: 12px 0 20px; }
.row { display: flex; flex-wrap: wrap; gap: 8px; }
input, select { padding: 8px 10px; border: 1px solid #ccc; border-radius: 8px; font-size: 14px; }
.primary { padding: 8px 16px; border: none; border-radius: 8px; background: #2b6cb0; color: #fff; cursor: pointer; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { border-bottom: 1px solid #eee; padding: 8px 10px; text-align: left; }
th { background: #f7f9fb; }
.error { color: #c0392b; }
.ok { color: #1a7f37; }
</style>
