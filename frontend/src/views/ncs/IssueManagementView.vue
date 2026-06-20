<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import {
  createIssueReply,
  listAllIssues,
  listIssueReplies,
  updateIssueReport,
} from '@/api/ncs'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const loading = ref(true)
const updatingId = ref(null)
const error = ref('')
const success = ref('')
const issues = ref([])
const selectedIssue = ref(null)
const replies = ref([])
const replyBody = ref('')
const replyLoading = ref(false)
const replySubmitting = ref(false)

const statusOptions = [
  { label: '待處理', value: 'OPEN' },
  { label: '處理中', value: 'IN_PROGRESS' },
  { label: '已解決', value: 'RESOLVED' },
  { label: '已關閉', value: 'CLOSED' },
]

const issueTypeLabels = {
  BUG: '系統錯誤',
  QUESTION: '操作問題',
  SUGGESTION: '改善建議',
}

const statusLabels = {
  OPEN: '待處理',
  IN_PROGRESS: '處理中',
  RESOLVED: '已解決',
  CLOSED: '已關閉',
}

const sortedIssues = computed(() => {
  return [...issues.value].sort((a, b) => {
    const left = new Date(a.created_at ?? a.createdAt ?? 0).getTime()
    const right = new Date(b.created_at ?? b.createdAt ?? 0).getTime()
    return right - left
  })
})

const currentUserId = computed(() => auth.user?.user_id ?? auth.user?.id ?? null)

function issueIdOf(issue) {
  return issue.issue_id ?? issue.issueId ?? issue.id
}

function statusOf(issue) {
  return issue.status ?? 'OPEN'
}

function reporterIdOf(issue) {
  return issue.reporter_id ?? issue.reporterId ?? '-'
}

function replierIdOf(reply) {
  return reply.replier_id ?? reply.replierId ?? null
}

function isReporterReply(reply) {
  return replierIdOf(reply) === reporterIdOf(selectedIssue.value)
}

function replyAuthorLabel(reply) {
  const replierId = replierIdOf(reply)

  if (isReporterReply(reply)) return `使用者回覆 ID：${replierId ?? '-'}`
  if (replierId === currentUserId.value) return '我的管理員回覆'
  return `管理員回覆 ID：${replierId ?? '-'}`
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'

  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function resolveErrorMessage(err, fallback = '操作失敗') {
  return err?.response?.data?.detail || err?.message || fallback
}

async function loadIssues() {
  loading.value = true
  error.value = ''
  success.value = ''

  try {
    issues.value = await listAllIssues()
  } catch (err) {
    error.value = resolveErrorMessage(err, '問題回報載入失敗')
  } finally {
    loading.value = false
  }
}

async function changeStatus(issue, nextStatus) {
  const issueId = issueIdOf(issue)

  if (!issueId) {
    error.value = '找不到問題編號'
    return
  }

  updatingId.value = issueId
  error.value = ''
  success.value = ''

  try {
    const updated = await updateIssueReport(issueId, { status: nextStatus })

    issues.value = issues.value.map((item) => {
      if (issueIdOf(item) !== issueId) return item
      return {
        ...item,
        ...updated,
        status: nextStatus,
      }
    })

    if (selectedIssue.value && issueIdOf(selectedIssue.value) === issueId) {
      selectedIssue.value = {
        ...selectedIssue.value,
        ...updated,
        status: nextStatus,
      }
    }

    success.value = '問題狀態已更新'
  } catch (err) {
    error.value = resolveErrorMessage(err, '狀態更新失敗')
  } finally {
    updatingId.value = null
  }
}

async function openIssue(issue) {
  selectedIssue.value = issue
  replies.value = []
  replyBody.value = ''
  error.value = ''
  success.value = ''

  const issueId = issueIdOf(issue)
  if (!issueId) return

  replyLoading.value = true

  try {
    replies.value = await listIssueReplies(issueId)
  } catch (err) {
    error.value = resolveErrorMessage(err, '回覆紀錄載入失敗')
  } finally {
    replyLoading.value = false
  }
}

async function submitReply() {
  if (!selectedIssue.value) return

  const issueId = issueIdOf(selectedIssue.value)

  if (!replyBody.value.trim()) {
    error.value = '請輸入回覆內容'
    return
  }

  error.value = ''
  success.value = ''
  replySubmitting.value = true

  try {
    const reply = await createIssueReply(issueId, replyBody.value.trim())
    replies.value.push(reply)
    replyBody.value = ''
    success.value = '回覆已送出'

    const updatedAt = reply?.created_at ?? reply?.createdAt ?? new Date().toISOString()
    selectedIssue.value = {
      ...selectedIssue.value,
      updated_at: updatedAt,
      updatedAt,
    }
    issues.value = issues.value.map((issue) => (
      issueIdOf(issue) === issueId
        ? { ...issue, updated_at: updatedAt, updatedAt }
        : issue
    ))

    if (statusOf(selectedIssue.value) === 'OPEN') {
      await changeStatus(selectedIssue.value, 'IN_PROGRESS')
    }
  } catch (err) {
    error.value = resolveErrorMessage(err, '回覆送出失敗')
  } finally {
    replySubmitting.value = false
  }
}

onMounted(loadIssues)
</script>

<template>
  <div class="page-grid">
    <BaseCard title="問題回報管理" eyebrow="NCS Issue Management">
      <p>管理員可查看所有使用者回報的系統錯誤、操作問題與改善建議，並更新處理狀態或回覆使用者。</p>
    </BaseCard>

    <BaseCard v-if="error" title="錯誤訊息">
      <p class="form-error">{{ error }}</p>
      <button class="primary-button" type="button" @click="loadIssues">
        重新載入
      </button>
    </BaseCard>

    <BaseCard v-if="success" title="操作成功">
      <p class="form-success">{{ success }}</p>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />

    <EmptyState
      v-else-if="sortedIssues.length === 0"
      title="目前沒有問題回報"
      description="使用者送出問題回報後，會出現在這裡。"
    />

    <section v-else class="issue-layout" :class="{ 'issue-layout--with-panel': selectedIssue }">
      <div class="issue-list">
        <BaseCard
          v-for="issue in sortedIssues"
          :key="issueIdOf(issue)"
          class="issue-card"
          :class="{ 'issue-card--active': selectedIssue && issueIdOf(selectedIssue) === issueIdOf(issue) }"
        >
          <div class="issue-card__header">
            <div>
              <span class="issue-card__type">
                {{ issueTypeLabels[issue.issue_type ?? issue.issueType] ?? issue.issue_type ?? issue.issueType }}
              </span>
              <h3>{{ issue.title }}</h3>
            </div>

            <span class="status-badge">
              {{ statusLabels[statusOf(issue)] ?? statusOf(issue) }}
            </span>
          </div>

          <p class="issue-card__description">
            {{ issue.description }}
          </p>

          <div class="issue-card__meta">
            <span>回報者 ID：{{ reporterIdOf(issue) }}</span>
            <span>建立時間：{{ formatDate(issue.created_at ?? issue.createdAt) }}</span>
          </div>

          <div v-if="issue.attachment_name || issue.attachmentName" class="issue-card__attachment">
            附件：{{ issue.attachment_name ?? issue.attachmentName }}
          </div>

          <div class="issue-card__actions">
            <button class="secondary-button" type="button" @click="openIssue(issue)">
              查看 / 回覆
            </button>

            <select
              :value="statusOf(issue)"
              :disabled="updatingId === issueIdOf(issue)"
              @change="changeStatus(issue, $event.target.value)"
            >
              <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </BaseCard>
      </div>

      <BaseCard v-if="selectedIssue" class="reply-panel" title="討論紀錄">
        <div class="reply-panel__issue">
          <strong>{{ selectedIssue.title }}</strong>
          <p>{{ selectedIssue.description }}</p>
        </div>

        <LoadingSkeleton v-if="replyLoading" :rows="3" />

        <div v-else-if="replies.length === 0" class="reply-empty">
          尚無討論紀錄。
        </div>

        <div v-else class="reply-list">
          <div
            v-for="reply in replies"
            :key="reply.reply_id ?? reply.replyId"
            class="reply-item"
            :class="{ 'reply-item--reporter': isReporterReply(reply) }"
          >
            <div class="reply-item__header">
              <strong>{{ replyAuthorLabel(reply) }}</strong>
              <span>{{ formatDate(reply.created_at ?? reply.createdAt) }}</span>
            </div>
            <p>{{ reply.body }}</p>
          </div>
        </div>

        <form class="reply-form" @submit.prevent="submitReply">
          <label>
            管理員回覆
            <textarea v-model="replyBody" rows="4" placeholder="請輸入回覆內容，送出後使用者會收到通知"></textarea>
          </label>

          <button class="primary-button" type="submit" :disabled="replyLoading || replySubmitting">
            {{ replySubmitting ? '送出中...' : '送出回覆' }}
          </button>
        </form>
      </BaseCard>
    </section>
  </div>
</template>

<style scoped>
.issue-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  align-items: start;
}

