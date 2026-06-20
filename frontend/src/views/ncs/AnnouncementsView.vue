<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { listAnnouncements } from '@/api/ncs'

const loading = ref(true)
const error = ref('')
const announcements = ref([])

const visibleAnnouncements = computed(() => announcements.value)

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
  const labels = {
    STUDENT: '學生',
    TEACHER: '教師',
    SPONSOR: '獎助單位人員',
    REVIEWER: '審查人員',
    ADMIN: '系統管理員',
  }
  return labels[item.targetRole] ?? item.targetRole ?? '指定對象'
}

async function loadAnnouncements() {
  loading.value = true
  error.value = ''

  try {
    announcements.value = await listAnnouncements()
  } catch (err) {
    error.value = err?.response?.data?.detail || err?.message || '公告載入失敗'
  } finally {
    loading.value = false
  }
}

onMounted(loadAnnouncements)
</script>

<template>
  <div class="page-grid">
    <BaseCard title="公告中心" eyebrow="NCS Announcement">
      <p>查看系統公告、獎助學金公告與重要維護訊息。</p>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="4" />

    <BaseCard v-else-if="error" title="載入失敗">
      <p>{{ error }}</p>
      <button class="primary-button" type="button" @click="loadAnnouncements">
        重新載入
      </button>
    </BaseCard>

    <EmptyState
      v-else-if="visibleAnnouncements.length === 0"
      title="目前沒有公告"
      description="目前沒有符合你身分的公告。"
    />

    <section v-else class="notification-list">
      <button
        v-for="announcement in visibleAnnouncements"
        :key="announcement.announcementId"
        type="button"
        class="notification-item"
      >
        <div class="notification-item__icon">
          公告
        </div>

        <div class="notification-item__content">
          <div class="notification-item__header">
            <strong>{{ announcement.title }}</strong>
            <span>{{ formatDate(announcement.publishedAt || announcement.createdAt) }}</span>
          </div>

          <p>{{ announcement.body || '無公告內容' }}</p>

          <div class="notification-item__meta">
            <span>{{ targetLabel(announcement) }}</span>
            <span v-if="announcement.expiresAt">
              有效期限：{{ formatDate(announcement.expiresAt) }}
            </span>
          </div>
        </div>
      </button>
    </section>
  </div>
</template>

<style scoped>
.notification-list {
  display: grid;
  gap: 0.85rem;
}

.notification-item {
  width: 100%;
  display: flex;
  gap: 1rem;
  text-align: left;
  border: 1px solid var(--color-border, #dbe3ef);
  border-radius: 1rem;
  background: var(--color-surface, #ffffff);
  padding: 1rem;
  cursor: default;
}

.notification-item__icon {
  min-width: 3rem;
  height: 3rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
  font-size: 0.85rem;
}

.notification-item__content {
  flex: 1;
  display: grid;
  gap: 0.35rem;
}

.notification-item__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.notification-item__header span,
.notification-item__meta {
  color: var(--color-text-muted, #64748b);
  font-size: 0.85rem;
}

.notification-item__content p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.6;
}

.notification-item__meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}
</style>