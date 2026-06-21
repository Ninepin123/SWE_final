<script setup>
// NCS 內建留言系統（NUKSAMS018）：學生與審查／獎助單位人員針對單一申請案互動。
import { onMounted, ref, watch } from 'vue'
import { listApplicationMessages, createApplicationMessage } from '@/api/ncs'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  applicationId: { type: [Number, String], required: true },
})

const auth = useAuthStore()
const toast = useToastStore()
const messages = ref([])
const draft = ref('')
const loading = ref(false)
const sending = ref(false)

const myId = () => auth.user?.user_id ?? auth.user?.id

function formatTime(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function load() {
  if (!props.applicationId) return
  loading.value = true
  try {
    const data = await listApplicationMessages(props.applicationId)
    messages.value = Array.isArray(data) ? data : []
  } catch (error) {
    toast.error(error.response?.data?.detail || error.message || '留言載入失敗')
  } finally {
    loading.value = false
  }
}

async function send() {
  const body = draft.value.trim()
  if (!body) return
  sending.value = true
  try {
    await createApplicationMessage(props.applicationId, body)
    draft.value = ''
    await load()
  } catch (error) {
    toast.error(error.response?.data?.detail || error.message || '留言送出失敗')
  } finally {
    sending.value = false
  }
}

watch(() => props.applicationId, load)
onMounted(load)
</script>

<template>
  <div class="message-board">
    <p v-if="loading" class="muted-text">留言載入中…</p>
    <p v-else-if="!messages.length" class="muted-text">目前沒有留言，輸入訊息開始與承辦人員溝通。</p>
    <ul v-else class="message-list">
      <li
        v-for="message in messages"
        :key="message.message_id"
        :class="['message-item', message.sender_id === myId() ? 'message-item--mine' : '']"
      >
        <div class="message-bubble">
          <span class="message-meta">{{ message.sender_id === myId() ? '我' : '對方' }} · {{ formatTime(message.created_at) }}</span>
          <p class="message-text">{{ message.body }}</p>
        </div>
      </li>
    </ul>

    <form class="message-input" @submit.prevent="send">
      <textarea
        v-model="draft"
        rows="2"
        placeholder="輸入訊息，按「送出」即可留言…"
        @keydown.enter.exact.prevent="send"
      />
      <button class="primary-button" type="submit" :disabled="sending || !draft.trim()">
        {{ sending ? '送出中' : '送出' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.message-board {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.message-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 260px;
  overflow-y: auto;
}

.message-item {
  display: flex;
  justify-content: flex-start;
}

.message-item--mine {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 78%;
  padding: 0.5rem 0.7rem;
  border-radius: 12px;
  background: var(--paper, #fbf8f1);
  border: 1px solid var(--line, #ddd5c7);
}

.message-item--mine .message-bubble {
  background: var(--jade-soft, #e7f0ea);
  border-color: var(--jade, #2f6b52);
}

.message-meta {
  display: block;
  font-size: 0.72rem;
  color: var(--ink-soft, #8a8170);
  margin-bottom: 0.2rem;
}

.message-text {
  margin: 0;
  white-space: pre-wrap;
  font-size: 0.92rem;
}

.message-input {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}

.message-input textarea {
  flex: 1;
  resize: vertical;
}
</style>
