<script setup>
// NCS 我的通知。
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { listNotifications, markRead } from '@/api/ncs'

const router = useRouter()
const auth = useAuthStore()
const items = ref([])
const loading = ref(false)
const error = ref('')

function fmtDate(t) { return t ? new Date(t).toLocaleString('zh-TW') : '' }

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await listNotifications()
    items.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail || '載入失敗'
  } finally {
    loading.value = false
  }
}

async function read(n) {
  try {
    await markRead(n.notification_id)
    await load()
  } catch (e) {
    error.value = e?.response?.data?.detail || '操作失敗'
  }
}

onMounted(() => {
  if (!auth.isLoggedIn) return router.push('/login')
  load()
})
</script>

<template>
  <main class="page">
    <h1>我的通知</h1>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading">載入中…</p>
    <p v-else-if="items.length === 0" class="muted">目前沒有通知。</p>

    <ul v-else class="list">
      <li v-for="n in items" :key="n.notification_id" :class="['item', { unread: !n.is_read }]">
        <div class="row">
          <strong>{{ n.title }}</strong>
          <span class="time">{{ fmtDate(n.created_at) }}</span>
        </div>
        <p v-if="n.body" class="body">{{ n.body }}</p>
        <button v-if="!n.is_read" class="link" @click="read(n)">標記為已讀</button>
      </li>
    </ul>
  </main>
</template>

<style scoped>
.page { max-width: 680px; margin: 28px auto; padding: 0 16px; }
h1 { font-size: 22px; }
.list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.item { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md); padding: 14px; box-shadow: var(--shadow-xs); }
.item.unread { border-left: 4px solid var(--primary); background: var(--primary-tint); }
.row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.time { color: var(--muted); font-size: 12px; white-space: nowrap; font-family: var(--font-mono); }
.body { color: var(--text-secondary); font-size: 14px; margin: 6px 0; }
.link { background: none; border: none; color: var(--primary); cursor: pointer; text-decoration: underline; font-size: 13px; padding: 0; }
.link:hover { color: var(--primary-strong); }
.muted { color: var(--muted); }
.error { color: var(--danger); }
</style>
