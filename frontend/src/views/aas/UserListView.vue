<script setup>
// AAS 帳號管理（系統管理員）：新增 / 查詢 / 修改 / 刪除使用者。
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listUsers, createUser, updateUser, deleteUser } from '@/api/aas'

const router = useRouter()
const auth = useAuthStore()

const ROLES = ['STUDENT', 'TEACHER', 'SPONSOR', 'REVIEWER', 'ADMIN']
const ROLE_LABEL = { STUDENT: '學生', TEACHER: '老師', SPONSOR: '獎助單位', REVIEWER: '審查人員', ADMIN: '系統管理員' }

const users = ref([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

const isAdmin = computed(() => auth.role === 'ADMIN')

const createForm = reactive({
  account: '', password: '', name: '', role: 'STUDENT', email: '', department: '', gpa: '', unit_id: '',
})

const editingId = ref(null)
const editForm = reactive({
  name: '', email: '', role: 'STUDENT', department: '', gpa: '', status: 'ACTIVE', unit_id: '', password: '',
})

function numOrNull(v) {
  return v === '' || v === null ? null : Number(v)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await listUsers()
    users.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  error.value = ''; notice.value = ''
  try {
    await createUser({
      account: createForm.account,
      password: createForm.password,
      name: createForm.name,
      role: createForm.role,
      email: createForm.email || null,
      department: createForm.department || null,
      gpa: numOrNull(createForm.gpa),
      unit_id: numOrNull(createForm.unit_id),
    })
    notice.value = `已新增帳號 ${createForm.account}`
    Object.assign(createForm, { account: '', password: '', name: '', role: 'STUDENT', email: '', department: '', gpa: '', unit_id: '' })
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '新增失敗'
  }
}

function startEdit(u) {
  editingId.value = u.user_id
  Object.assign(editForm, {
    name: u.name || '', email: u.email || '', role: u.role, department: u.department || '',
    gpa: u.gpa ?? '', status: u.status || 'ACTIVE', unit_id: u.unit_id ?? '', password: '',
  })
}
function cancelEdit() { editingId.value = null }

async function submitEdit(id) {
  error.value = ''; notice.value = ''
  const payload = {
    name: editForm.name,
    email: editForm.email || null,
    role: editForm.role,
    department: editForm.department || null,
    gpa: numOrNull(editForm.gpa),
    status: editForm.status,
    unit_id: numOrNull(editForm.unit_id),
  }
  if (editForm.password) payload.password = editForm.password
  try {
    await updateUser(id, payload)
    notice.value = '已更新帳號'
    editingId.value = null
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '更新失敗'
  }
}

async function remove(u) {
  if (!confirm(`確定刪除帳號「${u.name}（${u.account}）」？`)) return
  error.value = ''; notice.value = ''
  try {
    await deleteUser(u.user_id)
    notice.value = '已刪除帳號'
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
    <h1>帳號管理</h1>
    <p v-if="!isAdmin" class="warn">此功能僅限系統管理員。</p>

    <template v-else>
      <section class="card">
        <h2>新增帳號</h2>
        <div class="form-grid">
          <label>帳號<input v-model="createForm.account" /></label>
          <label>密碼<input v-model="createForm.password" type="password" /></label>
          <label>姓名<input v-model="createForm.name" /></label>
          <label>角色
            <select v-model="createForm.role">
              <option v-for="r in ROLES" :key="r" :value="r">{{ ROLE_LABEL[r] }}</option>
            </select>
          </label>
          <label>Email<input v-model="createForm.email" /></label>
          <label>系所<input v-model="createForm.department" /></label>
          <label>GPA<input v-model="createForm.gpa" type="number" step="0.01" /></label>
          <label>單位ID（獎助/審查單位用）<input v-model="createForm.unit_id" type="number" /></label>
        </div>
        <button class="primary" @click="submitCreate">新增</button>
      </section>

      <p v-if="notice" class="notice">{{ notice }}</p>
      <p v-if="error" class="error">{{ error }}</p>

      <section class="card">
        <h2>帳號清單</h2>
        <p v-if="loading">載入中…</p>
        <table v-else class="tbl">
          <thead>
            <tr><th>ID</th><th>帳號</th><th>姓名</th><th>角色</th><th>系所</th><th>GPA</th><th>狀態</th><th>操作</th></tr>
          </thead>
          <tbody>
            <template v-for="u in users" :key="u.user_id">
              <tr>
                <td>{{ u.user_id }}</td>
                <td>{{ u.account }}</td>
                <td>{{ u.name }}</td>
                <td>{{ ROLE_LABEL[u.role] || u.role }}</td>
                <td>{{ u.department || '—' }}</td>
                <td>{{ u.gpa ?? '—' }}</td>
                <td><span :class="['pill', u.status === 'ACTIVE' ? 'ok' : 'off']">{{ u.status === 'ACTIVE' ? '啟用' : '停用' }}</span></td>
                <td class="ops">
                  <button class="link" @click="startEdit(u)">編輯</button>
                  <button class="link danger" @click="remove(u)">刪除</button>
                </td>
              </tr>
              <tr v-if="editingId === u.user_id" class="edit-row">
                <td colspan="8">
                  <div class="form-grid">
                    <label>姓名<input v-model="editForm.name" /></label>
                    <label>角色
                      <select v-model="editForm.role">
                        <option v-for="r in ROLES" :key="r" :value="r">{{ ROLE_LABEL[r] }}</option>
                      </select>
                    </label>
                    <label>Email<input v-model="editForm.email" /></label>
                    <label>系所<input v-model="editForm.department" /></label>
                    <label>GPA<input v-model="editForm.gpa" type="number" step="0.01" /></label>
                    <label>單位ID<input v-model="editForm.unit_id" type="number" /></label>
                    <label>狀態
                      <select v-model="editForm.status">
                        <option value="ACTIVE">啟用</option>
                        <option value="DISABLED">停用</option>
                      </select>
                    </label>
                    <label>重設密碼（留空不改）<input v-model="editForm.password" type="password" /></label>
                  </div>
                  <button class="primary" @click="submitEdit(u.user_id)">儲存</button>
                  <button class="ghost" @click="cancelEdit">取消</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </section>
    </template>
  </main>
</template>

<style scoped>
.page { max-width: 1000px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
h2 { font-size: 16px; margin: 0 0 12px; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; margin-bottom: 18px; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 12px; }
label { display: flex; flex-direction: column; font-size: 13px; color: #4a5568; gap: 4px; }
input, select { padding: 8px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 14px; }
.primary { background: #2b6cb0; color: #fff; border: none; padding: 9px 16px; border-radius: 8px; cursor: pointer; margin-right: 8px; }
.ghost { background: #edf2f7; border: none; padding: 9px 16px; border-radius: 8px; cursor: pointer; }
.tbl { width: 100%; border-collapse: collapse; font-size: 14px; }
.tbl th, .tbl td { text-align: left; padding: 9px 8px; border-bottom: 1px solid #edf2f7; }
.ops { display: flex; gap: 10px; }
.link { background: none; border: none; color: #2b6cb0; cursor: pointer; text-decoration: underline; font-size: 13px; padding: 0; }
.link.danger { color: #e53e3e; }
.edit-row td { background: #f7fafc; }
.pill { padding: 2px 8px; border-radius: 999px; font-size: 12px; }
.pill.ok { background: #c6f6d5; color: #22543d; }
.pill.off { background: #fed7d7; color: #742a2a; }
.notice { color: #22732f; }
.error { color: #c53030; }
.warn { color: #c05621; }
</style>