.issue-layout--with-panel {
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
}

.issue-list {
  display: grid;
  gap: 1rem;
}

.issue-card {
  border: 1px solid transparent;
}

.issue-card--active {
  border-color: #2563eb;
}

.issue-card__header,
.issue-card__meta,
.issue-card__actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: center;
}

.issue-card__header h3 {
  margin: 0.25rem 0 0;
}

.issue-card__type,
.issue-card__meta,
.issue-card__attachment {
  color: var(--color-text-muted, #64748b);
  font-size: 0.85rem;
}

.issue-card__description {
  white-space: pre-wrap;
  line-height: 1.6;
}

.status-badge {
  border-radius: 999px;
  padding: 0.35rem 0.7rem;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
  font-size: 0.85rem;
}

.issue-card__actions select,
.reply-form textarea {
  border: 1px solid var(--color-border, #cbd5e1);
  border-radius: 0.75rem;
  padding: 0.65rem;
  font: inherit;
}

.reply-panel {
  position: sticky;
  top: 1rem;
}

.reply-panel__issue {
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}

.reply-list {
  display: grid;
  gap: 0.75rem;
}

.reply-item {
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.75rem;
  padding: 0.75rem;
}

.reply-item--reporter {
  background: #f0fdf4;
  border-color: #86efac;
}

.reply-item__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: var(--color-text-muted, #64748b);
  font-size: 0.85rem;
}

.reply-item p {
  white-space: pre-wrap;
  line-height: 1.6;
}

.reply-empty {
  color: var(--color-text-muted, #64748b);
}

.reply-form {
  margin-top: 1rem;
  display: grid;
  gap: 0.75rem;
}

.reply-form label {
  display: grid;
  gap: 0.4rem;
  font-weight: 600;
}

.form-error {
  color: #b91c1c;
  font-weight: 700;
}

.form-success {
  color: #15803d;
  font-weight: 700;
}

@media (max-width: 960px) {
  .issue-layout {
    grid-template-columns: 1fr;
  }

  .reply-panel {
    position: static;
  }
}
</style>
