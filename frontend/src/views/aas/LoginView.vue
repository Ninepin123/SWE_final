<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import Icon from '@/components/common/Icon.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const form = reactive({
  account: '',
  password: '',
})
const loading = ref(false)
const error = ref('')

async function login() {
  error.value = ''
  if (!form.account.trim()) {
    error.value = '請輸入帳號。'
    return
  }
  if (!form.password) {
    error.value = '請輸入密碼。'
    return
  }
  loading.value = true
  try {
    await auth.login(form.account.trim(), form.password)
    toast.success(`歡迎，${auth.user?.name}`)
    router.push(route.query.redirect || '/dashboard')
  } catch (loginError) {
    error.value = loginError.response?.data?.detail || loginError.message || '登入失敗'
  } finally {
    loading.value = false
  }
}

</script>

<template>
  <main class="login-page">
    <section class="login-hero">
      <div class="seal seal--watermark" aria-hidden="true">奬</div>
      <p class="eyebrow">NUKSAMS</p>
      <h1>高雄大學<br />獎助學金申請與管理系統</h1>
      <p>
        整合獎學金公告、線上申請、推薦信邀請、審查作業與通知，
        讓學生、推薦人、審查人員與管理員在同一平台上協作。
      </p>
      <div class="login-hero__badges">
        <span><Icon name="check" /> 線上申請</span>
        <span><Icon name="recommend" /> 推薦信追蹤</span>
        <span><Icon name="review" /> 分流審查</span>
      </div>
    </section>

    <section class="login-panel">
      <div class="login-panel__header">
        <h2>登入系統</h2>
        <p>請輸入您的帳號與密碼登入。首次使用請聯繫系統管理員開通帳號。</p>
      </div>

      <form class="login-form" @submit.prevent="login">
        <label>
          <span>帳號</span>
          <input v-model="form.account" type="text" placeholder="學號 / 帳號" autocomplete="username" />
        </label>
        <label>
          <span>密碼</span>
          <input v-model="form.password" type="password" placeholder="••••••••" autocomplete="current-password" />
        </label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="primary-button" type="submit" :disabled="loading">
          <Icon name="lock" />
          {{ loading ? '登入中' : '登入' }}
        </button>
      </form>
    </section>
  </main>
</template>
