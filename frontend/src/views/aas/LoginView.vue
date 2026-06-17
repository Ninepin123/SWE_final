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
  <main class="login-page">
    <section class="login-hero">
      <div class="seal seal--watermark" aria-hidden="true">奬</div>
      <p class="eyebrow">NUKSAMS</p>
      <h1>高雄大學<br />獎助學金申請與管理系統</h1>
      <p class="login-hero__lede">
        整合獎學金公告、線上申請、推薦信邀請、審查作業與通知，
        讓學生、推薦人、審查單位與管理員在同一平台上協作。
      </p>
      <div class="login-hero__badges">
        <span>線上申請</span>
        <span>推薦信追蹤</span>
        <span>分流審查</span>
      </div>
    </section>

    <section class="login-panel">
      <div class="login-panel__header">
        <h2>登入系統</h2>
        <p>請輸入帳號與密碼。首次使用請聯繫系統管理員開通帳號。</p>
      </div>

      <div class="login-form">
        <label class="field">
          <span>帳號</span>
          <input v-model="account" placeholder="例如 A1125529 / admin" autocomplete="username" @keyup.enter="submit" />
        </label>
        <label class="field">
          <span>密碼</span>
          <input v-model="password" type="password" placeholder="••••••••" autocomplete="current-password" @keyup.enter="submit" />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="primary-button" :disabled="loading" @click="submit">
          {{ loading ? '登入中…' : '登入' }}
        </button>
      </div>

      <div class="login-divider">示範帳號（點選自動填入，密碼皆為 <code>password123</code>）</div>

      <div class="login-demo">
        <button class="login-demo__chip" @click="quickFill('admin')">
          <strong>系統管理員</strong><small class="mono">admin</small>
        </button>
        <button class="login-demo__chip" @click="quickFill('sponsor')">
          <strong>獎助單位</strong><small class="mono">sponsor</small>
        </button>
        <button class="login-demo__chip" @click="quickFill('reviewer')">
          <strong>審查人員</strong><small class="mono">reviewer</small>
        </button>
        <button class="login-demo__chip" @click="quickFill('A1125529')">
          <strong>學生</strong><small class="mono">A1125529</small>
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  grid-template-columns: minmax(0, 1.05fr) minmax(420px, 1fr);
  background: var(--surface);
}

.login-hero {
  position: relative;
  display: grid;
  align-content: center;
  gap: 18px;
  padding: 64px;
  overflow: hidden;
  color: #f1ead9;
  background:
    radial-gradient(120% 95% at 82% 12%, rgba(187, 59, 42, 0.2), transparent 52%),
    radial-gradient(90% 80% at 8% 96%, rgba(138, 106, 44, 0.18), transparent 60%),
    linear-gradient(158deg, #2d261a 0%, #211c14 58%, #191510 100%);
}

.login-hero .seal--watermark {
  position: absolute;
  right: -34px;
  bottom: -30px;
  z-index: 0;
}

.login-hero > *:not(.seal--watermark) {
  position: relative;
  z-index: 1;
}

.login-hero .eyebrow {
  color: #d9b07a;
}

.login-hero .eyebrow::before {
  background: #e26a45;
}

.login-hero h1 {
  max-width: 600px;
  font-size: 42px;
  color: #fbf6ec;
  line-height: 1.18;
}

.login-hero__lede {
  max-width: 520px;
  color: rgba(241, 234, 217, 0.78);
  line-height: 1.85;
}

.login-hero__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

.login-hero__badges span {
  padding: 6px 13px;
  border: 1px solid rgba(241, 234, 217, 0.22);
  border-radius: var(--radius-pill);
  background: rgba(241, 234, 217, 0.07);
  color: rgba(241, 234, 217, 0.92);
  font-size: 13px;
  font-weight: 600;
}

.login-panel {
  display: grid;
  align-content: center;
  gap: 22px;
  padding: 56px 48px;
}

.login-panel__header h2 {
  font-size: 25px;
}

.login-panel__header p {
  margin-top: 8px;
  color: var(--muted);
  line-height: 1.6;
}

.login-form {
  display: grid;
  gap: 16px;
}

.login-form .primary-button {
  margin-top: 2px;
}

.login-divider {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.login-demo {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.login-demo__chip {
  display: grid;
  gap: 3px;
  justify-items: start;
  padding: 11px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.login-demo__chip:hover {
  border-color: var(--primary);
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.login-demo__chip strong {
  font-size: 14px;
}

.login-demo__chip small {
  color: var(--gold);
  font-size: 12px;
}

@media (max-width: 860px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .login-hero {
    padding: 40px 24px;
  }
  .login-hero h1 {
    font-size: 30px;
  }
  .login-panel {
    padding: 36px 24px;
  }
}
</style>
