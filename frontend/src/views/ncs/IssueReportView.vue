<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { createIssueReply, createIssueReport, listIssueReplies, listMyIssues } from '@/api/ncs'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const issues = ref([])
const error = ref('')
const pageError = ref('')
const replyError = ref('')
const success = ref('')
const loading = ref(false)
const issuesLoading = ref(true)
const showForm = ref(false)
const selectedIssue = ref(null)
const replies = ref([])
const replyLoading = ref(false)
const replySubmitting = ref(false)
const replyBody = ref('')

const form = reactive({
  issue_type: 'BUG',
  title: '',
  description: '',
  attachment_name: '',
  attachment_url: '',
})

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
  return issue?.issue_id ?? issue?.issueId ?? issue?.id
}

function statusOf(issue) {
  return issue?.status ?? 'OPEN'
}

function replierIdOf(reply) {
  return reply?.replier_id ?? reply?.replierId ?? null
}

function isCurrentUserReply(reply) {
  return replierIdOf(reply) === currentUserId.value
}

function replyAuthorLabel(reply) {
  return isCurrentUserReply(reply) ? '我的回覆' : '管理員回覆'
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

function resetForm() {
  form.issue_type = 'BUG'
  form.title = ''
  form.description = ''
  form.attachment_name = ''
  form.attachment_url = ''
}

function openCreate() {
  resetForm()
  error.value = ''
  success.value = ''
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  error.value = ''
}

async function loadIssues() {
  issuesLoading.value = true
  pageError.value = ''

  try {
    issues.value = await listMyIssues()

    if (selectedIssue.value) {
      const selectedIssueId = issueIdOf(selectedIssue.value)
      selectedIssue.value =
        issues.value.find((issue) => issueIdOf(issue) === selectedIssueId) ?? null
    }
  } catch (err) {
    pageError.value = err?.response?.data?.detail || err?.message || '問題回報載入失敗'
  } finally {
    issuesLoading.value = false
  }
}

async function openIssue(issue) {
  const issueId = issueIdOf(issue)
  if (!issueId) {
    replyError.value = '找不到問題編號'
    return
  }

  selectedIssue.value = issue
  replies.value = []
  replyBody.value = ''
  replyError.value = ''
  success.value = ''
  replyLoading.value = true

  try {
    replies.value = await listIssueReplies(issueId)
  } catch (err) {
    replyError.value = err?.response?.data?.detail || err?.message || '回覆紀錄載入失敗'
  } finally {
    replyLoading.value = false
  }
}

function closeIssue() {
  selectedIssue.value = null
  replies.value = []
  replyBody.value = ''
  replyError.value = ''
}

async function submitReply() {
  if (!selectedIssue.value) return

  const issueId = issueIdOf(selectedIssue.value)
  const body = replyBody.value.trim()

  if (!issueId) {
    replyError.value = '找不到問題編號'
    return
  }

  if (!body) {
    replyError.value = '請輸入回覆內容'
    return
  }

  replySubmitting.value = true
  replyError.value = ''
  success.value = ''

  try {
    const reply = await createIssueReply(issueId, body)
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
  } catch (err) {
    replyError.value = err?.response?.data?.detail || err?.message || '回覆送出失敗'
  } finally {
    replySubmitting.value = false
  }
}

async function submitIssue() {
  error.value = ''
  success.value = ''

  if (!form.title.trim() || !form.description.trim()) {
    error.value = '請輸入標題與描述'
    return
  }

  loading.value = true
  try {
    await createIssueReport(form)
    success.value = '問題已送出'
    closeForm()
    resetForm()
    await loadIssues()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '送出失敗'
  } finally {
    loading.value = false
  }
}

onMounted(loadIssues)
</script>

<template>
  <div class="page-grid">
    <BaseCard title="問題回報" eyebrow="NCS Issue Report">
      <template #actions>
        <button class="primary-button" type="button" @click="openCreate">新增回報</button>
      </template>
      <p>遇到系統錯誤、操作問題或有改善建議時，可於此送出回報並追蹤處理狀態。</p>
    </BaseCard>

    <p v-if="success" class="form-success">{{ success }}</p>

    <BaseModal :show="showForm" title="新增問題回報" @close="closeForm">
      <form class="form-grid" @submit.prevent="submitIssue">
        <label>
          問題類型
          <select v-model="form.issue_type">
            <option value="BUG">系統錯誤</option>
            <option value="QUESTION">操作問題</option>
            <option value="SUGGESTION">改善建議</option>
          </select>
        </label>

        <label>
          標題
          <input v-model="form.title" type="text" />
        </label>

        <label>
          描述
          <textarea v-model="form.description" rows="5"></textarea>
        </label>

        <label>
          附件名稱
          <input v-model="form.attachment_name" type="text" placeholder="例如 screenshot.png" />
        </label>

        <label>
          附件連結
          <input v-model="form.attachment_url" type="text" />
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>
      </form>

      <template #footer>
        <button type="button" class="secondary-button" @click="closeForm">取消</button>
        <button class="primary-button" type="button" :disabled="loading" @click="submitIssue">
          {{ loading ? '送出中...' : '送出問題回報' }}
        </button>
      </template>
    </BaseModal>

    <BaseCard v-if="pageError" title="資料載入失敗">
      <p class="form-error">{{ pageError }}</p>
      <button class="primary-button" type="button" @click="loadIssues">重新載入</button>
    </BaseCard>

    <LoadingSkeleton v-if="issuesLoading" :rows="4" />

    <EmptyState
      v-else-if="sortedIssues.length === 0"
      title="尚無問題回報"
      description="送出問題回報後，可在這裡追蹤處理狀態，並與管理員持續討論。"
    />

    <section v-else class="issue-layout" :class="{ 'issue-layout--with-panel': selectedIssue }">
      <div class="issue-list">
        <BaseCard
          v-for="issue in sortedIssues"
          :key="issueIdOf(issue)"
          class="issue-card"
          :class="{ 'issue-card--active': selectedIssue && issueIdOf(selectedIssue) === issueIdOf(issue) }"
          :title="issue.title"
          :eyebrow="issueTypeLabels[issue.issue_type ?? issue.issueType] ?? issue.issue_type ?? issue.issueType"
        >
          <template #actions>
            <span class="status-badge">
              {{ statusLabels[statusOf(issue)] ?? statusOf(issue) }}
            </span>
          </template>

          <p class="issue-card__description">{{ issue.description }}</p>

          <div class="issue-card__meta">
            <span>建立時間：{{ formatDate(issue.created_at ?? issue.createdAt) }}</span>
            <span v-if="issue.updated_at || issue.updatedAt">
              更新時間：{{ formatDate(issue.updated_at ?? issue.updatedAt) }}
            </span>
          </div>

          <div v-if="issue.attachment_name || issue.attachmentName" class="issue-card__attachment">
            附件：{{ issue.attachment_name ?? issue.attachmentName }}
          </div>

          <div class="issue-card__actions">
            <button class="secondary-button" type="button" @click="openIssue(issue)">
              查看 / 繼續討論
            </button>
          </div>
        </BaseCard>
      </div>

      <BaseCard v-if="selectedIssue" class="reply-panel" title="討論紀錄">
        <template #actions>
          <button class="secondary-button" type="button" @click="closeIssue">關閉</button>
        </template>

        <div class="reply-panel__issue">
          <strong>{{ selectedIssue.title }}</strong>
          <p>{{ selectedIssue.description }}</p>
        </div>

        <LoadingSkeleton v-if="replyLoading" :rows="3" />

        <div v-else-if="replies.length === 0" class="reply-empty">
          目前尚無回覆，可先補充更多說明讓管理員了解狀況。
        </div>

        <div v-else class="reply-list">
          <div
            v-for="reply in replies"
            :key="reply.reply_id ?? reply.replyId"
            class="reply-item"
            :class="{ 'reply-item--mine': isCurrentUserReply(reply) }"
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
            補充回覆
            <textarea
              v-model="replyBody"
              rows="4"
              placeholder="輸入補充內容，送出後管理員會收到通知"
            ></textarea>
          </label>

          <p v-if="replyError" class="form-error">{{ replyError }}</p>

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
  display: grid;
  gap: 1rem;
  border: 1px solid transparent;
}

.issue-card--active {
  border-color: #2563eb;
}

.issue-card :deep(.card__header) {
  margin-bottom: 0;
}

.issue-card :deep(.card__title-group) {
  gap: 0.55rem;
}

.issue-card :deep(.card__header h2) {
  line-height: 1.4;
}

.issue-card__description,
.reply-panel__issue p,
.reply-item p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.6;
}

.issue-card__meta,
.issue-card__attachment,
.reply-item__header,
.reply-empty {
  color: var(--color-text-muted, #64748b);
  font-size: 0.85rem;
}

.issue-card__meta,
.issue-card__actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: center;
}

.issue-card__meta {
  line-height: 1.5;
}

.issue-card__actions {
  padding-top: 0.15rem;
}

.status-badge {
  border-radius: 999px;
  padding: 0.35rem 0.7rem;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
  font-size: 0.85rem;
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

.reply-item--mine {
  background: #f0fdf4;
  border-color: #86efac;
}

.reply-item__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
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

.reply-form textarea {
  border: 1px solid var(--color-border, #cbd5e1);
  border-radius: 0.75rem;
  padding: 0.65rem;
  font: inherit;
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
