<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const account = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const HOME_BY_ROLE = {
  STUDENT: '/sas/apply',
  SPONSOR: '/sms/scholarships',
  REVIEWER: '/ras/applications',
  ADMIN: '/aas/users',
  TEACHER: '/',
}

async function submit() {
  if (!account.value.trim() || !password.value) {
    error.value = '請輸入帳號與密碼'
    return
  }
  error.value = ''
  loading.value = true
  try {
    const user = await auth.login(account.value.trim(), password.value)
    router.push(HOME_BY_ROLE[user.role] || '/')
  } catch (e) {
    error.value = e.response?.data?.detail || '登入失敗，請稍後再試'
  } finally {
    loading.value = false
  }
}

function quickFill(acc) {
  account.value = acc
  password.value = 'password123'
}
</script>

<template>
  <main class="login">
    <h1>NUKSAMS</h1>
    <p class="sub">高雄大學獎(助)學金申請與管理系統</p>

    <div class="card">
      <label>帳號
        <input v-model="account" placeholder="例如 A1125529 / admin" @keyup.enter="submit" />
      </label>
      <label>密碼
        <input v-model="password" type="password" placeholder="password123" @keyup.enter="submit" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="primary" :disabled="loading" @click="submit">
        {{ loading ? '登入中…' : '登入' }}
      </button>
    </div>

    <div class="demo">
      <p>示範帳號（點選自動填入，密碼皆為 <code>password123</code>）</p>
      <div class="chips">
        <button class="chip" @click="quickFill('admin')">admin · 管理員</button>
        <button class="chip" @click="quickFill('sponsor')">sponsor · 獎助單位</button>
        <button class="chip" @click="quickFill('reviewer')">reviewer · 審查</button>
        <button class="chip" @click="quickFill('A1125529')">A1125529 · 學生</button>
      </div>
    </div>
  </main>
</template>

<style scoped>
.login { max-width: 420px; margin: 8vh auto; padding: 0 16px; font-family: system-ui, sans-serif; }
h1 { margin: 0; text-align: center; letter-spacing: 2px; }
.sub { text-align: center; color: #666; margin: 4px 0 24px; }
.card { display: flex; flex-direction: column; gap: 14px; padding: 24px; border: 1px solid #e3e3e3; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,.04); }
label { display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #333; }
input { padding: 10px 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 15px; }
input:focus { outline: none; border-color: #2b6cb0; }
.primary { padding: 11px; border: none; border-radius: 8px; background: #2b6cb0; color: #fff; font-size: 15px; cursor: pointer; }
.primary:disabled { opacity: .6; cursor: default; }
.error { color: #c0392b; margin: 0; font-size: 14px; }
.demo { margin-top: 18px; color: #666; font-size: 13px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.chip { padding: 6px 10px; border: 1px solid #cdd; border-radius: 999px; background: #f5f8fb; cursor: pointer; font-size: 12px; }
code { background: #eef; padding: 1px 5px; border-radius: 4px; }
</style>
