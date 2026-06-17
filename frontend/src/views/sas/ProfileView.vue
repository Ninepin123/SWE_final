<script setup>
// SAS 個人資料（學生）：身分資料唯讀，聯絡方式/緊急聯絡人可編輯。
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getProfile, updateProfile } from '@/api/sas'

const router = useRouter()
const auth = useAuthStore()

const identity = ref(null)
const form = reactive({ contact_phone: '', address: '', emergency_contact_name: '', emergency_contact_phone: '' })
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const notice = ref('')

const isStudent = computed(() => auth.role === 'STUDENT')

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await getProfile()
    identity.value = data
    Object.assign(form, {
      contact_phone: data.contact_phone || '',
      address: data.address || '',
      emergency_contact_name: data.emergency_contact_name || '',
      emergency_contact_phone: data.emergency_contact_phone || '',
    })
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true; error.value = ''; notice.value = ''
  try {
    await updateProfile({
      contact_phone: form.contact_phone || null,
      address: form.address || null,
      emergency_contact_name: form.emergency_contact_name || null,
      emergency_contact_phone: form.emergency_contact_phone || null,
    })
    notice.value = '已儲存'
  } catch (e) {
    error.value = e?.response?.data?.detail || '儲存失敗'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  if (isStudent.value) load()
})
</script>

<template>
  <main class="page">
    <h1>個人資料</h1>
    <p v-if="!isStudent" class="warn">此功能僅限學生帳號。</p>

    <template v-else>
      <p v-if="loading">載入中…</p>
      <template v-else-if="identity">
        <section class="card readonly">
          <h2>身分資料（不可修改）</h2>
          <div class="rows">
            <div><span class="k">姓名</span>{{ identity.name }}</div>
            <div><span class="k">學號</span>{{ identity.account }}</div>
            <div><span class="k">系所</span>{{ identity.department || '—' }}</div>
            <div><span class="k">GPA</span>{{ identity.gpa ?? '—' }}</div>
            <div><span class="k">Email</span>{{ identity.email || '—' }}</div>
          </div>
          <p class="hint">如需修改學號、姓名、GPA 等核心資料，請洽系統管理員。</p>
        </section>

        <section class="card">
          <h2>聯絡資料（可修改）</h2>
          <div class="form">
            <label>聯絡電話<input v-model="form.contact_phone" /></label>
            <label>通訊地址<input v-model="form.address" /></label>
            <label>緊急聯絡人<input v-model="form.emergency_contact_name" /></label>
            <label>緊急聯絡電話<input v-model="form.emergency_contact_phone" /></label>
          </div>
          <button class="primary" :disabled="saving" @click="save">{{ saving ? '儲存中…' : '儲存' }}</button>
          <span v-if="notice" class="notice">{{ notice }}</span>
          <span v-if="error" class="error">{{ error }}</span>
        </section>
      </template>
    </template>
  </main>
</template>

<style scoped>
.page { max-width: 640px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
h2 { font-size: 16px; margin: 0 0 12px; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; margin-bottom: 16px; }
.readonly { background: #f7fafc; }
.rows { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px; }
.rows .k { display: inline-block; width: 60px; color: #718096; }
.hint { color: #a0aec0; font-size: 12px; margin: 12px 0 0; }
.form { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
label { display: flex; flex-direction: column; font-size: 13px; color: #4a5568; gap: 4px; }
input { padding: 8px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 14px; }
.primary { background: #2b6cb0; color: #fff; border: none; padding: 9px 18px; border-radius: 8px; cursor: pointer; margin-right: 10px; }
.primary:disabled { opacity: .6; cursor: default; }
.notice { color: #22732f; }
.error { color: #c53030; }
.warn { color: #c05621; }
</style>
