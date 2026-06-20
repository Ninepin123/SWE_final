<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import {
  createAnnouncement,
  deleteAnnouncement,
  listAdminAnnouncements,
  updateAnnouncement,
} from '@/api/ncs'

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const announcements = ref([])
const editingId = ref(null)

const form = reactive({
  title: '',
  body: '',
  isGlobal: true,
  targetRole: '',
  status: 'PUBLISHED',
  expiresAt: '',
  notifyUsers: true,
})

const isEditing = computed(() => editingId.value !== null)

const roleOptions = [
  { label: '學生', value: 'STUDENT' },
  { label: '教師', value: 'TEACHER' },
  { label: '獎助單位人員', value: 'SPONSOR' },
  { label: '審查人員', value: 'REVIEWER' },
  { label: '系統管理員', value: 'ADMIN' },
]

function resetForm() {
  editingId.value = null
  form.title = ''
  form.body = ''
  form.isGlobal = true
  form.targetRole = ''
  form.status = 'PUBLISHED'
  form.expiresAt = ''
  form.notifyUsers = true
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

function targetLabel(item) {
  if (item.isGlobal) return '全體使用者'
  const found = roleOptions.find((role) => role.value === item.targetRole)
  return found?.label ?? item.targetRole ?? '指定對象'
}

function toInputDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

function startEdit(item) {
  editingId.value = item.announcementId
  form.title = item.title
  form.body = item.body ?? ''
  form.isGlobal = item.isGlobal
  form.targetRole = item.targetRole ?? ''
  form.status = item.status ?? 'PUBLISHED'
  form.expiresAt = toInputDateTime(item.expiresAt)
  form.notifyUsers = false
  success.value = ''
  error.value = ''
}

function buildPayload() {
  return {
    title: form.title.trim(),
    body: form.body.trim(),
    isGlobal: form.isGlobal,
    targetRole: form.isGlobal ? null : form.targetRole,
    status: form.status,
    expiresAt: form.expiresAt ? new Date(form.expiresAt).toISOString() : null,
    notifyUsers: form.notifyUsers,
  }
}

async function loadAnnouncements() {
  loading.value = true
  error.value = ''

  try {
    announcements.value = await listAdminAnnouncements()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '公告載入失敗'
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  error.value = ''
  success.value = ''

  if (!form.title.trim()) {
    error.value = '請輸入公告標題'
    return
  }

  if (!form.isGlobal && !form.targetRole) {
    error.value = '指定對象公告需選擇角色'
    return
  }

  saving.value = true

  try {
    const payload = buildPayload()

    if (isEditing.value) {
      await updateAnnouncement(editingId.value, payload)
      success.value = '公告已更新'
    } else {
      await createAnnouncement(payload)
      success.value = '公告已發布'
    }

    resetForm()
    await loadAnnouncements()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '公告儲存失敗'
  } finally {
    saving.value = false
  }
}

async function removeAnnouncement(item) {
  const confirmed = window.confirm(`確定要刪除公告「${item.title}」嗎？`)
  if (!confirmed) return

  error.value = ''
  success.value = ''

  try {
    await deleteAnnouncement(item.announcementId)
    success.value = '公告已刪除'
    await loadAnnouncements()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '公告刪除失敗'
  }
}

onMounted(loadAnnouncements)
</script>

<template>
  <div class="page-grid">
    <BaseCard title="公告管理" eyebrow="NCS Announcement Admin">
      <p>系統管理員可發布全域公告或指定角色公告，並維護既有公告內容。</p>
    </BaseCard>

    <BaseCard :title="isEditing ? '修改公告' : '新增公告'">
      <form class="announcement-form" @submit.prevent="submitForm">
        <label>
          公告標題
          <input v-model="form.title" type="text" placeholder="請輸入公告標題" />
        </label>

        <label>
          公告內容
          <textarea v-model="form.body" rows="5" placeholder="請輸入公告內容"></textarea>
        </label>

        <label class="checkbox-row">
          <input v-model="form.isGlobal" type="checkbox" />
          全域公告，所有角色皆可查看
        </label>

        <label v-if="!form.isGlobal">
          發布對象
          <select v-model="form.targetRole">
            <option value="">請選擇角色</option>
            <option v-for="role in roleOptions" :key="role.value" :value="role.value">
              {{ role.label }}
            </option>
          </select>
        </label>

        <label>
          狀態
          <select v-model="form.status">
            <option value="PUBLISHED">發布</option>
            <option value="DRAFT">草稿</option>
            <option value="ARCHIVED">封存</option>
          </select>
        </label>

        <label>
          有效期限
          <input v-model="form.expiresAt" type="datetime-local" />
        </label>

        <label v-if="!isEditing" class="checkbox-row">
          <input v-model="form.notifyUsers" type="checkbox" />
          發布後建立站內通知
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>
        <p v-if="success" class="form-success">{{ success }}</p>

        <div class="form-actions">
          <button class="primary-button" type="submit" :disabled="saving">
            {{ saving ? '儲存中...' : isEditing ? '更新公告' : '發布公告' }}
          </button>
          <button v-if="isEditing" type="button" class="secondary-button" @click="resetForm">
            取消編輯
          </button>
        </div>
      </form>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="4" />

    <EmptyState
      v-else-if="announcements.length === 0"
      title="目前沒有公告"
      description="尚未建立任何公告。"
    />

    <section v-else class="announcement-list">
      <BaseCard
        v-for="announcement in announcements"
        :key="announcement.announcementId"
        class="announcement-card"
      >
        <div class="announcement-card__header">
          <div>
            <span class="announcement-card__target">
              {{ targetLabel(announcement) }}
            </span>
            <h3>{{ announcement.title }}</h3>
          </div>
          <span class="announcement-card__status">
            {{ announcement.status }}
          </span>
        </div>

        <p class="announcement-card__body">
          {{ announcement.body || '無公告內容' }}
        </p>

        <div class="announcement-card__meta">
          <span>建立時間：{{ formatDate(announcement.createdAt) }}</span>
          <span>有效期限：{{ formatDate(announcement.expiresAt) }}</span>
        </div>

        <div class="announcement-card__actions">
          <button type="button" class="secondary-button" @click="startEdit(announcement)">
            修改
          </button>
          <button type="button" class="danger-button" @click="removeAnnouncement(announcement)">
            刪除
          </button>
        </div>
      </BaseCard>
    </section>
  </div>
</template>

<style scoped>
.announcement-form {
  display: grid;
  gap: 1rem;
}

.announcement-form label {
  display: grid;
  gap: 0.4rem;
  font-weight: 600;
}

.announcement-form input,
.announcement-form textarea,
.announcement-form select {
  width: 100%;
  border: 1px solid var(--color-border, #cbd5e1);
  border-radius: 0.75rem;
  padding: 0.75rem;
  font: inherit;
}

.checkbox-row {
  display: flex !important;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 0.5rem !important;
  font-weight: 500 !important;
}

.checkbox-row input {
  width: auto;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.form-error {
  color: #b91c1c;
  font-weight: 600;
}

.form-success {
  color: #15803d;
  font-weight: 600;
}

.announcement-list {
  display: grid;
  gap: 1rem;
}

.announcement-card__header,
.announcement-card__meta,
.announcement-card__actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.announcement-card__header h3 {
  margin: 0.25rem 0 0;
}

.announcement-card__target,
.announcement-card__status,
.announcement-card__meta {
  font-size: 0.85rem;
  color: var(--color-text-muted, #64748b);
}

.announcement-card__body {
  white-space: pre-wrap;
  line-height: 1.7;
}

.danger-button {
  border: 1px solid #fecaca;
  background: #fee2e2;
  color: #b91c1c;
  border-radius: 999px;
  padding: 0.65rem 1rem;
  font-weight: 700;
  cursor: pointer;
}
</style>