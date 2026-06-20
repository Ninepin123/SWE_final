<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseCard from '@/components/common/BaseCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import { getUnreadNotificationCount, listNotifications, markAllNotificationsRead, markNotificationRead } from '@/api/ncs'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const loading = ref(true)
const notifications = ref([])
const unreadCount = ref(0)
const filter = ref('all')
const error = ref('')
const markingAll = ref(false)
const updatingIds = ref(new Set())

const visibleNotifications = computed(() => {
  if (filter.value === 'unread') return notifications.value.filter((item) => !item.isRead)
  return notifications.value
})

function formatDate(value) {
  return new Intl.DateTimeFormat('zh-TW', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function resolveErrorMessage(err, fallback) {
  return err?.response?.data?.detail || err?.message || fallback
}

async function fetchNotifications() {
  notifications.value = await listNotifications({
    unreadOnly: filter.value === 'unread',
    limit: 100,
    offset: 0,
  })
}

async function fetchUnreadCount() {
  unreadCount.value = await getUnreadNotificationCount()
}

async function reload(showLoading = false) {
  if (showLoading) loading.value = true
  error.value = ''
  try {
    await Promise.all([fetchNotifications(), fetchUnreadCount()])
  } catch (err) {
    const message = resolveErrorMessage(err, '通知資料載入失敗，請稍後再試。')
    error.value = message
    toast.error(message)
  } finally {
    loading.value = false
  }
}

async function onFilterChange(next) {
  filter.value = next
  await reload()
}

async function markOneRead(item) {
  if (item.isRead || updatingIds.value.has(item.notificationId)) return

  const nextIds = new Set(updatingIds.value)
  nextIds.add(item.notificationId)
  updatingIds.value = nextIds

  try {
    const updated = await markNotificationRead(item.notificationId)
    const readAt = updated?.readAt ?? new Date().toISOString()
    notifications.value = notifications.value
      .map((current) => (
        current.notificationId === item.notificationId
          ? { ...current, isRead: true, readAt }
          : current
      ))
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    if (filter.value === 'unread') {
      notifications.value = notifications.value.filter((current) => !current.isRead)
    }
    toast.success('已標記為已讀')
  } catch (err) {
    toast.error(resolveErrorMessage(err, '標記已讀失敗，請稍後再試。'))
  } finally {
    const releasingIds = new Set(updatingIds.value)
    releasingIds.delete(item.notificationId)
    updatingIds.value = releasingIds
  }
}

async function markAllRead() {
  if (!unreadCount.value || markingAll.value) return
  markingAll.value = true
  try {
    const result = await markAllNotificationsRead()
    const updatedCount = result?.updatedCount ?? 0
    notifications.value = notifications.value.map((item) => ({
      ...item,
      isRead: true,
      readAt: item.readAt ?? new Date().toISOString(),
    }))
    unreadCount.value = 0
    if (filter.value === 'unread') {
      notifications.value = []
    }
    toast.success(updatedCount > 0 ? `已將 ${updatedCount} 筆通知標記為已讀` : '目前沒有未讀通知')
  } catch (err) {
    toast.error(resolveErrorMessage(err, '全部標記已讀失敗，請稍後再試。'))
  } finally {
    markingAll.value = false
  }
}

onMounted(async () => {
  await reload(true)
})
</script>

<template>
  <div class="page-grid">
    <BaseCard title="通知中心" eyebrow="Notifications">
      <template #actions>
        <div class="card-actions">
          <span class="status-badge status-badge--warning">未讀 {{ unreadCount }}</span>
          <button
            type="button"
            class="secondary-button"
            :disabled="markingAll || unreadCount === 0"
            @click="markAllRead"
          >
            全部標記已讀
          </button>
        </div>
      </template>

      <div class="segmented">
        <button
          type="button"
          :class="{ active: filter === 'all' }"
          @click="onFilterChange('all')"
        >
          全部
        </button>
        <button
          type="button"
          :class="{ active: filter === 'unread' }"
          @click="onFilterChange('unread')"
        >
          未讀
        </button>
      </div>
    </BaseCard>

    <LoadingSkeleton v-if="loading" :rows="5" />
    <BaseCard v-else-if="error" title="通知載入失敗">
      <p class="form-error">{{ error }}</p>
      <div class="form-actions form-actions--left">
        <button type="button" class="secondary-button" @click="reload(true)">重新載入</button>
      </div>
    </BaseCard>
    <EmptyState
      v-else-if="!visibleNotifications.length"
      title="目前沒有通知"
      description="申請成功、補件、審查結果與推薦信提醒會出現在這裡。"
      icon="notification"
    />

    <BaseCard v-else>
      <div class="notification-list">
        <button
          v-for="item in visibleNotifications"
          :key="item.notificationId"
          type="button"
          class="notification-item"
          :class="[`notification-item--${item.type}`, { 'notification-item--read': item.isRead }]"
          @click="markOneRead(item)"
        >
          <span class="notification-item__dot" />
          <div>
            <div class="notification-item__top">
              <strong>{{ item.title }}<span v-if="item.category">（{{ item.category }}）</span></strong>
              <time>{{ formatDate(item.createdAt) }}</time>
            </div>
            <p>{{ item.body }}</p>
          </div>
          <span>{{ item.isRead ? '已讀' : '未讀' }}</span>
        </button>
      </div>
    </BaseCard>
  </div>
</template>
